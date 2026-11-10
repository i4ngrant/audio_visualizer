"""Drawing. Each display mode is one function: draw_<mode>(surface, frame).

To add a new mode, write a function with that signature, add it to RENDERERS,
and add its name to MODES in config.py.
"""
import math
from dataclasses import dataclass

import numpy as np
import pygame

from . import config


@dataclass
class Frame:
    """Everything a renderer needs to draw one frame."""
    levels: np.ndarray      # bar heights, 0..1, one per bar
    peaks: np.ndarray       # peak-cap heights, 0..1
    samples: np.ndarray     # raw audio (for the waveform)
    colors: list            # one RGB tuple per bar
    pulse: float            # 0..1 beat strength (0 when beat effects are off)


def _bar_layout(width, n):
    """Return (spacing between bar starts, width of each bar)."""
    spacing = width / n
    gap = 2 if spacing >= 6 else 1                 # thinner gaps when bars are skinny
    return spacing, max(1, int(spacing) - gap)


def draw_bars(surf, frame):
    w, h = surf.get_size()
    n = len(frame.levels)
    usable = h - 40
    spacing, bar_w = _bar_layout(w, n)
    for i in range(n):
        x = int(i * spacing) + 1
        bar_h = int(frame.levels[i] * usable)
        if bar_h > 0:
            pygame.draw.rect(surf, frame.colors[i], (x, h - bar_h, bar_w, bar_h))
        cap_y = h - int(frame.peaks[i] * usable) - 4
        pygame.draw.rect(surf, (235, 235, 235), (x, cap_y, bar_w, 3))


def draw_mirrored(surf, frame):
    w, h = surf.get_size()
    n = len(frame.levels)
    mid = h // 2
    usable = (h // 2 - 20) * (1 + 0.08 * frame.pulse)    # slight stretch on the beat
    spacing, bar_w = _bar_layout(w, n)
    for i in range(n):
        x = int(i * spacing) + 1
        half = min(h // 2, int(frame.levels[i] * usable))
        pygame.draw.rect(surf, frame.colors[i], (x, mid - half, bar_w, 2 * half + 1))


def draw_circular(surf, frame):
    w, h = surf.get_size()
    n = len(frame.levels)
    cx, cy = w / 2, h / 2
    size = min(w, h)
    bass = float(frame.levels[:max(2, n // 10)].mean())
    radius = size * 0.17 * (1 + 0.2 * bass + 0.15 * frame.pulse)   # breathes with the bass
    max_len = size * 0.30
    thickness = max(1, int(math.pi * radius / n * 0.7))
    for i in range(n):
        # Bass at the top, treble at the bottom, mirrored left and right.
        a = math.pi * (i + 0.5) / n
        length = 4 + frame.levels[i] * max_len
        for angle in (-math.pi / 2 + a, -math.pi / 2 - a):
            dx, dy = math.cos(angle), math.sin(angle)
            pygame.draw.line(surf, frame.colors[i],
                             (cx + radius * dx, cy + radius * dy),
                             (cx + (radius + length) * dx, cy + (radius + length) * dy),
                             thickness)
    pygame.draw.circle(surf, frame.colors[0], (int(cx), int(cy)),
                       int(radius - 4), 2 + int(3 * frame.pulse))


def draw_waveform(surf, frame):
    w, h = surf.get_size()
    data = frame.samples[-2048:]
    # Start at a rising zero crossing so the wave holds still instead of jittering.
    rising = np.where((data[:-1] < 0) & (data[1:] >= 0))[0]
    start = int(rising[0]) if len(rising) and rising[0] < 1024 else 0
    seg = data[start:start + 1024]
    scale = 0.9 / max(float(np.abs(seg).max()), 0.05)    # auto-zoom to fill the height
    xs = np.linspace(0, w - 1, len(seg))
    ys = h / 2 - seg * scale * (h / 2 - 20)
    pygame.draw.line(surf, (40, 40, 60), (0, h // 2), (w, h // 2), 1)
    pygame.draw.lines(surf, frame.colors[len(frame.colors) // 2], False,
                      np.column_stack((xs, ys)).tolist(), 2 + int(2 * frame.pulse))


RENDERERS = {
    "bars": draw_bars,
    "mirrored": draw_mirrored,
    "circular": draw_circular,
    "waveform": draw_waveform,
}


# ---------------------------------------------------------------- post effects
def add_glow(dest, src, boost=1.0):
    """Bloom: shrink the frame (which blurs it), scale it back up, add it on top."""
    w, h = src.get_size()
    for shrink, strength in config.GLOW_LAYERS:
        small = pygame.transform.smoothscale(src, (max(1, w // shrink), max(1, h // shrink)))
        k = max(0, min(255, int(255 * strength * boost)))
        small.fill((k, k, k), special_flags=pygame.BLEND_RGB_MULT)    # dim to taste
        dest.blit(pygame.transform.smoothscale(small, (w, h)), (0, 0),
                  special_flags=pygame.BLEND_RGB_ADD)


def add_flash(dest, color, pulse):
    """Brighten the whole screen with a tint of `color` on a beat."""
    f = config.FLASH_STRENGTH * pulse
    dest.fill(tuple(int(c * f) for c in color), special_flags=pygame.BLEND_RGB_ADD)
