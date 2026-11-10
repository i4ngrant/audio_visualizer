"""Beat detection: spots kick drums by watching for sudden jumps in bass energy."""
import math
from collections import deque

from . import config


class BeatDetector:
    """A beat is when the bass is much louder than its average over the last second.

    `pulse` jumps to 1.0 on each beat and fades back to 0, so effects (flash,
    glow, circle size) can scale with it smoothly instead of blinking.
    """

    def __init__(self, sensitivity=config.BEAT_SENSITIVITY):
        self.sensitivity = sensitivity     # bass must exceed average * sensitivity
        self.pulse = 0.0
        self._history = deque()            # (time, energy) over the last BEAT_WINDOW seconds
        self._prev_energy = 0.0
        self._last_beat = -1.0

    def update(self, energy, now, dt):
        """Feed one frame of bass energy. Returns True if this frame is a beat."""
        self.pulse *= math.exp(-dt * config.PULSE_DECAY)
        while self._history and now - self._history[0][0] > config.BEAT_WINDOW:
            self._history.popleft()

        beat = False
        if len(self._history) >= 10:       # need some history before judging
            average = sum(e for _, e in self._history) / len(self._history)
            beat = (energy > average * self.sensitivity
                    and energy > self._prev_energy              # only on the way up
                    and energy > config.BEAT_MIN_ENERGY
                    and now - self._last_beat > config.BEAT_COOLDOWN)
            if beat:
                self._last_beat = now
                self.pulse = 1.0

        self._history.append((now, energy))
        self._prev_energy = energy
        return beat

    def adjust_sensitivity(self, direction):
        """direction > 0 detects more beats, < 0 is stricter."""
        lo, hi = config.BEAT_SENS_RANGE
        new = self.sensitivity - direction * config.BEAT_SENS_STEP
        self.sensitivity = max(lo, min(hi, new))
