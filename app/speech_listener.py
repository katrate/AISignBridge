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


# ── Writable model storage (not the read-only MEIPASS temp dir) ──
def _model_dir():
    """Return a writable path for storing downloaded models.
    PyInstaller: next to the EXE.
    Nuitka: use app data dir (temp dir is not persistent in onefile mode).
    Source: project root."""
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(os.path.dirname(sys.executable), "models")
        if sys.platform == 'win32':
            base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        elif sys.platform == 'darwin':
            base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
        else:
            base = os.path.expanduser('~')
        return os.path.join(base, 'AI-Sign-Bridge', 'models')
    return resource_path("models")


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
    model_ready = pyqtSignal(bool)     # Emits True when model loaded, False on failure

    VOSK_MODEL_PATH = os.path.join(_model_dir(), "vosk-model")
    SAMPLE_RATE = 16000
    CHUNK = 4096

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self._muted = False
        self._vosk_model = None
        self._queue = queue.Queue()
        # Model loading deferred to run() for boot speed

    def set_muted(self, muted: bool):
        """Mute or unmute the microphone. When muted, audio is drained
        from the queue but NOT sent to Vosk for recognition."""
        self._muted = muted
        status = "MUTED" if muted else "UNMUTED"
        print(f"[SpeechListener] Mic {status}")

    VOSK_DOWNLOAD_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    VOSK_EXTRACTED_DIR = "vosk-model-small-en-us-0.15"

    def _ensure_model(self):
        """Ensure the Vosk model exists locally, downloading if needed.
        Returns True if the model is ready, False otherwise."""
        if os.path.exists(self.VOSK_MODEL_PATH):
            return True
        print(f"[SpeechListener] Vosk model not found at '{self.VOSK_MODEL_PATH}'.")
        self.status_message.emit("Downloading Vosk speech model (~128 MB)…")
        self._download_model()
        if not os.path.exists(self.VOSK_MODEL_PATH):
            print("[SpeechListener] Model download failed. Speech→Sign disabled.")
            self.status_message.emit("Vosk model download failed. Speech→Sign disabled.")
            return False
        return True

    def _download_model(self):
        """Download and extract the Vosk model on first run with progress."""
        models_dir = os.path.dirname(self.VOSK_MODEL_PATH)
        os.makedirs(models_dir, exist_ok=True)
        zip_path = os.path.join(models_dir, "vosk-model.zip")

        try:
            self.status_message.emit("MODAL_DOWNLOAD:Downloading Vosk speech model (~40 MB)…")
            print("[SpeechListener] Downloading Vosk model (~40MB)...")
            print("  This happens once on first launch.")

            req = urllib.request.Request(self.VOSK_DOWNLOAD_URL, method='GET')
            with urllib.request.urlopen(req) as resp:
                total = int(resp.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 65536
                with open(zip_path, 'wb') as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = int(downloaded * 100 / total)
                            self.status_message.emit(f"MODAL_PROGRESS:{pct}")

            self.status_message.emit("MODAL_EXTRACT:Extracting Vosk model…")

            print("[SpeechListener] Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(models_dir)

            extracted = os.path.join(models_dir, self.VOSK_EXTRACTED_DIR)
            if os.path.exists(extracted):
                os.rename(extracted, self.VOSK_MODEL_PATH)

            os.remove(zip_path)
            print("[SpeechListener] Vosk model ready.")
            self.status_message.emit("Vosk model downloaded. Loading…")
        except Exception as e:
            print(f"[SpeechListener] Download failed: {e}")
            self.status_message.emit(f"MODAL_FAIL:Vosk download failed: {e}")
            if os.path.exists(zip_path):
                os.remove(zip_path)

    def _load_model(self):
        """Load or auto-download the Vosk speech recognition model."""
        if not self._ensure_model():
            return
        try:
            import vosk
            self._vosk_model = vosk.Model(self.VOSK_MODEL_PATH)
            print("[SpeechListener] Vosk model loaded.")
            self.status_message.emit("Vosk model loaded. Speech→Sign ready.")
        except Exception as e:
            print(f"[SpeechListener] Failed to load Vosk: {e}")
            self.status_message.emit(f"Failed to load Vosk model: {e}")

    def _audio_callback(self, indata, frames, time, status):
        """Called by sounddevice for each audio chunk."""
        if status:
            print(f"[SpeechListener] Audio status: {status}")
        self._queue.put(indata.copy())

    def run(self):
        self._load_model()
        if self._vosk_model is None:
            print("[SpeechListener] No Vosk model loaded. Speech→Sign pipeline disabled.")
            self.status_message.emit("Speech recognition unavailable (no model).")
            self.model_ready.emit(False)
            return
        self.model_ready.emit(True)

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
