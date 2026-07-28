"""
app/sign_detector.py
=====================
Runs in a QThread. Captures webcam frames, extracts MediaPipe hand landmarks,
predicts the sign using the trained model, and emits signals for the UI.
Uses the new MediaPipe Tasks API (compatible with protobuf 6+).
"""

import os
import sys
import time
import cv2
import mediapipe as mp
import numpy as np
import joblib
from collections import Counter
import traceback
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

# MediaPipe Tasks API (replaces old mp.solutions.hands)
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core import base_options

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.feature_extraction import extract_features_from_mediapipe
from app.ensemble_model import EnsembleGestureModel  # noqa: F401
from app.paths import resource_path

# Hand connections constant (21 landmarks, defined inline)
# From the MediaPipe hand model
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (0, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (0, 13), (13, 14), (14, 15), (15, 16), # Ring
    (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
    (5, 9), (9, 13), (13, 17), (0, 17),    # Palm
]


class SignDetector(QThread):
    # Signals emitted to the main UI thread
    frame_ready = pyqtSignal(QImage)          # Processed webcam frame
    prediction_ready = pyqtSignal(str, float) # (sign_label, confidence)

    MODEL_PATH_H5 = resource_path("models/gesture_model.h5")
    MODEL_PATH_PKL = resource_path("models/gesture_model.pkl")
    ENCODER_PATH = resource_path("models/label_encoder.pkl")
    NORMALIZER_PATH = resource_path("models/normalizer.pkl")
    # Smoothing constants — tuned for stability vs responsiveness
    WINDOW_SIZE = 15      # Number of recent predictions to consider
    MAJORITY_RATIO = 0.70 # Fraction of window that must agree
    MIN_CONFIDENCE = 0.40 # Average confidence must exceed this
    TOP2_GAP = 0.15       # Min gap between top-1 and top-2 probabilities

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.model = None
        self.label_encoder = None
        self.normalizer = None
        self._load_model()
        self._buffer = []        # list of (label, confidence) tuples
        self._last_spoken = None # last label that was emitted

    def _load_model(self):
        """Load TF model (.h5) first, fallback to joblib (.pkl)."""
        # Try TensorFlow model first
        try:
            import tensorflow as tf
            self.model = tf.keras.models.load_model(self.MODEL_PATH_H5)
            self.label_encoder = joblib.load(self.ENCODER_PATH)
            self.normalizer = joblib.load(self.NORMALIZER_PATH)
            print("[SignDetector] TensorFlow model loaded successfully.")
            return
        except Exception as e:
            # Reset partial loads so we don't have a model without encoder
            self.model = None
            self.label_encoder = None
            self.normalizer = None
            print(f"[SignDetector] TF load failed: {e}")

        # Fallback to joblib pickle model
        try:
            self.model = joblib.load(self.MODEL_PATH_PKL)
            self.label_encoder = joblib.load(self.ENCODER_PATH)
            # normalizer stays None (sklearn ensemble normalizes internally)
            print("[SignDetector] Pickle model loaded successfully.")
            return
        except Exception as e:
            self.model = None
            self.label_encoder = None
            print(f"[SignDetector] WARNING: No model found. Train first. ({e})")

    def run(self):
        self.running = True

        # Use the new MediaPipe Tasks API for hand landmarking
        landmarker_options = vision.HandLandmarkerOptions(
            base_options=base_options.BaseOptions(model_asset_path=resource_path("models/hand_landmarker.task")),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        landmarker = vision.HandLandmarker.create_from_options(landmarker_options)

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        self._frame_count = 0

        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            self._frame_count += 1
            do_predict = (self._frame_count % 2 == 0)

            # Convert frame for MediaPipe Tasks API
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(time.perf_counter() * 1000)

            # Detect hand landmarks using the Tasks API
            detection_result = landmarker.detect_for_video(mp_image, timestamp_ms)

            # Always draw landmarks when hands are detected (using OpenCV)
            if detection_result.hand_landmarks:
                h, w, _ = frame.shape
                for hand_landmarks in detection_result.hand_landmarks:
                    # Draw connections (lines)
                    for connection in HAND_CONNECTIONS:
                        start = hand_landmarks[connection[0]]
                        end = hand_landmarks[connection[1]]
                        cv2.line(frame,
                                 (int(start.x * w), int(start.y * h)),
                                 (int(end.x * w), int(end.y * h)),
                                 (0, 255, 0), 2)
                    # Draw landmarks (circles)
                    for lm in hand_landmarks:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

                    # Only predict on every other frame to save CPU
                    if self.model and do_predict:
                        try:
                            # Same function used to build the training data --
                            # guarantees train/inference features never drift apart.
                            features = extract_features_from_mediapipe(hand_landmarks).reshape(1, -1)

                            # Standardize if TF model (has normalizer). The sklearn
                            # ensemble model normalizes internally, so self.normalizer
                            # is None for that path and this is skipped.
                            if self.normalizer is not None:
                                features = (features - self.normalizer['mean']) / self.normalizer['std']

                            # Predict: handle both TF (.predict) and sklearn (.predict_proba)
                            if hasattr(self.model, 'predict_proba'):
                                proba = self.model.predict_proba(features)[0]
                            else:
                                proba = self.model.predict(features, verbose=0)[0]

                            pred_idx = np.argmax(proba)
                            confidence = float(proba[pred_idx])
                            label = self.label_encoder.inverse_transform([pred_idx])[0]

                            # Smoothing buffer (sliding window) — emit only when stable
                            self._buffer.append((label, confidence))
                            if len(self._buffer) > self.WINDOW_SIZE:
                                self._buffer.pop(0)

                            if len(self._buffer) == self.WINDOW_SIZE:
                                # Count label frequency in the window
                                labels_in_window = [lbl for lbl, _ in self._buffer]
                                label_counts = Counter(labels_in_window)
                                most_common_label, freq = label_counts.most_common(1)[0]

                                # 1) Majority agreement check
                                if freq >= self.WINDOW_SIZE * self.MAJORITY_RATIO:
                                    # 2) Average confidence for the majority label
                                    confs = [c for lbl, c in self._buffer if lbl == most_common_label]
                                    avg_conf = sum(confs) / len(confs)

                                    # 3) Top-2 gap check (optional — needs proba vector)
                                    #    We approximate by checking how close the runner-up is
                                    top2 = label_counts.most_common(2)
                                    gap_ok = True
                                    if len(top2) == 2:
                                        _, runner_up_count = top2[1]
                                        # Runner-up must not be within 2 frames of the leader
                                        if freq - runner_up_count < 3:
                                            gap_ok = False

                                    if gap_ok and most_common_label != self._last_spoken and avg_conf >= self.MIN_CONFIDENCE:
                                        self._last_spoken = most_common_label
                                        self.prediction_ready.emit(most_common_label, avg_conf)
                        except Exception as e:
                            print(f"[SIGNDETECTOR ERROR] {e}")
                            traceback.print_exc()
            else:
                self._buffer.clear()
                self._last_spoken = None

            # Convert frame to QImage for display
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            qt_image = QImage(rgb_frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
            self.frame_ready.emit(qt_image)

        cap.release()
        landmarker.close()

    def stop(self):
        self.running = False
        self.wait()
