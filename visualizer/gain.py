"""Gain: decides how loud a sound has to be before its bar appears.

Everything is expressed as a "floor" in dB: anything at the floor is an empty
bar, and the floor + DB_RANGE is a full bar.

  * Auto mode follows the music: it measures how loud recent frames have been
    and moves the floor so loud and quiet songs both fill the screen.
  * Manual mode uses a fixed floor that you move with - and =.
"""
import math

import numpy as np

from . import config


class GainControl:
    def __init__(self, auto=True):
        self.auto = auto
        self.offset_db = 0.0                       # your - / = tweak while in auto mode
        self.manual_floor_db = config.MANUAL_FLOOR_DB
        self._reference_db = -30.0                 # auto mode's idea of "typically loud"

    def update(self, band_db, dt):
        """Track the music's loudness. Call once per frame, even in manual mode,
        so switching to auto later starts from a sensible level."""
        loud = float(np.percentile(band_db, 90))   # the loudest ~10% of bands this frame
        if loud > config.SILENCE_DB:               # during silence, hold steady
            tau = config.GAIN_ATTACK if loud > self._reference_db else config.GAIN_RELEASE
            self._reference_db += (loud - self._reference_db) * (1.0 - math.exp(-dt / tau))

    def floor(self):
        if not self.auto:
            return self.manual_floor_db
        top = max(self._reference_db, config.MIN_REF_DB) + config.HEADROOM_DB + self.offset_db
        return top - config.DB_RANGE

    def adjust(self, direction):
        """direction > 0 = more sensitive (taller bars), < 0 = less."""
        delta = -direction * config.SENS_STEP_DB
        if self.auto:
            self.offset_db += delta
        else:
            self.manual_floor_db += delta

    def toggle_auto(self):
        if self.auto:
            self.manual_floor_db = self.floor()    # hand over without the bars jumping
        self.auto = not self.auto

    def describe(self):
        if self.auto:
            return f"auto gain {self.offset_db:+.0f} dB"
        return f"manual floor {self.manual_floor_db:.0f} dB"
