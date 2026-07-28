"""
app/speech_listener.py
=======================
Runs speech recognition in a daemon QThread using Vosk
with a RESTRICTED GRAMMAR (letters A-Z, digits 0-9).

By limiting Vosk's vocabulary to just 36 possibilities, the model only
needs to distinguish between similar-sounding letters (e.g. K vs A, M vs N)
instead of the entire English vocabulary — dramatically improving accuracy
for single-letter ASL detection.

Emits only single letters/digits (A-Z, 0-9).
"""

import json
import os
import sys
import urllib.request
import zipfile
import numpy as np
import queue

import sounddevice as sd
from PyQt6.QtCore import QThread, pyqtSignal
from app.paths import resource_path


# ── Complete ASL letter/digit vocabulary for grammar mode ──
# Vosk will ONLY recognize these exact words, nothing else.
_LETTERS = [chr(i) for i in range(ord('a'), ord('z') + 1)]
_DIGITS = [str(i) for i in range(10)]
_GRAMMAR = json.dumps(_LETTERS + _DIGITS)


# --------------------------------------------------------------------------
# SpeechListener — Vosk with grammar mode
# --------------------------------------------------------------------------

class SpeechListener(QThread):
    word_recognized = pyqtSignal(str)  # Emits recognized letter A-Z or digit 0-9
    status_message = pyqtSignal(str)   # Status updates for UI

    VOSK_MODEL_PATH = resource_path("models/vosk-model")
    SAMPLE_RATE = 16000
    CHUNK = 4096

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self._muted = False
        self._vosk_model = None
        self._queue = queue.Queue()
        self._load_model()

    def set_muted(self, muted: bool):
        """Mute or unmute the microphone. When muted, audio is drained
        from the queue but NOT sent to Vosk for recognition."""
        self._muted = muted
        status = "MUTED" if muted else "UNMUTED"
        print(f"[SpeechListener] Mic {status}")

    VOSK_DOWNLOAD_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    VOSK_EXTRACTED_DIR = "vosk-model-small-en-us-0.15"

    def _load_model(self):
        """Load or auto-download the Vosk speech recognition model."""
        if not os.path.exists(self.VOSK_MODEL_PATH):
            print(f"[SpeechListener] Vosk model not found at '{self.VOSK_MODEL_PATH}'.")
            self._download_model()
            if not os.path.exists(self.VOSK_MODEL_PATH):
                print("[SpeechListener] Model download failed. Speech→Sign disabled.")
                return

    def _download_model(self):
        """Download and extract the Vosk model on first run."""
        models_dir = os.path.dirname(self.VOSK_MODEL_PATH)
        os.makedirs(models_dir, exist_ok=True)
        zip_path = os.path.join(models_dir, "vosk-model.zip")

        try:
            print("[SpeechListener] Downloading Vosk model (~40MB)...")
            print("  This happens once on first launch.")
            urllib.request.urlretrieve(self.VOSK_DOWNLOAD_URL, zip_path)

            print("[SpeechListener] Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(models_dir)

            extracted = os.path.join(models_dir, self.VOSK_EXTRACTED_DIR)
            if os.path.exists(extracted):
                os.rename(extracted, self.VOSK_MODEL_PATH)

            os.remove(zip_path)
            print("[SpeechListener] Vosk model ready.")
        except Exception as e:
            print(f"[SpeechListener] Download failed: {e}")
            if os.path.exists(zip_path):
                os.remove(zip_path)

        try:
            import vosk
            self._vosk_model = vosk.Model(self.VOSK_MODEL_PATH)
            print("[SpeechListener] Vosk model loaded.")
        except Exception as e:
            print(f"[SpeechListener] Failed to load Vosk: {e}")

    def _audio_callback(self, indata, frames, time, status):
        """Called by sounddevice for each audio chunk."""
        if status:
            print(f"[SpeechListener] Audio status: {status}")
        self._queue.put(indata.copy())

    def run(self):
        if self._vosk_model is None:
            print("[SpeechListener] No Vosk model loaded. Speech→Sign pipeline disabled.")
            return

        self.running = True

        import vosk
        # Create recognizer with RESTRICTED GRAMMAR — only A-Z and 0-9.
        # This forces Vosk to choose from just 36 possibilities instead of
        # the entire English vocabulary, making letter detection far more accurate.
        vosk_rec = vosk.KaldiRecognizer(self._vosk_model, self.SAMPLE_RATE, _GRAMMAR)

        print(f"[SpeechListener] Listening (grammar: A-Z, 0-9)...")
        with sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            blocksize=self.CHUNK,
            dtype="float32",
            channels=1,
            callback=self._audio_callback
        ):
            while self.running:
                try:
                    chunk = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                flat = chunk.flatten()

                # ── When muted, drain audio WITHOUT feeding it to Vosk ──
                if self._muted:
                    continue

                # Feed ALL audio to Vosk continuously — it has its own VAD.
                chunk_int16 = (flat * 32767).astype(np.int16)
                chunk_bytes = chunk_int16.tobytes()

                if vosk_rec.AcceptWaveform(chunk_bytes):
                    result = json.loads(vosk_rec.Result())
                    text = result.get("text", "").strip().lower()
                    if text:
                        print(f"[SpeechListener] Vosk: '{text}'")
                        # With grammar mode, Vosk should only output single
                        # letters/digits from our grammar. Emit each one.
                        for token in text.split():
                            self.word_recognized.emit(token)

    def stop(self):
        self.running = False
        self.wait()
