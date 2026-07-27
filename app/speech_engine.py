"""
app/speech_engine.py
=====================
Thin wrapper around pyttsx3 for offline text-to-speech.
Uses a single background worker thread with a queue to avoid
pyttsx3 engine state corruption from repeated runAndWait() calls.

Emits Qt signals so the UI can show a speaking indicator.
"""

import pyttsx3
import queue
import threading
import time

from PyQt6.QtCore import QObject, pyqtSignal


class SpeechEngine(QObject):
    # Emitted when the engine starts speaking a word
    speaking_started = pyqtSignal(str)  # the word being spoken
    # Emitted when the engine finishes speaking
    speaking_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine = pyttsx3.init()
        self._engine.setProperty('rate', 145)   # Speaking speed
        self._engine.setProperty('volume', 1.0) # Max volume

        # Try to set a clearer voice
        voices = self._engine.getProperty('voices')
        for v in voices:
            if 'zira' in v.name.lower() or 'david' in v.name.lower():
                self._engine.setProperty('voice', v.id)
                break

        # Use a single worker thread that keeps the engine's event loop
        # alive continuously.  DO NOT call runAndWait() — it internally
        # calls startLoop() + endLoop() each time, and on Windows SAPI5
        # the engine silently stops producing audio after the first
        # runAndWait() call.  Instead, start the loop once at thread
        # start and pump it with iterate() while checking isBusy().
        self._queue: queue.Queue = queue.Queue()
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        """Keep the pyttsx3 event loop alive forever, speaking queued text."""
        self._engine.startLoop(False)
        try:
            while self._running:
                # Non-blocking check for new speech requests
                try:
                    text = self._queue.get(timeout=0.05)
                except queue.Empty:
                    self._engine.iterate()
                    continue

                if text is None:  # Sentinel to shut down
                    break

                self.speaking_started.emit(text)
                self._engine.say(text)

                # Pump the event loop until the utterance completes.
                # isBusy() returns False only when all queued speech
                # has finished playing.
                while True:
                    self._engine.iterate()
                    if not self._engine.isBusy():
                        break
                    if not self._running:  # Allow abort mid-speech
                        break
                    time.sleep(0.05)

                self.speaking_finished.emit()
        finally:
            self._engine.endLoop()

    def speak(self, text: str):
        """Queue text for speech. Returns immediately (non-blocking)."""
        if self._running:
            self._queue.put(text)

    def stop(self):
        """Shut down the worker thread gracefully."""
        self._running = False
        self._queue.put(None)
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)
