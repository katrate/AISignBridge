"""
scripts/collect_voice_data.py
==============================
Records your voice saying each ASL letter (A-Z) and digit (0-9) so the app
can learn YOUR specific pronunciation. Similar-sounding letters like K/A
and I/E become easy to distinguish because the model trains on how YOU
actually say them.

Usage:
    python scripts/collect_voice_data.py

Instructions:
    - Say the displayed letter clearly when the recording starts
    - Speak in a normal voice, about 30cm from your mic
    - Each letter records 5 samples by default
    - Total time: ~10 minutes for 36 letters x 5 samples
"""

import os
import sys
import time
import argparse
import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000
DURATION = 1.5          # seconds per recording
SAMPLES_PER_LETTER = 5  # how many times to record each letter

# Letters to record: A-Z and 0-9
LABELS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + list("0123456789")

OUTPUT_DIR = os.path.join("data", "voice_samples")


def record_audio(duration: float, samplerate: int) -> np.ndarray:
    """Record audio from the default microphone."""
    print(f"\n  Recording for {duration:.1f}s ... ", end="", flush=True)
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate,
                   channels=1, dtype="float32")
    sd.wait()
    print("Done!")
    return audio.flatten()


def main():
    parser = argparse.ArgumentParser(
        description="Record your voice for custom speech-to-sign training."
    )
    parser.add_argument("--samples", type=int, default=SAMPLES_PER_LETTER,
                        help=f"Samples per letter (default: {SAMPLES_PER_LETTER})")
    parser.add_argument("--duration", type=float, default=DURATION,
                        help=f"Seconds per recording (default: {DURATION})")
    parser.add_argument("--labels", type=str, nargs="*",
                        help="Specific labels to record (default: all A-Z, 0-9)")
    args = parser.parse_args()

    labels = args.labels if args.labels else LABELS

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("  AI Sign Bridge — Voice Data Collector")
    print("=" * 60)
    print(f"\n  Recording {len(labels)} labels × {args.samples} samples")
    print(f"  Duration: {args.duration}s each")
    print(f"  Output: {OUTPUT_DIR}/")
    print("\n  When the countdown starts, say the letter clearly.")
    print("  Press Ctrl+C anytime to stop.\n")

    total = 0
    try:
        for label in labels:
            print(f"\n─── [{label}] ────────────────────────────────")
            for i in range(1, args.samples + 1):
                # Countdown
                print(f"\n  Sample {i}/{args.samples} — say \"{label}\" in:")
                for c in range(3, 0, -1):
                    print(f"    {c}...")
                    time.sleep(0.8)

                # Record
                audio = record_audio(args.duration, SAMPLE_RATE)

                # Save as .npy file (numpy array)
                fname = f"{label}_{i:02d}.npy"
                fpath = os.path.join(OUTPUT_DIR, fname)
                np.save(fpath, audio)
                total += 1
                print(f"  Saved: {fname}")

                # Brief pause between samples
                time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n  Interrupted by user.")

    print(f"\n{'=' * 60}")
    print(f"  Done! {total} samples saved to '{OUTPUT_DIR}/'")
    print(f"\n  NEXT: Run:  python scripts/train_voice_classifier.py")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
