"""Audio capture: grabs what your PC is playing (or the mic) into a rolling buffer.

The audio driver calls us on its own thread every few milliseconds with new
samples. We mix them to mono and keep only the newest FFT_SIZE of them, so
the render loop can grab a snapshot whenever it draws a frame.
"""
import threading
import time

import numpy as np

from . import config


class AudioBuffer:
    """Thread-safe rolling buffer of the most recent mono samples."""

    def __init__(self, size=config.FFT_SIZE):
        self._buf = np.zeros(size, dtype=np.float32)
        self._lock = threading.Lock()
        self._last_write = 0.0

    def write(self, data):
        """Append new samples, dropping the oldest ones (called from the audio thread)."""
        n = len(data)
        with self._lock:
            if n >= len(self._buf):
                self._buf[:] = data[-len(self._buf):]
            else:
                self._buf[:-n] = self._buf[n:]
                self._buf[-n:] = data
            self._last_write = time.perf_counter()

    def read(self):
        """Return a copy of the newest samples (called from the render loop)."""
        with self._lock:
            # Windows stops sending loopback audio when nothing is playing, so an
            # old buffer means silence; clear it instead of freezing the display.
            if time.perf_counter() - self._last_write > config.STALE_AFTER:
                self._buf[:] = 0.0
            return self._buf.copy()


class AudioCapture:
    """Opens a WASAPI stream into an AudioBuffer. Use it as a context manager:

        with AudioCapture(use_mic=False) as audio:
            samples = audio.buffer.read()
    """

    def __init__(self, use_mic=False):
        try:
            import pyaudiowpatch as pyaudio   # Windows-only fork of PyAudio with loopback support
        except ImportError as e:
            raise RuntimeError("pyaudiowpatch is not installed (py -m pip install pyaudiowpatch)") from e
        self._pyaudio = pyaudio
        self._pa = pyaudio.PyAudio()
        self.buffer = AudioBuffer()
        try:
            device = self._pa.get_default_input_device_info() if use_mic else self._find_loopback()
            self.device_name = device["name"]
            self.rate = int(device["defaultSampleRate"])
            self._channels = max(1, int(device["maxInputChannels"]))
            self._stream = self._pa.open(
                format=pyaudio.paFloat32,
                channels=self._channels,
                rate=self.rate,
                input=True,
                input_device_index=device["index"],
                frames_per_buffer=config.CALLBACK_FRAMES,
                stream_callback=self._on_audio,
            )
        except Exception:
            self._pa.terminate()
            raise

    def _find_loopback(self):
        """Find the 'loopback' copy of the default speakers, i.e. what you hear."""
        wasapi = self._pa.get_host_api_info_by_type(self._pyaudio.paWASAPI)
        speakers = self._pa.get_device_info_by_index(wasapi["defaultOutputDevice"])
        if speakers.get("isLoopbackDevice"):
            return speakers
        for dev in self._pa.get_loopback_device_info_generator():
            if speakers["name"] in dev["name"]:
                return dev
        raise RuntimeError(f"No loopback device found for '{speakers['name']}'.")

    def _on_audio(self, in_data, frame_count, time_info, status):
        samples = np.frombuffer(in_data, dtype=np.float32)
        if self._channels > 1:
            samples = samples.reshape(-1, self._channels).mean(axis=1)   # mix to mono
        self.buffer.write(samples)
        return (None, self._pyaudio.paContinue)

    def close(self):
        self._stream.stop_stream()
        self._stream.close()
        self._pa.terminate()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
