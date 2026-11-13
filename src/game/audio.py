"""Sons du jeu, synthétisés en code (aucun fichier audio), mixés comme sur une console.

Tout passe par un seul flux (un seul canal pygame) rendu par morceaux de 80 ms :
  moteur     : « v10 » (défaut) : V10 atmosphérique de F1 en synthèse additive. Toutes les harmoniques
               découlent d'une seule phase de vilebrequin : ordres d'allumage (5, 10, 15...) dominants, demi-ordres
               pour l'irrégularité du V, résonances d'échappement, combustion qui fluctue (le grain), 6 rapports
               avec coupure d'allumage au passage, détonations à l'échappement au lâcher de gaz.
               « electric » : l'ancien sifflement électrique (TRACKAI_ENGINE=electric pour comparer).
  autres     : souffle d'air, pneus (crissement en glisse/freinage), effets ponctuels (choc, bips, carillon, fanfare)
  bus master : EQ (coupe-bas 40 Hz, adoucissement des aigus) -> compresseur -> limiteur doux, en stéréo
Rien ne peut donc couper un autre son ni saturer la sortie.
CarAudio(offline=True) ne touche pas à la carte son : render() renvoie les échantillons (démo, tests).
"""
import atexit
import math
import os
import threading
import time

import numpy as np
import pygame

SR = 22050
# volume général réglé par le joueur (touches + / -), gardé d'une session à l'autre
SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                             "data", "audio_settings.json")


def _load_volume():
    try:
        import json
        with open(SETTINGS_PATH) as f:
            return min(1.0, max(0.0, float(json.load(f).get("volume", 0.7))))
    except (OSError, ValueError, TypeError):
        return 0.7


