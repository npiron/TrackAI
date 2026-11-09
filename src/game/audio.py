"""Sons du jeu, synthétisés en code (aucun fichier audio) : moteur, pneus, chocs, bips.

Le moteur est une série de boucles pré-calculées à différents régimes ; on mélange les deux plus
proches du régime courant (pygame ne sait pas changer la hauteur d'un son à la volée).
"""
import math

import numpy as np
import pygame

SR = 22050
ENGINE_BANDS = 20
GEARS = 5


def _sound(wave, volume=1.0):
    w = np.clip(wave * volume, -1.0, 1.0)
    pcm = (w * 32000).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([pcm, pcm]).copy(order="C"))


def _engine_loop(f0, rng):
    """Boucle de ~0,4 s d'un nombre entier de périodes (pas de clic au bouclage)."""
    periods = max(1, round(f0 * 0.4))
    n = int(round(periods * SR / f0))
    t = np.arange(n) / SR
    ph = 2 * math.pi * f0 * t
    w = np.zeros(n)
    for h, a in ((1, 1.0), (2, 0.6), (3, 0.35), (4, 0.18), (5, 0.08)):   # timbre de F1 : haut perché, un peu métallique
        w += a * np.sin(h * ph + h * 0.7)
    w *= 0.75 + 0.25 * np.sin(ph / 2) ** 2          # pulsations d'allumage
    noise = rng.standard_normal(n)
    noise = np.convolve(noise, np.ones(24) / 24, mode="same")   # souffle grave seulement
    w += 0.25 * noise / (np.max(np.abs(noise)) + 1e-9)
    return w / np.max(np.abs(w))


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
            pygame.mixer.init(SR, -16, 2, 512)
        except pygame.error:
            return
        pygame.mixer.set_num_channels(ENGINE_BANDS + 8)
        rng = np.random.default_rng(1)
        self.freqs = np.geomspace(90.0, 420.0, ENGINE_BANDS)   # F1 : ça monte haut dans les tours
        self.engine = [_sound(_engine_loop(f, rng), 0.55) for f in self.freqs]
        self.eng_ch = [pygame.mixer.Channel(i) for i in range(ENGINE_BANDS)]
        for ch, snd in zip(self.eng_ch, self.engine):
            ch.play(snd, loops=-1)
            ch.set_volume(0.0)
        self.skid = _sound(_filtered_noise(SR, rng, 9, ((420, 0.25), (610, 0.15))), 0.45)
        self.skid_ch = pygame.mixer.Channel(ENGINE_BANDS)
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
        self._rpm = 0.0
        self.ok = True

    def toggle_mute(self):
        self.muted = not self.muted
        if self.ok and self.muted:
            for ch in self.eng_ch:
                ch.set_volume(0.0)
            self.skid_ch.set_volume(0.0)

    def play(self, name, volume=1.0):
        if self.ok and not self.muted:
            snd = getattr(self, name)
            snd.set_volume(volume)
            snd.play()

    def update(self, speed_frac, throttle, slip_deg, drifting, braking, running=True):
        """À appeler à chaque image. speed_frac : vitesse / vitesse max."""
        if not self.ok or self.muted:
            return
        # régime : monte dans chaque rapport puis retombe au passage du suivant
        x = max(0.0, min(1.0, speed_frac)) * GEARS
        gear = min(GEARS - 1, int(x))
        in_gear = x - gear if speed_frac < 1.0 else 1.0
        target = 0.18 + 0.8 * in_gear if gear > 0 else 0.15 + 0.85 * in_gear
        if not throttle:
            target *= 0.85
        self._rpm += (target - self._rpm) * 0.35
        pos = self._rpm * (ENGINE_BANDS - 1)
        i = int(pos)
        frac = pos - i
        loud = (0.45 if throttle else 0.25) if running else 0.2
        for k, ch in enumerate(self.eng_ch):
            v = 0.0
            if k == i:
                v = 1.0 - frac
            elif k == i + 1:
                v = frac
            ch.set_volume(v * loud)
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
            for ch in self.eng_ch:
                ch.set_volume(0.0)
            self.skid_ch.set_volume(0.0)
