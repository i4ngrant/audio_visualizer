"""The main loop: read audio -> analyze -> draw -> repeat, 60 times a second."""
import time

import pygame

from . import config
from .analysis import LevelSmoother, SpectrumAnalyzer, to_bar_heights
from .beat import BeatDetector
from .controls import KEYMAP
from .gain import GainControl
from .hud import Hud
from .palettes import PALETTE_NAMES, palette_colors
from .renderers import RENDERERS, Frame, add_flash, add_glow


class Visualizer:
    def __init__(self, audio, num_bars=config.DEFAULT_BARS, palette="rainbow"):
        self.audio = audio

        # What you can change with the keyboard
        self.num_bars = max(config.BAR_COUNTS[0], min(config.BAR_COUNTS[-1], num_bars))
        self.palette = PALETTE_NAMES.index(palette)
        self.mode = 0
        self.glow = True
        self.beat_fx = True
        self.trails = False
        self.show_help = True
        self.fullscreen = False
        self.running = True

        # Long-lived helpers
        self.gain = GainControl()
        self.beats = BeatDetector()

        # Window
        pygame.init()
        pygame.display.set_caption(f"Audio Visualizer - {audio.device_name}")
        self.screen = pygame.display.set_mode(config.WINDOW_SIZE, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.hud = Hud()
        self._scene = None     # offscreen frame we draw into, so glow can be built from it
        self._fade = None      # translucent layer used for motion trails

        self._rebuild()

    # ------------------------------------------------------------ setup helpers
    def _rebuild(self):
        """Recreate everything that depends on the bar count."""
        self.analyzer = SpectrumAnalyzer(self.audio.rate, self.num_bars)
        self.smoother = LevelSmoother(self.num_bars)
        self._recolor()

    def _recolor(self):
        self.colors = palette_colors(PALETTE_NAMES[self.palette], self.num_bars)
        self.accent = self.colors[len(self.colors) // 4]   # used for the flash and beat light

    def _step_bars(self, direction):
        """Move to the next preset bar count up or down."""
        counts = config.BAR_COUNTS
        options = [b for b in counts if b > self.num_bars] if direction > 0 else \
                  [b for b in counts if b < self.num_bars][::-1]
        if options:
            self.num_bars = options[0]
            self._rebuild()

    def _set_window(self):
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(config.WINDOW_SIZE, pygame.RESIZABLE)

    # ------------------------------------------------------------ input
    def handle_action(self, action):
        if action == "quit":
            self.running = False
        elif action == "next_mode":
            self.mode = (self.mode + 1) % len(config.MODES)
        elif action == "next_palette":
            self.palette = (self.palette + 1) % len(PALETTE_NAMES)
            self._recolor()
        elif action == "more_bars":
            self._step_bars(+1)
        elif action == "fewer_bars":
            self._step_bars(-1)
        elif action == "more_sensitive":
            self.gain.adjust(+1)
        elif action == "less_sensitive":
            self.gain.adjust(-1)
        elif action == "toggle_auto_gain":
            self.gain.toggle_auto()
        elif action == "more_beats":
            self.beats.adjust_sensitivity(+1)
        elif action == "fewer_beats":
            self.beats.adjust_sensitivity(-1)
        elif action == "toggle_glow":
            self.glow = not self.glow
        elif action == "toggle_beat_fx":
            self.beat_fx = not self.beat_fx
        elif action == "toggle_trails":
            self.trails = not self.trails
        elif action == "toggle_help":
            self.show_help = not self.show_help
        elif action == "toggle_fullscreen":
            self.fullscreen = not self.fullscreen
            self._set_window()

    def _process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key in KEYMAP:
                self.handle_action(KEYMAP[event.key])

    # ------------------------------------------------------------ per-frame work
    def _analyze(self, samples, dt):
        """Audio -> smoothed bar heights + beat pulse."""
        band_db, bass_energy = self.analyzer.analyze(samples)
        self.gain.update(band_db, dt)
        self.beats.update(bass_energy, time.perf_counter(), dt)
        self.smoother.update(to_bar_heights(band_db, self.gain.floor()), dt)

    def _draw(self, samples):
        size = self.screen.get_size()
        if self._scene is None or self._scene.get_size() != size:
            self._scene = pygame.Surface(size).convert()
            self._scene.fill(config.BACKGROUND)
            self._fade = pygame.Surface(size, pygame.SRCALPHA)
            self._fade.fill((*config.BACKGROUND, config.TRAIL_ALPHA))

        # 1. Draw the visualization offscreen (fading the last frame if trails are on).
        if self.trails:
            self._scene.blit(self._fade, (0, 0))
        else:
            self._scene.fill(config.BACKGROUND)
        pulse = self.beats.pulse if self.beat_fx else 0.0
        frame = Frame(self.smoother.levels, self.smoother.peaks, samples, self.colors, pulse)
        RENDERERS[config.MODES[self.mode]](self._scene, frame)

        # 2. Copy it to the window and layer the effects on top.
        self.screen.blit(self._scene, (0, 0))
        if self.glow:
            add_glow(self.screen, self._scene, 1.0 + config.GLOW_BEAT_BOOST * pulse)
        if pulse > 0.02:
            add_flash(self.screen, self.accent, pulse)

        # 3. Text and beat light.
        if self.show_help:
            self.hud.draw(self.screen, self._status_text(), self.beats.pulse, self.accent)
        pygame.display.flip()

    def _status_text(self):
        on_off = lambda flag: "on" if flag else "off"
        return (f"{config.MODES[self.mode]}  |  {PALETTE_NAMES[self.palette]}  |  "
                f"{self.num_bars} bars  |  {self.gain.describe()}  |  glow {on_off(self.glow)}  |  "
                f"beat fx {on_off(self.beat_fx)} (x{self.beats.sensitivity:.2f})  |  "
                f"{self.clock.get_fps():.0f} fps")

    # ------------------------------------------------------------ main loop
    def run(self):
        dt = 1.0 / config.FPS
        try:
            while self.running:
                self._process_events()
                samples = self.audio.buffer.read()
                self._analyze(samples, dt)
                self._draw(samples)
                # Real time since the last frame, capped so a hiccup doesn't jump everything.
                dt = min(self.clock.tick(config.FPS) / 1000.0, 0.1)
        finally:
            pygame.quit()
