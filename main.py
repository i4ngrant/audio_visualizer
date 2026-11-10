"""Start the visualizer.

    py main.py                              # visualize whatever your PC is playing
    py main.py --mic                        # use the microphone instead
    py main.py --bars 96 --palette synthwave
"""
import argparse
import sys

from visualizer import config
from visualizer.app import Visualizer
from visualizer.audio import AudioCapture
from visualizer.palettes import PALETTE_NAMES


def parse_args():
    parser = argparse.ArgumentParser(description="Real-time audio visualizer")
    parser.add_argument("--mic", action="store_true",
                        help="use the microphone instead of system audio")
    parser.add_argument("--bars", type=int, default=config.DEFAULT_BARS,
                        help=f"number of bars, {config.BAR_COUNTS[0]}-{config.BAR_COUNTS[-1]}")
    parser.add_argument("--palette", choices=PALETTE_NAMES, default="rainbow",
                        help="starting color palette")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        audio = AudioCapture(use_mic=args.mic)
    except Exception as e:
        sys.exit(f"Could not open audio device: {e}")

    print(f"Capturing from: {audio.device_name} @ {audio.rate} Hz")
    with audio:
        Visualizer(audio, num_bars=args.bars, palette=args.palette).run()


if __name__ == "__main__":
    main()
