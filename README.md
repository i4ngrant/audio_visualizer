# audio_visualizer

A real-time audio visualizer for Windows, written in Python. It captures whatever your PC is playing (or your microphone), runs a Fourier transform on it, splits the result into frequency bands from bass to treble, and draws them with Pygame. It includes beat detection, a glow effect and automatic gain.

## Setup

Requires Windows and Python 3.

```
py -m pip install -r requirements.txt
py main.py
```

Then play some music.

```
py main.py --mic                          # use the microphone instead
py main.py --bars 96 --palette synthwave  # pick a starting bar count and palette
```

## Controls

| Key | Action |
| --- | --- |
| `SPACE` | Cycle mode: bars, mirrored, circular, waveform |
| `C` | Cycle color palette |
| `,` `.` | Fewer / more bars (16–128) |
| `-` `=` | Less / more sensitive |
| `A` | Auto-gain on/off |
| `G` | Glow on/off |
| `B` | Beat effects on/off |
| `[` `]` | Beat detection: stricter / catch more beats |
| `T` | Motion trails on/off |
| `F` | Fullscreen |
| `H` | Hide/show the help text |
| `ESC` | Quit |

To rebind keys, edit `KEYMAP` in `visualizer/controls.py`.

## How it works

Each frame (60 per second), the data goes through these steps:

```
audio.py      system audio → rolling buffer of the newest 4096 samples
analysis.py   Hann window → FFT → 16–128 log-spaced bands in dB
gain.py       picks the dB level that counts as an empty bar (auto or manual)
analysis.py   dB → 0–1 bar heights, smoothed so bars rise fast and fall gently
beat.py       bass energy (40–140 Hz) jumps above its 1-second average → beat
renderers.py  draws the current mode, then glow and a beat flash on top
```

| File | What's in it |
| --- | --- |
| `main.py` | Command-line options; starts audio and the app |
| `visualizer/app.py` | The main loop and keyboard actions |
| `visualizer/audio.py` | WASAPI loopback/mic capture into a thread-safe buffer |
| `visualizer/analysis.py` | FFT, frequency bands, bar smoothing |
| `visualizer/gain.py` | Auto-gain and manual sensitivity |
| `visualizer/beat.py` | Kick-drum beat detection |
| `visualizer/renderers.py` | One drawing function per mode, plus glow and flash |
| `visualizer/palettes.py` | Color palettes |
| `visualizer/hud.py` | On-screen status text and beat light |
| `visualizer/controls.py` | Key bindings |
| `visualizer/config.py` | Every tunable number |

### Customizing

- **New palette:** add a list of RGB colors to `PALETTES` in `palettes.py`. It joins the `C` rotation automatically.
- **New display mode:** write a `draw_<name>(surface, frame)` function in `renderers.py`, add it to `RENDERERS`, and add the name to `MODES` in `config.py`.
- **Tuning:** smoothing speed, glow strength, beat sensitivity, frequency range and more are all in `config.py`.

## Tests

The signal-processing code is tested with synthetic audio (a 120 BPM drum pattern played loud and quiet, plus pure tones and silence). The tests only need numpy, so they run anywhere:

```
py -m pip install pytest
py -m pytest
```
