"""Every tunable number in one place. Change things here, not in the code."""

# ---------------------------------------------------------------- audio capture
FFT_SIZE = 4096          # samples per FFT (~85 ms at 48 kHz); bigger = finer bass detail
CALLBACK_FRAMES = 512    # samples delivered per audio callback
STALE_AFTER = 0.15       # seconds without new audio before the buffer is treated as silence

# ---------------------------------------------------------------- spectrum
BAR_COUNTS = [16, 24, 32, 48, 64, 80, 96, 112, 128]   # steps for the , and . keys
DEFAULT_BARS = 64
F_MIN, F_MAX = 30.0, 16000.0   # frequency range shown, in Hz
DB_RANGE = 60.0                # dB span between an empty bar and a full one
TILT_DB_PER_OCTAVE = 3.0       # boosts treble so high bars move as much as bass

# ---------------------------------------------------------------- bar motion (per 60 fps frame)
RISE_KEEP = 0.4          # when rising, fraction of the gap left after one frame (lower = snappier)
FALL_KEEP = 0.90         # when falling, fraction of the height kept each frame
PEAK_FALL_PER_SEC = 0.36 # how fast the peak caps drift down (screen heights per second)

# ---------------------------------------------------------------- gain
MANUAL_FLOOR_DB = -65.0  # starting floor when auto-gain is off
SENS_STEP_DB = 3.0       # how much - and = change the sensitivity
SILENCE_DB = -75.0       # quieter than this counts as silence: auto-gain holds steady
MIN_REF_DB = -55.0       # auto-gain never boosts quiet music beyond this level
HEADROOM_DB = 6.0        # room above the "typical loud" level before bars hit the top
GAIN_ATTACK = 0.3        # seconds for auto-gain to react to louder music
GAIN_RELEASE = 4.0       # seconds for auto-gain to relax after it gets quieter

# ---------------------------------------------------------------- beat detection
BASS_LO, BASS_HI = 40.0, 140.0   # kick-drum range in Hz
BEAT_SENSITIVITY = 1.45          # bass must exceed its recent average by this factor
BEAT_SENS_RANGE = (1.10, 2.50)   # limits for the [ and ] keys
BEAT_SENS_STEP = 0.05
BEAT_WINDOW = 1.0                # seconds of history used for the average
BEAT_COOLDOWN = 0.22             # minimum seconds between beats (caps at ~270 BPM)
BEAT_MIN_ENERGY = 1e-6           # ignore near-silence
PULSE_DECAY = 5.0                # how fast beat effects fade (higher = shorter, ~1/x seconds)

# ---------------------------------------------------------------- display
FPS = 60
WINDOW_SIZE = (1280, 720)
BACKGROUND = (8, 8, 14)
TRAIL_ALPHA = 55                 # 0-255: lower = longer motion trails
FLASH_STRENGTH = 0.22            # brightness of the background flash on a beat
GLOW_LAYERS = [(6, 0.55), (18, 0.45)]   # (shrink factor, strength): small = tight glow, big = wide halo
GLOW_BEAT_BOOST = 0.8            # extra glow on a beat
MODES = ["bars", "mirrored", "circular", "waveform"]