def _tone(freqs, dur, decay=6.0):
    t = np.arange(int(dur * SR)) / SR
    w = sum(np.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
    env = np.minimum(1.0, t / 0.01) * np.exp(-decay * t)
    return w * env


def _one_pole(x, a, state):
    """Filtre passe-bas d'ordre 1 (y += a * (x - y)) ; renvoie (sortie, nouvel état)."""
    y = np.empty_like(x)
    s = state
    for i in range(len(x)):
        s += a * (x[i] - s)
        y[i] = s
    return y, s


class V10:
    """Régime, rapports et timbre d'un V10 de F1 (4 temps : 5 explosions par tour de vilebrequin)."""
    IDLE, REDLINE = 3000.0, 11500.0   # régime bien plus bas qu'un vrai V10 : note grave, pas stridente
    # vitesse max (fraction de MAX_SPEED) au rupteur dans chaque rapport : étagement calé sur l'accélération
    # de la voiture (chaque rapport dure à peu près aussi longtemps), le régime retombe de 15 à 35 % au passage
    TOPS = (0.28, 0.43, 0.57, 0.71, 0.85, 1.0)
    UPSHIFT, DOWNSHIFT = 0.965, 0.66   # en fraction du rupteur
    CUT_FRAMES = 3             # coupure d'allumage au passage d'un rapport (~60 ms) : le « brap »
    # ordres (multiples de la fréquence du vilebrequin) : demi-ordres à 18 (au-delà, 9 kHz à bas régime)
    ORDERS = np.arange(1, 37) * 0.5
    # résonances (Hz, gain, largeur en octaves) : coffre de l'échappement, cri métallique, éclat
    FORMANTS = ((220.0, 1.0, 0.9), (650.0, 0.85, 0.7), (1600.0, 0.22, 0.6), (3500.0, 0.04, 0.5))

    def __init__(self, rng):
        o = self.ORDERS
        firing = np.isclose(o % 5.0, 0.0)
        integer = np.isclose(o % 1.0, 0.0)
        base = np.where(firing, 1.0, np.where(integer, 0.22, 0.10))
        self.base = base * rng.uniform(0.7, 1.3, len(o)) / (1.0 + 0.08 * o)
        self.phase0 = rng.uniform(0, 2 * math.pi, len(o))
        self.tops = np.array(self.TOPS)
        self.GEARS = len(self.TOPS)
        self.gear = 0
        self.rpm = self.IDLE
        self.cut = 0
        self.theta = 0.0         # phase du vilebrequin (en tours)

    def step(self, v, throttle, running):
        """Une image (1/50 s) : met à jour rapport et régime ; renvoie (régime, charge, coupure)."""
        if not running:
            self.gear, self.cut = 0, 0
            self.rpm += (self.IDLE - self.rpm) * 0.2
            return self.rpm, 0.0, False
        frac = v / self.tops[self.gear]
        if frac > self.UPSHIFT and self.gear < self.GEARS - 1 and throttle:
            self.gear += 1
            self.cut = self.CUT_FRAMES
        elif self.gear > 0 and v / self.tops[self.gear - 1] < self.UPSHIFT * 0.92 and frac < self.DOWNSHIFT:
            self.gear -= 1        # rétrogradage : le régime remonte d'un coup
        frac = min(1.02, v / self.tops[self.gear])
        target = self.IDLE + (self.REDLINE - self.IDLE) * frac
        if throttle and v < 0.05:
            target = max(target, self.IDLE + 2500.0)     # coups de gaz à l'arrêt
        rate = 0.55 if target < self.rpm - 1500 else 0.35   # passage de rapport : chute rapide
        self.rpm += (target - self.rpm) * rate
        cutting = self.cut > 0
        if cutting:
            self.cut -= 1
        load = 0.0 if cutting else (1.0 if throttle else 0.0)
        return self.rpm, load, cutting

    def weights(self, rpm, load):
        """Amplitude de chaque ordre au régime donné (résonances, éclat sous charge)."""
        fc = rpm / 60.0
        f = self.ORDERS * fc
        logf = np.log2(np.maximum(f, 1.0))
        w = 0.12 * np.ones_like(f)
        for k, (fr, g, width) in enumerate(self.FORMANTS):
            if k >= 2:
                g *= 0.35 + 0.65 * load          # l'éclat aigu vient avec les gaz
            w += g * np.exp(-0.5 * ((logf - math.log2(fr)) / width) ** 2)
        w *= np.clip((5000.0 - f) / 2000.0, 0.0, 1.0)   # rien au-delà de ~5 kHz
        w *= np.clip(f / 120.0, 0.0, 1.0)
        a = self.base * w
        if load < 0.5:   # gaz coupés : moins d'ordres d'allumage, plus de demi-ordres (ça gronde, ça crépite)
            a = a * np.where(np.isclose(self.ORDERS % 5.0, 0.0), 0.55, 1.35)
        return a / (np.sqrt(np.sum(a ** 2)) + 1e-9)


class CarAudio:
    CHUNK = 0.08            # s par morceau rendu
    GEARS = 5               # moteur électrique : rapports simulés
    # sifflement électrique : fondamentale + harmoniques légèrement désaccordées (moteur, onduleur, pignons)
    PARTIALS = ((1.0, 1.0), (2.0, 0.32), (3.02, 0.10), (0.5, 0.08))
    # bus master
    COMP_THRESHOLD = 0.35   # niveau RMS au-delà duquel on compresse
    COMP_RATIO = 3.0
    CEILING = 0.89          # limiteur : ~ -1 dBFS
    # cibles d'un morceau à l'autre (interpolées) : 0 fréquence élec., 1 niveau moteur, 2 air, 3 pneus,
    # 4 charge, 5 fréquence grave élec., 6 régime du V10
    # 7 position gauche-droite de la voiture (-1 à 1)
    N_TARGETS = 8
    ENGINE_GAIN = 0.36      # moteur en retrait (-4 dB par rapport à avant) : il accompagne, il ne couvre plus tout
    PAN_MAX = 0.65          # la voiture se déplace dans l'image stéréo sans jamais sortir d'une enceinte
    # premières réflexions (ms, gain gauche, gain droite) : une petite salle autour de la voiture, qui l'éloigne
    # un peu et ouvre la stéréo (taps différents à gauche et à droite)
    REFLECTIONS = ((9.7, 0.30, 0.12), (13.1, 0.10, 0.28), (19.4, 0.22, 0.09), (26.8, 0.08, 0.20),
                   (37.3, 0.14, 0.06), (49.9, 0.05, 0.12), (63.1, 0.07, 0.04))
    SPATIAL_FX = ("hit",)   # effets placés sur la voiture ; les autres (bips, carillon, fanfare) restent au centre

    def __init__(self, engine=None, offline=False):
        self.engine = (engine or os.environ.get("TRACKAI_ENGINE", "v10")).lower()
        if self.engine not in ("v10", "electric"):
            self.engine = "v10"
        self.ok = False
        self.muted = False
        self.offline = offline
        self.volume = 1.0 if offline else _load_volume()   # la démo hors ligne garde le niveau de référence
        if not offline:
            try:
                pygame.mixer.init(SR, -16, 2, 1024)
            except pygame.error:
                return
            pygame.mixer.set_num_channels(4)
            pygame.mixer.set_reserved(1)
            self.ch = pygame.mixer.Channel(0)
        self.rng = np.random.default_rng(1)
        t = np.arange(int(0.22 * SR)) / SR
        thud = (self.rng.standard_normal(len(t)) * np.exp(-28 * t) * 0.8
                + np.sin(2 * math.pi * 70 * t) * np.exp(-14 * t))
        fan = [_tone([f, f * 1.5], 0.15, 8) for f in (392, 494, 587)] + [_tone([784, 988, 1175], 0.8, 3.5)]
        self.samples = {
            "hit": 0.8 * thud / np.max(np.abs(thud)),
            "beep": 0.35 * _tone([440], 0.16, 12),
            "go": 0.35 * _tone([587, 880], 0.4, 6),
            "chime": 0.25 * np.concatenate([_tone([659], 0.08, 20), _tone([988], 0.22, 10)]),
            "fanfare": 0.3 * np.concatenate(fan),
        }
        self._pops = [self._make_pop(i) for i in range(5)]
        self.v10 = V10(np.random.default_rng(10))
        self.voices = []                      # effets en cours : [échantillons, position, gain]
        self._phase = np.zeros((1, len(self.PARTIALS)))   # sifflement électrique (mono)
        self._low_phase = np.zeros(2)                        # couche grave électrique
        self._air_lp = 0.0
        self._skid_lp = 0.0
        self._skid_lp2 = 0.0
        self._squeal_ph = 0.0
        self._squeal_t = 0.0
        self._jit_lp = 0.0                    # fluctuation de la combustion (grain du V10)
        self._body_lp = 0.0                   # corps de l'échappement (bruit grave sous charge)
        self._hp_lp = np.zeros(2)             # état du coupe-bas (passe-bas soustrait), par canal
        self._smooth_lp = np.zeros(2)         # état de l'adoucissement des aigus, par canal
        self._comp_gain = 1.0
        self._gear = 0
        self._shift_dip = 0                   # images restantes du creux de volume au changement de rapport
        self._lift_frames = 0                 # images depuis le lâcher de gaz (détonations)
        self._cut_pending = False             # une coupure d'allumage a eu lieu depuis le dernier morceau
        self._load_s = 0.0                    # charge lissée (inertie du moteur)
        self._held_frames = 0                 # images de gaz tenus d'affilée
        self._pop_window = False              # un vrai lâcher de gaz : les détonations sont permises
        self._pop_gap = 0
        self._w_prev = None                   # timbre du V10 à la fin du morceau précédent
        self._hist = np.zeros(2048)           # derniers échantillons de la scène (pour les réflexions)
        self._refl_lp = np.zeros(2)
        self._prev = np.zeros(self.N_TARGETS)
        self._prev[6] = V10.IDLE
        self._target = self._prev.copy()
        self._keep = []
        self._lock = threading.Lock()
        self.ok = True
        if offline:
            return
        # un fil dédié alimente le son en continu : il ne dépend plus du rythme de l'affichage
        # (si l'image prend du retard, par exemple pendant un entraînement, le son ne crépite pas)
        self._running = True
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()
        atexit.register(self.close)   # s'arrête avant que pygame ne se ferme

    def _make_pop(self, i):
        """Détonation à l'échappement : claquement bref, grave et sale (variantes)."""
        rng = np.random.default_rng(100 + i)
        dur = 0.035 + 0.025 * rng.random()
        t = np.arange(int(dur * SR)) / SR
        crack = rng.standard_normal(len(t)) * np.exp(-t / (0.004 + 0.004 * rng.random()))
        crack, _ = _one_pole(crack, 0.35 + 0.2 * rng.random(), 0.0)
        thump = np.sin(2 * math.pi * (55 + 40 * rng.random()) * t) * np.exp(-t / 0.018)
        p = crack * 1.6 + thump
        return p / np.max(np.abs(p))

    def _pump(self):
        while self._running:
            with self._lock:
                if not self._running or not pygame.mixer.get_init():
                    return
                try:
                    if not self.muted:
                        self._feed()
                except pygame.error:
                    return   # mixer fermé (fin du jeu)
            time.sleep(0.005)

    def close(self):
        """Arrête proprement le fil du son (à appeler avant pygame.quit, sinon fait à la sortie)."""
        if getattr(self, "_running", False):
            self._running = False
            with self._lock:
                pass
            self._thread.join(timeout=1.0)

    # --- interface du jeu ---
    def change_volume(self, delta):
        """Monte ou baisse le volume général (par pas de 10 %), le garde pour les prochaines sessions ; renvoie le niveau."""
        self.volume = round(min(1.0, max(0.0, self.volume + delta)), 2)
        if self.volume > 0 and self.muted:
            self.toggle_mute()
        try:
            import json
            os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
            with open(SETTINGS_PATH, "w") as f:
                json.dump({"volume": self.volume}, f)
        except OSError:
            pass
        return self.volume

    def toggle_mute(self):
        self.muted = not self.muted
        if self.ok and self.muted and not self.offline:
            with self._lock:
                self.ch.stop()
                self.voices.clear()

    def play(self, name, volume=1.0):
        if self.ok and not self.muted:
            with self._lock:
                self.voices.append([self.samples[name], 0, float(volume), name in self.SPATIAL_FX])

    def update(self, speed_frac, throttle, slip_deg, drifting, braking, running=True, pan=0.0):
        """À appeler à chaque image. speed_frac : vitesse réelle / vitesse max ;
        pan : position gauche-droite de la voiture à l'écran (-1 bord gauche, 1 bord droit)."""
        if not self.ok or self.muted:
            return
        v = max(0.0, min(1.1, speed_frac))
        throttle = bool(throttle)
        # --- moteur électrique (ancien) : le sifflement monte dans chaque rapport ---
        x = min(v, 0.999) * self.GEARS
        gear = int(x)
        freq = 170.0 + 30.0 * gear + 250.0 * (x - gear)
        if gear != self._gear:
            if gear > self._gear and throttle:
                self._shift_dip = 3
            self._gear = gear
        whine = 0.65 * (0.10 + 0.32 * v) * (1.0 if throttle else 0.55)
        if self._shift_dip > 0:
            whine *= 0.45
            self._shift_dip -= 1
        if not running:
            whine = 0.035
        low_f = freq * 0.25
        load = 1.0 if (throttle and running) else 0.0
        # --- V10 ---
        rpm, v_load, cutting = self.v10.step(v, throttle and running, running)
        if self.engine == "v10":
            r = (rpm - V10.IDLE) / (V10.REDLINE - V10.IDLE)
            # inertie : la charge suit la pédale en ~80 ms à l'appui, ~150 ms au lâcher. Un pied qui tapote
            # (bot débutant : une décision toutes les 40 ms) donne un régime moyen, pas un son haché.
            self._load_s += (v_load - self._load_s) * (0.45 if v_load > self._load_s else 0.25)
            level = (0.30 + 0.45 * r) * (0.62 + 0.38 * self._load_s)
            if cutting:
                self._cut_pending = True   # rendue au morceau suivant, même si elle tombe entre deux
            if not running:
                level = 0.12
            whine, load = level, self._load_s
            # détonations : seulement après un vrai lâcher (gaz tenus au moins 0,4 s avant), à haut régime,
            # surtout dans la demi-seconde qui suit ; jamais deux à moins de 60 ms
            if throttle and running:
                self._held_frames += 1
                self._lift_frames = 0
                self._pop_window = self._held_frames >= 20
            elif running and r > 0.45 and self._pop_window:
                self._held_frames = 0
                self._lift_frames += 1
                self._pop_gap -= 1
                p = (0.3 if self._lift_frames < 25 else 0.04) * r
                if self._lift_frames > 75:
                    self._pop_window = False      # au-delà de 1,5 s, l'échappement s'est calmé
                if self._pop_gap <= 0 and self.rng.random() < p:
                    self._pop_gap = 3
                    pop = self._pops[int(self.rng.integers(len(self._pops)))]
                    with self._lock:
                        self.voices.append([pop, 0, 0.25 + 0.35 * self.rng.random() * r, True])
            else:
                self._held_frames = 0
                self._lift_frames = 0
        air = 0.18 * max(0.0, (v - 0.55) / 0.45) ** 2   # le souffle d'air ne vient qu'à haute vitesse
        skid = 0.0
        if v > 0.15:
            skid = max(0.0, min(1.0, (slip_deg - 8.0) / 22.0))
            if drifting:
                skid = max(skid, 0.55)
            if braking:
                skid = max(skid, 0.35)
            skid *= 0.2 * min(1.0, v * 1.5)   # crissement présent mais discret
        pan = max(-1.0, min(1.0, float(pan))) * self.PAN_MAX
        self._target = np.array([freq, whine, air, skid, load, low_f, rpm, pan])

    def silence(self):
        """Coupe moteur et pneus (les effets, comme la fanfare d'arrivée, continuent)."""
        if self.ok:
            t = self._prev.copy()
            t[1:5] = 0.0
            self._target = t

    # --- rendu ---
    def _feed(self):
        if self.ch.get_queue() is not None:
            return
        pcm = (self.render() * 32767).astype(np.int16)
        snd = pygame.sndarray.make_sound(pcm.copy(order="C"))
        if self.ch.get_busy():
            self.ch.queue(snd)
            self._keep = self._keep[-1:] + [snd]   # garder vivants le morceau joué et celui en attente
        else:
            self.ch.play(snd)
            self._keep = [snd]

    def _electric(self, n, f, load, low_f):
        m = np.zeros(n)
        for idx, (mult, gain) in enumerate(self.PARTIALS):
            if mult > 1.0:
                gain = gain * (0.7 + 0.8 * load)     # plus de mordant en accélération
            ph = self._phase[0, idx] + np.cumsum(2 * math.pi * f * mult / SR)
            m += gain * np.sin(ph)
            self._phase[0, idx] = ph[-1] % (2 * math.pi)
        drive = 1.0 + 0.8 * load
        center = np.tanh(drive * m / 1.6) / np.tanh(drive) * 0.5 * 0.95
        lows = np.zeros(n)
        for j, (mult, gain) in enumerate(((1.0, 1.0), (2.0, 0.7))):
            ph = self._low_phase[j] + np.cumsum(2 * math.pi * low_f * mult / SR)
            lows += gain * np.sin(ph)
            self._low_phase[j] = ph[-1] % (2 * math.pi)
        return center, lows * (0.55 + 0.35 * load) * 1.3

    def _v10(self, n, rpm, load):
        """Un morceau de V10 (niveau 1 avant le gain) : additif sur la phase du vilebrequin."""
        e = self.v10
        theta = e.theta + np.cumsum(rpm / 60.0 / SR)          # tours de vilebrequin
        e.theta = float(theta[-1] % 2.0)                        # le cycle 4 temps dure 2 tours
        w1 = e.weights(float(rpm[-1]), float(load[-1]))
        w0 = self._w_prev if self._w_prev is not None else w1
        self._w_prev = w1
        sines = np.sin(2 * math.pi * np.outer(theta, e.ORDERS) + e.phase0)
        ramp = np.arange(n) / n
        x = (sines @ w0) * (1.0 - ramp) + (sines @ w1) * ramp   # timbre interpolé : pas de clic entre morceaux
        # la combustion n'est jamais régulière : modulation rapide d'amplitude (le grain, la râpe)
        jit, self._jit_lp = _one_pole(self.rng.standard_normal(n), 0.12, self._jit_lp)
        x *= 1.0 + (0.9 + 0.8 * load) * jit
        # corps d'échappement : bruit grave qui épaissit le son sous charge
        body, self._body_lp = _one_pole(self.rng.standard_normal(n), 0.05, self._body_lp)
        x += body * (0.6 + 0.9 * load)
        drive = 1.3 + 1.4 * load                               # saturation : plus sale à fond
        return np.tanh(drive * x) / np.tanh(drive)

    def render(self):
        """Un morceau stéréo (CHUNK s, float dans [-1, 1], forme (n, 2))."""
        n = int(SR * self.CHUNK)
        k = np.linspace(0.0, 1.0, n, endpoint=False)
        p0, p1 = self._prev, self._target
        f, level, air, skid, load, low_f, rpm, pan = (p0[i] + (p1[i] - p0[i]) * k for i in range(self.N_TARGETS))
        self._prev = self._target.copy()

        if self.engine == "v10":
            env = np.ones(n)
            if self._cut_pending:   # coupure d'allumage : creux de 50 ms puis reprise (le « brap » du passage)
                self._cut_pending = False
                a, m = int(0.006 * SR), int(0.05 * SR)
                env[:a] = np.linspace(1.0, 0.3, a)
                env[a:m] = 0.3
                env[m:m + 200] = np.linspace(0.3, 1.0, 200)
            car = self._v10(n, rpm, load) * level * env * self.ENGINE_GAIN
        else:
            center, lows = self._electric(n, f, load, low_f)
            car = (center + lows) * level * self.ENGINE_GAIN / 0.55

        # souffle d'air
        noise, self._air_lp = _one_pole(self.rng.standard_normal(n), 0.08, self._air_lp)
        car = car + air * noise * 0.45   # vent discret (-11 dB), seulement à haute vitesse
        # pneus : crissement = bruit filtré en bande (~0,5-2 kHz) + léger sifflement qui ondule vers 950 Hz
        white = self.rng.standard_normal(n)
        hi, self._skid_lp = _one_pole(white, 0.45, self._skid_lp)
        lo, self._skid_lp2 = _one_pole(white, 0.13, self._skid_lp2)
        band = (hi - lo) * 2.2
        tt = self._squeal_t + np.arange(n) / SR
        fq = 950.0 + 60.0 * np.sin(2 * math.pi * 5.5 * tt) + 25.0 * np.sin(2 * math.pi * 13.0 * tt)
        sq_ph = self._squeal_ph + np.cumsum(2 * math.pi * fq / SR)
        self._squeal_ph = sq_ph[-1] % (2 * math.pi)
        self._squeal_t = tt[-1] + 1.0 / SR
        car = car + skid * (0.75 * band + 0.45 * np.sin(sq_ph))

        # effets ponctuels : sur la voiture (chocs, détonations) ou au centre (bips, carillon, fanfare)
        fx = np.zeros(n)
        alive = []
        for v in self.voices:
            data, pos, gain, spatial = v
            m = min(n, len(data) - pos)
            (car if spatial else fx)[:m] += gain * data[pos:pos + m]
            v[1] = pos + m
            if v[1] < len(data):
                alive.append(v)
        self.voices = alive

        # scène : la voiture placée à sa position (panoramique à puissance constante), plus des réflexions
        # gauche/droite différentes calculées sur le son non placé (la salle, elle, ne bouge pas)
        ang = (pan + 1.0) * math.pi / 4
        g_l, g_r = np.cos(ang) * math.sqrt(2), np.sin(ang) * math.sqrt(2)
        buf = np.concatenate([self._hist, car])
        h = len(self._hist)
        refl = [np.zeros(n), np.zeros(n)]
        for ms, gl, gr in self.REFLECTIONS:
            d = int(ms * SR / 1000)
            tap = buf[h - d:h - d + n]
            refl[0] += gl * tap
            refl[1] += gr * tap
        self._hist = buf[-h:]
        for c in range(2):   # les réflexions sont plus sourdes que le son direct
            refl[c], self._refl_lp[c] = _one_pole(refl[c], 0.35, self._refl_lp[c])
        chans = [car * g_l + refl[0] + fx, car * g_r + refl[1] + fx]

        # bus master : EQ par canal (coupe-bas 40 Hz pour garder le grave, aigus adoucis)
        for c in range(2):
            low, self._hp_lp[c] = _one_pole(chans[c], 2 * math.pi * 40 / SR, self._hp_lp[c])
            chans[c], self._smooth_lp[c] = _one_pole(chans[c] - low, 0.75, self._smooth_lp[c])
        # compresseur commun aux deux canaux (gain lissé : attaque rapide, relâchement lent)
        rms = float(np.sqrt(np.mean(chans[0] ** 2 + chans[1] ** 2) / 2)) + 1e-9
        target = 1.0
        if rms > self.COMP_THRESHOLD:
            target = (self.COMP_THRESHOLD / rms) ** (1.0 - 1.0 / self.COMP_RATIO)
        speed = 0.6 if target < self._comp_gain else 0.15
        g1 = self._comp_gain + (target - self._comp_gain) * speed
        gain_ramp = self._comp_gain + (g1 - self._comp_gain) * k
        self._comp_gain = g1
        # limiteur doux : jamais au-delà du plafond, sans écrêtage dur
        out = [self.CEILING * np.tanh(ch * gain_ramp / self.CEILING) * self.volume for ch in chans]
        return np.column_stack(out)
