"""Real-time audio visualizer: captures Windows audio, runs an FFT, draws it with Pygame.

Module map (data flows top to bottom):
    audio.py      capture system audio / mic into a rolling buffer
    analysis.py   FFT -> frequency bands in dB -> smoothed bar heights
    gain.py       auto/manual gain: which loudness counts as an empty vs full bar
    beat.py       kick-drum detection from bass energy
    palettes.py   color palettes
    renderers.py  one drawing function per display mode, plus glow and flash
    hud.py        on-screen status text and beat light
    controls.py   key bindings
    app.py        ties it all together in the main loop
    config.py     every tunable number
"""
