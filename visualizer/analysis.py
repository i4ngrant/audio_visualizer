"""Signal processing: samples -> FFT -> bar heights.

Pipeline for each frame:
    1. SpectrumAnalyzer.analyze()  samples -> loudness (dB) of each frequency band
    2. GainControl.floor()         decides which dB value counts as an empty bar
    3. to_bar_heights()            dB -> 0..1 bar heights
    4. LevelSmoother.update()      makes the bars rise fast and fall gently
"""
import numpy as np

from . import config


class SpectrumAnalyzer:
    """Splits the spectrum into `num_bars` bands spaced like a piano keyboard
    (logarithmically), so bass and treble each get a fair share of the bars."""

    def __init__(self, rate, num_bars):
        self.num_bars = num_bars
        self._window = np.hanning(config.FFT_SIZE).astype(np.float32)
        self._norm = 2.0 / self._window.sum()      # a full-volume sine wave reads 0 dB
        freqs = np.fft.rfftfreq(config.FFT_SIZE, 1.0 / rate)

        # Band edges, e.g. 30, 33, 37, ... 16000 Hz, converted to FFT bin indices.
        edges = np.geomspace(config.F_MIN, min(config.F_MAX, rate / 2), num_bars + 1)
        idx = np.searchsorted(freqs, edges)
        self._bands = [(idx[i], max(idx[i + 1], idx[i] + 1)) for i in range(num_bars)]

        # Music naturally has less energy up high; tilt it so treble bars move too.
        centers = np.sqrt(edges[:-1] * edges[1:])
        self._tilt = config.TILT_DB_PER_OCTAVE * np.log2(centers / 1000.0)

        lo, hi = np.searchsorted(freqs, [config.BASS_LO, config.BASS_HI])
        self._bass_bins = (lo, max(hi, lo + 1))

    def analyze(self, samples):
        """Return (band loudness in dB, bass energy for beat detection)."""
        magnitude = np.abs(np.fft.rfft(samples * self._window)) * self._norm

        lo, hi = self._bass_bins
        bass_energy = float(np.sum(magnitude[lo:hi] ** 2))

        bands = np.array([magnitude[lo:hi].max() for lo, hi in self._bands])
        band_db = 20.0 * np.log10(bands + 1e-12) + self._tilt
        return band_db, bass_energy


def to_bar_heights(band_db, floor_db):
    """Map dB to 0..1, where floor_db is an empty bar and floor_db + DB_RANGE is full."""
    return np.clip((band_db - floor_db) / config.DB_RANGE, 0.0, 1.0)


class LevelSmoother:
    """Keeps bars from flickering: they jump up quickly and fall back gently.
    Also tracks the peak caps that float above each bar."""

    def __init__(self, num_bars):
        self.levels = np.zeros(num_bars)
        self.peaks = np.zeros(num_bars)

    def update(self, target, dt):
        frames = dt * 60.0     # tuned at 60 fps; scale so it feels the same at any frame rate
        rise = 1.0 - config.RISE_KEEP ** frames
        rising = target > self.levels
        self.levels = np.where(rising,
                               self.levels + (target - self.levels) * rise,
                               np.maximum(target, self.levels * config.FALL_KEEP ** frames))
        self.peaks = np.where(self.levels > self.peaks, self.levels,
                              np.maximum(self.peaks - config.PEAK_FALL_PER_SEC * dt, 0.0))
