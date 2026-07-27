"""
app/speech_listener.py
=======================
Runs speech recognition in a daemon QThread.
Supports TWO backends:
  1. Custom voice classifier (trained on YOUR voice) — preferred
  2. Vosk (generic English model) — fallback

Emits a signal with the recognized letter when speech is detected.
"""

import json
import os
import sys
import time
from typing import Optional
import numpy as np
import queue

import sounddevice as sd
from PyQt6.QtCore import QThread, pyqtSignal

from app.voice_features import compute_mfcc_vector




# --------------------------------------------------------------------------
# SpeechListener
# --------------------------------------------------------------------------

class SpeechListener(QThread):
    word_recognized = pyqtSignal(str)  # Emits recognized word/letter

    VOSK_MODEL_PATH = "models/vosk-model"
    CUSTOM_MODEL_PATH = "models/voice_classifier.pkl"
    CUSTOM_ENCODER_PATH = "models/voice_label_encoder.pkl"
    SAMPLE_RATE = 16000
    CHUNK = 4096
    RECORD_SECONDS = 1.5   # Length of audio clip for custom classifier
    # Voice Activity Detection thresholds
    VAD_ENERGY_THRESHOLD = 0.015  # Min RMS energy to consider as speech
    VAD_MIN_SPEECH_FRACTION = 0.15  # At least 15% of window must have speech
    MIN_CONFIDENCE = 0.3  # Min classifier confidence to emit

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self._vosk_model = None
        self._custom_model = None
        self._custom_encoder = None
        self._queue = queue.Queue()
        self._last_custom_letter = None  # Avoid re-emitting same letter
        self._load_models()

    def _load_models(self):
        """Load custom voice classifier first, then Vosk as fallback."""
        # Try custom voice classifier (trained on user's voice)
        try:
            import joblib
            if os.path.exists(self.CUSTOM_MODEL_PATH) and os.path.exists(self.CUSTOM_ENCODER_PATH):
                self._custom_model = joblib.load(self.CUSTOM_MODEL_PATH)
                self._custom_encoder = joblib.load(self.CUSTOM_ENCODER_PATH)
                print(f"[SpeechListener] Custom voice classifier loaded"
                      f" ({len(self._custom_encoder.classes_)} classes).")
            else:
                print(f"[SpeechListener] No custom model at '{self.CUSTOM_MODEL_PATH}'.")
        except Exception as e:
            print(f"[SpeechListener] Failed to load custom model: {e}")

        # Fallback: try Vosk
        if os.path.exists(self.VOSK_MODEL_PATH):
            try:
                import vosk
                self._vosk_model = vosk.Model(self.VOSK_MODEL_PATH)
                print("[SpeechListener] Vosk model loaded (fallback).")
            except Exception as e:
                print(f"[SpeechListener] Failed to load Vosk: {e}")
        else:
            print(f"[SpeechListener] Vosk model not found at '{self.VOSK_MODEL_PATH}'.")

        if not self._custom_model and not self._vosk_model:
            print("[SpeechListener] WARNING: No speech models loaded.")
            print("  Train a custom model:  python scripts/collect_voice_data.py")
            print("                        python scripts/train_voice_classifier.py")
            print("  Or download Vosk:      python scripts/download_vosk_model.py")

    @staticmethod
    def _rms_energy(audio: np.ndarray) -> float:
        """Compute RMS energy of an audio segment (0.0 = silence)."""
        return float(np.sqrt(np.mean(audio ** 2)))

    @staticmethod
    def _has_voice(audio: np.ndarray) -> bool:
        """Check if audio contains actual speech using energy-based VAD."""
        energy = SpeechListener._rms_energy(audio)
        return energy > SpeechListener.VAD_ENERGY_THRESHOLD

    def _predict_custom(self, audio: np.ndarray) -> Optional[str]:
        """Use the custom voice classifier to predict the letter.
        Returns None if silent, low confidence, or same as last emission.
        """
        if self._custom_model is None or self._custom_encoder is None:
            return None

        # Voice Activity Detection: skip if too quiet
        if not self._has_voice(audio):
            return None

        try:
            feats = compute_mfcc_vector(audio).reshape(1, -1)

            # Check confidence if model supports predict_proba
            confidence = None
            if hasattr(self._custom_model, 'predict_proba'):
                proba = self._custom_model.predict_proba(feats)[0]
                pred_idx = int(np.argmax(proba))
                confidence = float(proba[pred_idx])
                if confidence < self.MIN_CONFIDENCE:
                    return None
            else:
                pred_idx = int(self._custom_model.predict(feats)[0])

            letter = self._custom_encoder.inverse_transform([pred_idx])[0]

            # Avoid re-emitting the same letter repeatedly
            if letter == self._last_custom_letter:
                return None
            self._last_custom_letter = letter

            return letter
        except Exception as e:
            print(f"[SpeechListener] Custom prediction error: {e}")
            return None

    def _audio_callback(self, indata, frames, time, status):
        """Called by sounddevice for each audio chunk."""
        if status:
            print(f"[SpeechListener] Audio status: {status}")
        self._queue.put(indata.copy())

    def run(self):
        if not self._custom_model and not self._vosk_model:
            print("[SpeechListener] No models loaded. Speech→Sign pipeline disabled.")
            return

        self.running = True

        # Set up Vosk if available
        if self._vosk_model:
            import vosk
            vosk_rec = vosk.KaldiRecognizer(self._vosk_model, self.SAMPLE_RATE)
        else:
            vosk_rec = None

        print("[SpeechListener] Listening...")
        with sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            blocksize=self.CHUNK,
            dtype="float32",
            channels=1,
            callback=self._audio_callback
        ):
            # Buffer for custom classifier (with VAD gating)
            custom_buffer = []
            custom_buffer_samples = 0
            custom_silent_chunks = 0  # Consecutive silent chunks
            custom_samples_needed = int(self.SAMPLE_RATE * self.RECORD_SECONDS)
            max_silent_chunks = int(self.SAMPLE_RATE / self.CHUNK * 0.3)  # 0.3s silence = reset

            while self.running:
                try:
                    chunk = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                # Flatten once for both paths
                flat = chunk.flatten()
                energy = self._rms_energy(flat)

                # --- CUSTOM CLASSIFIER PATH (with VAD) ---
                if self._custom_model:

                    if energy > self.VAD_ENERGY_THRESHOLD:
                        # Voice detected — add to buffer
                        custom_buffer.append(flat)
                        custom_buffer_samples += len(flat)
                        custom_silent_chunks = 0
                    else:
                        # Silence — don't add to buffer (let it drain via silence reset)
                        custom_silent_chunks += 1
                        # Reset if too much consecutive silence (user stopped speaking)
                        if custom_silent_chunks > max_silent_chunks:
                            custom_buffer = []
                            custom_buffer_samples = 0
                            custom_silent_chunks = 0
                            self._last_custom_letter = None
                            continue

                    if custom_buffer_samples >= custom_samples_needed:
                        clip = np.concatenate(custom_buffer)[:custom_samples_needed]
                        custom_buffer = []
                        custom_buffer_samples = 0
                        custom_silent_chunks = 0
                        letter = self._predict_custom(clip)
                        if letter is not None and len(letter) == 1:
                            print(f"[SpeechListener] Custom voice → '{letter}'")
                            self.word_recognized.emit(letter)

                # --- VOSK PATH (fallback, VAD-gated) ---
                if self._vosk_model and vosk_rec and energy > self.VAD_ENERGY_THRESHOLD:
                    # Convert float32 to int16 bytes for Vosk
                    chunk_int16 = (flat * 32767).astype(np.int16)
                    if vosk_rec.AcceptWaveform(chunk_int16.tobytes()):
                        result = json.loads(vosk_rec.Result())
                        text = result.get("text", "").strip().lower()
                        if text:
                            print(f"[SpeechListener] Vosk: '{text}'")
                            for word in text.split():
                                self.word_recognized.emit(word)

    def stop(self):
        self.running = False
        self.wait()
