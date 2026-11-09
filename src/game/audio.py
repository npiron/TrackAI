"""Sons du jeu, synthétisés en code (aucun fichier audio), mixés comme sur une console.

Tout passe par un seul flux (un seul canal pygame) rendu par morceaux de 60 ms :
  sources    : moteur électrique (sifflement continu qui suit la vitesse, un seul rapport, + souffle d'air),
               pneus (frottement sourd en glisse/freinage), effets ponctuels (choc, bips, carillon, fanfare)
  bus master : EQ (coupe-bas 70 Hz, adoucissement des aigus) -> compresseur -> limiteur doux
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
        self._phase = np.zeros(len(self.PARTIALS))
        self._air_lp = 0.0
        self._skid_lp = 0.0
        self._skid_lp2 = 0.0
        self._squeal_ph = 0.0
        self._squeal_t = 0.0
        self._hp_lp = 0.0                     # état du coupe-bas (passe-bas soustrait)
        self._smooth_lp = 0.0                 # état de l'adoucissement des aigus
        self._comp_gain = 1.0
        self._prev = np.zeros(4)              # (fréquence, sifflement, air, pneus) du morceau précédent
        self._target = np.zeros(4)
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
        freq = 160.0 + 300.0 * v                      # un seul rapport : la hauteur suit la vitesse
        whine = 0.65 * (0.10 + 0.32 * v) * (1.0 if throttle else 0.55)   # moteur un peu en retrait
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
        self._target = np.array([freq, whine, air, skid])

    def silence(self):
        """Coupe moteur et pneus (les effets, comme la fanfare d'arrivée, continuent)."""
        if self.ok:
            self._target = np.array([self._prev[0], 0.0, 0.0, 0.0])

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

    def _render(self):
        n = int(SR * self.CHUNK)
        k = np.linspace(0.0, 1.0, n, endpoint=False)
        f0, w0, a0, s0 = self._prev
        f1, w1, a1, s1 = self._target
        f = f0 + (f1 - f0) * k
        whine = w0 + (w1 - w0) * k
        air = a0 + (a1 - a0) * k
        skid = s0 + (s1 - s0) * k
        self._prev = self._target.copy()

        # moteur : phases continues d'un morceau à l'autre
        motor = np.zeros(n)
        for idx, (mult, gain) in enumerate(self.PARTIALS):
            ph = self._phase[idx] + np.cumsum(2 * math.pi * f * mult / SR)
            motor += gain * np.sin(ph)
            self._phase[idx] = ph[-1] % (2 * math.pi)
        out = motor * whine / 1.6
        noise, self._air_lp = _one_pole(self.rng.standard_normal(n), 0.08, self._air_lp)
        out += air * noise * 1.6
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
        out += skid * (0.75 * band + 0.45 * np.sin(sq_ph))

        # effets ponctuels
        alive = []
        for v in self.voices:
            data, pos, gain = v
            m = min(n, len(data) - pos)
            out[:m] += gain * data[pos:pos + m]
            v[1] = pos + m
            if v[1] < len(data):
                alive.append(v)
        self.voices = alive

        # bus master : EQ
        low, self._hp_lp = _one_pole(out, 2 * math.pi * 70 / SR, self._hp_lp)
        out = out - low                                                  # coupe-bas 70 Hz
        out, self._smooth_lp = _one_pole(out, 0.75, self._smooth_lp)    # adoucit le haut du spectre
        # compresseur (gain lissé d'un morceau à l'autre : attaque rapide, relâchement lent)
        rms = float(np.sqrt(np.mean(out * out))) + 1e-9
        target = 1.0
        if rms > self.COMP_THRESHOLD:
            target = (self.COMP_THRESHOLD / rms) ** (1.0 - 1.0 / self.COMP_RATIO)
        speed = 0.6 if target < self._comp_gain else 0.15
        g1 = self._comp_gain + (target - self._comp_gain) * speed
        out *= self._comp_gain + (g1 - self._comp_gain) * k
        self._comp_gain = g1
        # limiteur doux : jamais au-delà du plafond, sans écrêtage dur
        out = self.CEILING * np.tanh(out / self.CEILING)

        pcm = (out * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(np.column_stack([pcm, pcm]).copy(order="C"))
