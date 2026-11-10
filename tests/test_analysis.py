"""Tests for the signal-processing parts. They only need numpy and pytest, so they
run on any OS without audio hardware or a screen:

    py -m pip install pytest
    py -m pytest
"""
import numpy as np
import pytest

from visualizer import config
from visualizer.analysis import LevelSmoother, SpectrumAnalyzer, to_bar_heights
from visualizer.audio import AudioBuffer
from visualizer.beat import BeatDetector
from visualizer.gain import GainControl
from visualizer.palettes import PALETTE_NAMES, palette_colors

RATE = 48000


def sine(freq, amp=0.5, rate=RATE, n=config.FFT_SIZE):
    t = np.arange(n) / rate
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def fake_track(seconds=12, scale=1.0, rate=RATE):
    """120 BPM: kick every 0.5 s, hi-hats on the off-beats, a sustained pad."""
    rng = np.random.default_rng(0)
    t = np.arange(rate * seconds) / rate
    x = 0.12 * np.sin(2 * np.pi * 220 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.25 * t))
    for start in np.arange(0, seconds, 0.5):
        m = (t >= start) & (t < start + 0.25)
        tt = t[m] - start
        x[m] += 0.8 * np.sin(2 * np.pi * (55 + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 12)
    for start in np.arange(0.25, seconds, 0.5):
        m = (t >= start) & (t < start + 0.05)
        x[m] += 0.15 * rng.standard_normal(m.sum()) * np.exp(-(t[m] - start) * 60)
    return (x * scale).astype(np.float32)


def run_track(track, rate=RATE, fps=60):
    """Feed a track through the pipeline frame by frame, like the app does."""
    analyzer = SpectrumAnalyzer(rate, 64)
    beats, gain = BeatDetector(), GainControl()
    buf, hop, dt = np.zeros(config.FFT_SIZE, np.float32), rate // fps, 1 / fps
    beat_times, heights = [], []
    for i in range(0, len(track) - hop, hop):
        buf = np.concatenate((buf[hop:], track[i:i + hop]))
        now = i / rate
        band_db, bass = analyzer.analyze(buf)
        gain.update(band_db, dt)
        if beats.update(bass, now, dt):
            beat_times.append(now)
        if now > 4:                                     # after auto-gain settles
            heights.append(to_bar_heights(band_db, gain.floor()))
    return beat_times, np.array(heights)


# ---------------------------------------------------------------- spectrum
@pytest.mark.parametrize("rate", [44100, 48000])
@pytest.mark.parametrize("num_bars", config.BAR_COUNTS)
def test_band_count_matches_bar_count(rate, num_bars):
    band_db, _ = SpectrumAnalyzer(rate, num_bars).analyze(sine(1000, rate=rate))
    assert len(band_db) == num_bars


def test_louder_bands_follow_the_tone():
    analyzer = SpectrumAnalyzer(RATE, 64)
    low = analyzer.analyze(sine(80))[0].argmax()
    high = analyzer.analyze(sine(6000))[0].argmax()
    assert low < 16 < 48 < high


def test_half_scale_sine_reads_minus_6_db():
    analyzer = SpectrumAnalyzer(RATE, 64)
    band_db, _ = analyzer.analyze(sine(1000, amp=0.5))
    peak = band_db.argmax()
    assert band_db[peak] - analyzer._tilt[peak] == pytest.approx(-6.0, abs=1.0)


def test_bar_heights_are_clamped():
    h = to_bar_heights(np.array([-200.0, -65.0, -35.0, 50.0]), floor_db=-65.0)
    assert list(h) == [0.0, 0.0, 0.5, 1.0]


def test_smoother_rises_fast_and_falls_slowly():
    s = LevelSmoother(1)
    s.update(np.array([1.0]), dt=1 / 60)
    assert s.levels[0] == pytest.approx(0.6)
    s.update(np.array([0.0]), dt=1 / 60)
    assert s.levels[0] == pytest.approx(0.54)
    assert s.peaks[0] == pytest.approx(0.6 - config.PEAK_FALL_PER_SEC / 60)


# ---------------------------------------------------------------- beats + gain
def test_detects_120_bpm_kicks():
    beat_times, _ = run_track(fake_track())
    assert 22 <= len(beat_times) <= 24                  # first kick is used to learn the average
    assert np.median(np.diff(beat_times)) == pytest.approx(0.5, abs=0.02)


def test_quiet_track_still_detected_and_fills_screen():
    loud_beats, loud = run_track(fake_track(scale=1.0))
    quiet_beats, quiet = run_track(fake_track(scale=0.03))   # 30 dB quieter
    assert len(quiet_beats) == len(loud_beats)
    assert quiet.max(axis=1).mean() > 0.7                     # tallest bar still near the top


def test_silence_has_no_beats_and_no_bars():
    beat_times, heights = run_track(np.zeros(RATE * 6, np.float32))
    assert beat_times == []
    assert heights.max() == 0.0


def test_beat_sensitivity_stays_in_range():
    b = BeatDetector()
    for _ in range(100):
        b.adjust_sensitivity(+1)
    assert b.sensitivity == pytest.approx(config.BEAT_SENS_RANGE[0])


def test_switching_gain_mode_does_not_jump():
    g = GainControl()
    g.update(np.full(64, -20.0), dt=1.0)
    before = g.floor()
    g.toggle_auto()
    assert not g.auto and g.floor() == before


# ---------------------------------------------------------------- misc
def test_audio_buffer_keeps_newest_samples():
    b = AudioBuffer(8)
    b.write(np.ones(3, np.float32))
    assert list(b.read()) == [0] * 5 + [1] * 3
    b.write(np.arange(20, dtype=np.float32))
    assert list(b.read()) == list(range(12, 20))


@pytest.mark.parametrize("name", PALETTE_NAMES)
def test_palettes_produce_valid_colors(name):
    colors = palette_colors(name, 16)
    assert len(colors) == 16
    assert all(len(c) == 3 and all(0 <= v <= 255 for v in c) for c in colors)
