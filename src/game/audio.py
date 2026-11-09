"""Sons du jeu, synthétisés en code (aucun fichier audio), mixés comme sur une console.

Tout passe par un seul flux (un seul canal pygame) rendu par morceaux de 60 ms :
  sources    : moteur électrique (sifflement qui monte dans chacun des 5 rapports, + souffle d'air),
               pneus (frottement sourd en glisse/freinage), effets ponctuels (choc, bips, carillon, fanfare)
  bus master : EQ (coupe-bas 40 Hz, adoucissement des aigus) -> compresseur -> limiteur doux, en stéréo
Rien ne peut donc couper un autre son ni saturer la sortie.
"""
import atexit
import math
import threading
import time

import numpy as np
import pygame

SR = 22050


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


class CarAudio:
    CHUNK = 0.08            # s par morceau rendu
    GEARS = 5
    # sifflement : fondamentale + harmoniques légèrement désaccordées (moteur, onduleur, pignons)
    PARTIALS = ((1.0, 1.0), (2.0, 0.32), (3.02, 0.10), (0.5, 0.08))
    # bus master
    COMP_THRESHOLD = 0.35   # niveau RMS au-delà duquel on compresse
    COMP_RATIO = 3.0
    CEILING = 0.89          # limiteur : ~ -1 dBFS

    def __init__(self):
        self.ok = False
        self.muted = False
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
        self.voices = []                      # effets en cours : [échantillons, position, gain]
        self._phase = np.zeros((3, len(self.PARTIALS)))   # sifflement : centre, gauche, droite
        self._low_phase = np.zeros(2)                        # couche grave de puissance
        self._air_lp = 0.0
        self._skid_lp = 0.0
        self._skid_lp2 = 0.0
        self._squeal_ph = 0.0
        self._squeal_t = 0.0
        self._hp_lp = np.zeros(2)             # état du coupe-bas (passe-bas soustrait), par canal
        self._smooth_lp = np.zeros(2)         # état de l'adoucissement des aigus, par canal
        self._comp_gain = 1.0
        self._gear = 0
        self._shift_dip = 0                   # images restantes du creux de volume au changement de rapport
        # (fréquence, sifflement, air, pneus, charge, fréquence grave) du morceau précédent
        self._prev = np.zeros(6)
        self._target = np.zeros(6)
        self._keep = []
        self._lock = threading.Lock()
        self.ok = True
        # un fil dédié alimente le son en continu : il ne dépend plus du rythme de l'affichage
        # (si l'image prend du retard, par exemple pendant un entraînement, le son ne crépite pas)
        self._running = True
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()
        atexit.register(self.close)   # s'arrête avant que pygame ne se ferme

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
    def toggle_mute(self):
        self.muted = not self.muted
        if self.ok and self.muted:
            with self._lock:
                self.ch.stop()
                self.voices.clear()

    def play(self, name, volume=1.0):
        if self.ok and not self.muted:
            with self._lock:
                self.voices.append([self.samples[name], 0, float(volume)])

    def update(self, speed_frac, throttle, slip_deg, drifting, braking, running=True):
        """À appeler à chaque image. speed_frac : vitesse réelle / vitesse max."""
        if not self.ok or self.muted:
            return
        v = max(0.0, min(1.1, speed_frac))
        # rapports : le sifflement monte dans chaque rapport puis redescend au passage du suivant
        x = min(v, 0.999) * self.GEARS
        gear = int(x)
        freq = 170.0 + 30.0 * gear + 250.0 * (x - gear)
        if gear != self._gear:
            if gear > self._gear and throttle:
                self._shift_dip = 3          # petit creux de volume : on « entend » passer le rapport
            self._gear = gear
        whine = 0.65 * (0.10 + 0.32 * v) * (1.0 if throttle else 0.55)   # moteur un peu en retrait
        if self._shift_dip > 0:
            whine *= 0.45
            self._shift_dip -= 1
        if not running:
            whine = 0.035
        air = 0.18 * max(0.0, (v - 0.55) / 0.45) ** 2   # le souffle d'air ne vient qu'à haute vitesse
        skid = 0.0
        if v > 0.15:
            skid = max(0.0, min(1.0, (slip_deg - 8.0) / 22.0))
            if drifting:
                skid = max(skid, 0.55)
            if braking:
                skid = max(skid, 0.35)
            skid *= 0.2 * min(1.0, v * 1.5)   # crissement présent mais discret
        load = 1.0 if (throttle and running) else 0.0
        low_f = 55.0 + 45.0 * v              # la couche grave suit la vitesse, sans les rapports
        self._target = np.array([freq, whine, air, skid, load, low_f])

    def silence(self):
        """Coupe moteur et pneus (les effets, comme la fanfare d'arrivée, continuent)."""
        if self.ok:
            self._target = np.array([self._prev[0], 0.0, 0.0, 0.0, 0.0, self._prev[5]])

    # --- rendu ---
    def _feed(self):
        if self.ch.get_queue() is not None:
            return
        snd = self._render()
        if self.ch.get_busy():
            self.ch.queue(snd)
            self._keep = self._keep[-1:] + [snd]   # garder vivants le morceau joué et celui en attente
        else:
            self.ch.play(snd)
            self._keep = [snd]

    DETUNE = (1.0, 0.993, 1.007)   # sifflement au centre, un peu plus bas à gauche, plus haut à droite

    def _render(self):
        n = int(SR * self.CHUNK)
        k = np.linspace(0.0, 1.0, n, endpoint=False)
        p0, p1 = self._prev, self._target
        f, whine, air, skid, load, low_f = (p0[i] + (p1[i] - p0[i]) * k for i in range(6))
        self._prev = self._target.copy()

        # moteur : 3 voix légèrement désaccordées (centre, gauche, droite) -> son large, pas « petite voiture »
        voices = []
        for vi, det in enumerate(self.DETUNE):
            m = np.zeros(n)
            for idx, (mult, gain) in enumerate(self.PARTIALS):
                if mult > 1.0:
                    gain = gain * (0.7 + 0.8 * load)     # plus de mordant en accélération
                ph = self._phase[vi, idx] + np.cumsum(2 * math.pi * f * det * mult / SR)
                m += gain * np.sin(ph)
                self._phase[vi, idx] = ph[-1] % (2 * math.pi)
            voices.append(m)
        drive = 1.0 + 0.8 * load                          # légère saturation sous charge
        sat = [np.tanh(drive * m / 1.6) / np.tanh(drive) for m in voices]
        center = sat[0] * whine
        left = center * 0.6 + sat[1] * whine * 0.55
        right = center * 0.6 + sat[2] * whine * 0.55
        # couche grave de puissance (fondamentale + octave), au centre
        lows = np.zeros(n)
        for j, (mult, gain) in enumerate(((1.0, 1.0), (2.0, 0.4))):
            ph = self._low_phase[j] + np.cumsum(2 * math.pi * low_f * mult / SR)
            lows += gain * np.sin(ph)
            self._low_phase[j] = ph[-1] % (2 * math.pi)
        lows *= whine * (0.55 + 0.35 * load) * 0.6
        left = left + lows
        right = right + lows

        # souffle d'air (un peu différent à gauche et à droite)
        noise, self._air_lp = _one_pole(self.rng.standard_normal(n), 0.08, self._air_lp)
        left = left + air * noise * 1.6
        right = right + air * np.roll(noise, 157) * 1.6
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
        tyre = skid * (0.75 * band + 0.45 * np.sin(sq_ph))
        left = left + tyre
        right = right + tyre

        # effets ponctuels (au centre)
        fx = np.zeros(n)
        alive = []
        for v in self.voices:
            data, pos, gain = v
            m = min(n, len(data) - pos)
            fx[:m] += gain * data[pos:pos + m]
            v[1] = pos + m
            if v[1] < len(data):
                alive.append(v)
        self.voices = alive
        chans = [left + fx, right + fx]

        # bus master : EQ par canal (coupe-bas 40 Hz pour garder la couche grave, aigus adoucis)
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
        out = [self.CEILING * np.tanh(ch * gain_ramp / self.CEILING) for ch in chans]
        pcm = np.column_stack([(o * 32767).astype(np.int16) for o in out])
        return pygame.sndarray.make_sound(pcm.copy(order="C"))
