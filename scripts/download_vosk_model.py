"""
scripts/download_vosk_model.py
===============================
Downloads the Vosk speech recognition model with dynamic graph support
(lgraph variant) and extracts it to models/vosk-model/.

This model uses a grammar (vocabulary restriction) so it only recognizes
the ASL letters A-Z and digits 0-9 — dramatically more accurate for
single-letter speech detection than free-form dictation models.

Usage:
    python scripts/download_vosk_model.py
"""

import os
import sys
import zipfile
import urllib.request
import shutil

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip"
MODEL_DIR = os.path.join("models", "vosk-model")
MODEL_FOLDER_NAME = "vosk-model-en-us-0.22-lgraph"  # Name inside the zip

def download_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size / (1024 * 1024)
    total = total_size / (1024 * 1024)
    percent = min(100, int(downloaded / total * 100)) if total > 0 else 0
    bar = "=" * (percent // 2) + "-" * (50 - percent // 2)
    sys.stdout.write(f"\r  [{bar}] {percent}% ({downloaded:.1f}/{total:.1f} MB)")
    sys.stdout.flush()

def main():
    print("=" * 60)
    print("  AI Sign Bridge — Vosk Model Downloader")
    print("=" * 60)

    # Check if already downloaded
    if os.path.exists(MODEL_DIR):
        print(f"\n[INFO] Model already exists at '{MODEL_DIR}'.")
        print("[INFO] Delete that directory and re-run to re-download.")
        return

    os.makedirs("models", exist_ok=True)

    zip_filename = f"{MODEL_FOLDER_NAME}.zip"
    zip_path = os.path.join("models", zip_filename)

    # Download
    print(f"\n[INFO] Downloading dynamic-graph Vosk model (~128 MB)...")
    print(f"  URL: {MODEL_URL}")
    print(f"  This model supports grammar mode for accurate letter detection.\n")
    try:
        urllib.request.urlretrieve(MODEL_URL, zip_path, reporthook=download_progress)
        print("\n[INFO] Download complete.")
    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        print("\n  Try downloading manually from:")
        print(f"    {MODEL_URL}")
        print(f"  Then extract the '{MODEL_FOLDER_NAME}' folder as 'models/vosk-model/'")
        sys.exit(1)

    # Extract
    print("[INFO] Extracting...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall("models")
        # Rename extracted folder to vosk-model
        extracted = os.path.join("models", MODEL_FOLDER_NAME)
        if os.path.exists(extracted):
            if os.path.exists(MODEL_DIR):
                shutil.rmtree(MODEL_DIR)
            os.rename(extracted, MODEL_DIR)
        print(f"[INFO] Extracted to '{MODEL_DIR}'.")
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        print("\n  Try extracting manually:")
        print(f"    1. Extract '{zip_path}' into the 'models/' folder")
        print(f"    2. Rename '{MODEL_FOLDER_NAME}' to 'vosk-model'")
        sys.exit(1)
    finally:
        # Clean up zip
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print("[INFO] Cleaned up zip file.")

    print("\n[DONE] Dynamic-graph Vosk model ready! Run 'python app/main.py' to use speech -> sign.")
    print("=" * 60)


if __name__ == "__main__":
    main()
