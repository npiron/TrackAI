"""Sons du jeu, synthétisés en code (aucun fichier audio) : moteur électrique, pneus, chocs, bips.

Le moteur est celui d'une monoplace électrique (type Formula E) : un sifflement de turbine qui monte
continûment avec la vitesse (un seul rapport), plus le souffle de l'air. Il est généré en continu par
petits morceaux (~40 ms), phase continue, pour que la hauteur glisse sans palier ni clic.
"""
import math

import numpy as np
import pygame

SR = 22050


def _sound(wave, volume=1.0):
    w = np.clip(wave * volume, -1.0, 1.0)
    pcm = (w * 32000).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([pcm, pcm]).copy(order="C"))


def _filtered_noise(n, rng, smooth, tones=()):
    """Bruit adouci (passe-bas par moyenne glissante) : un frottement sourd, pas un sifflement."""
    x = rng.standard_normal(n)
    x = np.convolve(x, np.ones(smooth) / smooth, mode="same")
    t = np.arange(n) / SR
    for f, a in tones:
        x += a * np.sin(2 * math.pi * f * t) * (0.6 + 0.4 * np.sin(2 * math.pi * 7 * t))
    return x / np.max(np.abs(x))


def _tone(freqs, dur, decay=6.0):
    t = np.arange(int(dur * SR)) / SR
    w = sum(np.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
    env = np.minimum(1.0, t / 0.01) * np.exp(-decay * t)
    return w * env


class CarAudio:
    def __init__(self):
        self.ok = False
        self.muted = False
        try:
            pygame.mixer.init(SR, -16, 2, 1024)   # tampon plus grand : pas de trou entre les morceaux
        except pygame.error:
            return
        pygame.mixer.set_num_channels(10)
        pygame.mixer.set_reserved(8)       # canaux 0-7 réservés : aucun effet ne peut prendre celui du moteur
        self._fx_ch = {name: pygame.mixer.Channel(2 + i)
                       for i, name in enumerate(("hit", "beep", "go", "chime", "fanfare"))}
        self._keep = []                    # références aux morceaux du moteur en cours/en attente
        rng = np.random.default_rng(1)
        self.rng = rng
        self.motor_ch = pygame.mixer.Channel(0)
        self._phase = np.zeros(4)          # phases continues des composantes du sifflement
        self._lp = 0.0                     # état du filtre du souffle d'air
        self._prev = (0.0, 0.0, 0.0)       # (fréquence, volume sifflement, volume air) du morceau précédent
        self.skid = _sound(_filtered_noise(SR, rng, 9, ((420, 0.25), (610, 0.15))), 0.45)
        self.skid_ch = pygame.mixer.Channel(1)
        self.skid_ch.play(self.skid, loops=-1)
        self.skid_ch.set_volume(0.0)
        t = np.arange(int(0.22 * SR)) / SR
        thud = (rng.standard_normal(len(t)) * np.exp(-28 * t) * 0.8
                + np.sin(2 * math.pi * 70 * t) * np.exp(-14 * t))
        self.hit = _sound(thud / np.max(np.abs(thud)), 0.9)
        self.beep = _sound(_tone([440], 0.16, 12), 0.3)
        self.go = _sound(_tone([587, 880], 0.4, 6), 0.3)
        self.chime = _sound(np.concatenate([_tone([659], 0.08, 20), _tone([988], 0.22, 10)]), 0.22)
        fan = [_tone([f, f * 1.5], 0.15, 8) for f in (392, 494, 587)] + [_tone([784, 988, 1175], 0.8, 3.5)]
        self.fanfare = _sound(np.concatenate(fan), 0.28)
        self.ok = True

    def toggle_mute(self):
        self.muted = not self.muted
        if self.ok and self.muted:
            self.silence()

    def play(self, name, volume=1.0):
        if self.ok and not self.muted:
            snd = getattr(self, name)
            ch = self._fx_ch[name]          # chaque effet a son canal : il ne coupe ni le moteur ni les autres
            ch.set_volume(volume)
            ch.play(snd)

    # Sifflement : fondamentale + harmoniques légèrement désaccordées (moteur + onduleur + pignons)
    PARTIALS = ((1.0, 1.0), (2.0, 0.32), (3.02, 0.10), (0.5, 0.25))
    CHUNK = 0.06  # s

    def _motor_chunk(self, f1, a1, w1):
        """Un morceau de son, en interpolant depuis l'état précédent (aucun saut de hauteur ni de volume)."""
        n = int(SR * self.CHUNK)
        f0, a0, w0 = self._prev
        k = np.linspace(0.0, 1.0, n, endpoint=False)
        f = f0 + (f1 - f0) * k
        amp = a0 + (a1 - a0) * k
        air = w0 + (w1 - w0) * k
        out = np.zeros(n)
        for idx, (mult, gain) in enumerate(self.PARTIALS):
            ph = self._phase[idx] + np.cumsum(2 * math.pi * f * mult / SR)
            out += gain * np.sin(ph)
            self._phase[idx] = ph[-1] % (2 * math.pi)
        out *= amp / 1.6
        # souffle de l'air : bruit adouci (filtre passe-bas d'ordre 1)
        noise = self.rng.standard_normal(n)
        lp = np.empty(n)
        y = self._lp
        for t in range(n):
            y += 0.08 * (noise[t] - y)
            lp[t] = y
        self._lp = y
        out += air * lp * 1.6
        out *= 0.8   # marge : moteur + pneus + effets ensemble ne saturent pas
        self._prev = (f1, a1, w1)
        return _sound(out)

    def update(self, speed_frac, throttle, slip_deg, drifting, braking, running=True):
        """À appeler à chaque image. speed_frac : vitesse réelle / vitesse max."""
        if not self.ok or self.muted:
            return
        v = max(0.0, min(1.1, speed_frac))
        # un seul rapport : la hauteur suit directement la vitesse (doux en bas, chante en haut)
        freq = 70.0 + 330.0 * v
        whine = (0.10 + 0.32 * v) * (1.0 if throttle else 0.55)   # moins fort au lever de pied (récupération)
        if not running:
            whine = 0.05
        air = 0.18 * v * v
        if self.motor_ch.get_queue() is None:
            snd = self._motor_chunk(freq, whine, air)
            if self.motor_ch.get_busy():
                self.motor_ch.queue(snd)
                self._keep = self._keep[-1:] + [snd]   # garder vivants le morceau joué et celui en attente
            else:
                self.motor_ch.play(snd)
                self._keep = [snd]
        screech = 0.0
        if speed_frac > 0.15:
            screech = max(0.0, min(1.0, (slip_deg - 8.0) / 22.0))
            if drifting:
                screech = max(screech, 0.55)
            if braking:
                screech = max(screech, 0.35)
        self.skid_ch.set_volume(screech * 0.4 * min(1.0, speed_frac * 1.5))

    def silence(self):
        if self.ok:
            self.motor_ch.stop()
            self._prev = (0.0, 0.0, 0.0)
            self.skid_ch.set_volume(0.0)
