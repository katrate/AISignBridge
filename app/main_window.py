"""
app/main_window.py
==================
Main PyQt6 window for AI Sign Bridge.
Refined modern UI with glassmorphism cards, smooth animations,
and professional micro-interactions.

Layout: Webcam feed (left) | Sign output + GIF (right) | Status bar (bottom)
"""

import os
import math
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStatusBar, QSizePolicy,
    QGraphicsOpacityEffect, QProgressDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import (
    QPixmap, QFont, QMovie, QColor, QImage, QIcon,
    QPainter, QLinearGradient, QPen, QPainterPath,
    QBrush, QRadialGradient
)

from app.sign_detector import SignDetector
from app.speech_engine import SpeechEngine
from app.speech_listener import SpeechListener
from app.paths import resource_path


# ─── Elegant Dark Stylesheet ────────────────────────────────────────────
# Design: Deep charcoal background with subtle blue-teal accent.
# Cards use a glassmorphism-inspired semi-transparent fill with thin borders.
# No heavy gradients or purple tones — aims for a clean, professional tool feel.

STYLESHEET = """
QMainWindow, QWidget {
    background-color: #080810;
    color: #ededf5;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', 'SF Pro Display', sans-serif;
}

/* ── Cards ── */
QFrame#card {
    background-color: rgba(16, 16, 32, 0.85);
    border: 1px solid #1e1e38;
    border-radius: 16px;
}
QFrame#card:hover {
    border-color: #282848;
}

QFrame#card_accent {
    background-color: rgba(16, 16, 32, 0.85);
    border: 1px solid #1e1e38;
    border-radius: 16px;
    border-top: 2px solid qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #06b6d4, stop:0.5 #3b82f6, stop:1 #6366f1);
}

/* ── Section Titles ── */
QLabel#section_title {
    color: #585880;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    padding: 0px;
}

/* ── Webcam ── */
QLabel#webcam_label {
    background-color: #0a0a16;
    border-radius: 12px;
    border: 1px solid #181830;
}

/* ── Prediction Display ── */
QLabel#prediction_text {
    color: #ededf5;
    font-size: 60px;
    font-weight: 700;
    letter-spacing: -2px;
}
QLabel#prediction_text[class="detected"] {
    color: #22c55e;
}

/* ── Sign Image Display ── */
QLabel#sign_gif_label {
    background-color: #0a0a16;
    border-radius: 12px;
    border: 1px solid #181830;
    color: #383858;
    font-size: 13px;
}

/* ── Transcript ── */
QLabel#transcript_label {
    color: #b0b0d0;
    font-size: 15px;
    font-weight: 500;
    padding: 6px 12px;
    background-color: #0e0e20;
    border-radius: 8px;
    border: 1px solid #1a1a34;
}

/* ── History Items ── */
QLabel#history_item {
    color: #505070;
    font-size: 13px;
    padding: 2px 0px;
    letter-spacing: 0.3px;
}

QLabel#history_badge {
    background-color: #141428;
    color: #686890;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 12px;
    font-weight: 600;
    border: 1px solid #1e1e38;
}

/* ── Buttons ── */
QPushButton#start_btn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #06b6d4, stop:0.5 #3b82f6, stop:1 #6366f1);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 28px;
    font-size: 14px;
    font-weight: 700;
    min-width: 120px;
}
QPushButton#start_btn:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #0891b2, stop:0.5 #2563eb, stop:1 #4f46e5);
}
QPushButton#start_btn:pressed {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #065a75, stop:0.5 #1d4ed8, stop:1 #4338ca);
}
QPushButton#start_btn:disabled {
    background: #1a1a34;
    color: #484868;
}

QPushButton#stop_btn {
    background: transparent;
    color: #f87171;
    border: 1.5px solid #f87171;
    border-radius: 10px;
    padding: 10px 28px;
    font-size: 14px;
    font-weight: 700;
    min-width: 120px;
}
QPushButton#stop_btn:hover {
    background: rgba(248, 113, 113, 0.1);
    border-color: #ef4444;
    color: #ef4444;
}
QPushButton#stop_btn:pressed {
    background: rgba(248, 113, 113, 0.2);
}
QPushButton#stop_btn:disabled {
    background: transparent;
    color: #383858;
    border-color: #282848;
}

/* ── Mic Toggle Button ── */
QPushButton#mic_toggle_btn {
    background: transparent;
    color: #22c55e;
    border: 1.5px solid #22c55e;
    border-radius: 10px;
    padding: 10px 18px;
    font-size: 14px;
    font-weight: 700;
    min-width: 90px;
}
QPushButton#mic_toggle_btn:hover {
    background: rgba(34, 197, 94, 0.1);
}
QPushButton#mic_toggle_btn:pressed {
    background: rgba(34, 197, 94, 0.2);
}
QPushButton#mic_toggle_btn[muted="true"] {
    color: #f87171;
    border-color: #f87171;
}
QPushButton#mic_toggle_btn[muted="true"]:hover {
    background: rgba(248, 113, 113, 0.1);
}
QPushButton#mic_toggle_btn:disabled {
    color: #383858;
    border-color: #282848;
}

/* ── Status Bar ── */
QStatusBar {
    background-color: #080810;
    color: #484870;
    border-top: 1px solid #141428;
    font-size: 12px;
    padding: 4px 12px;
}

/* ── Live Badge ── */
QLabel#live_badge {
    border-radius: 8px;
    padding: 2px 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

/* ── Header ── */
QLabel#header_title {
    color: #ededf5;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.3px;
}

QLabel#header_subtitle {
    color: #484868;
    font-size: 12px;
    font-weight: 500;
}

/* ── Speaking Indicator ── */
QLabel#speaking_indicator {
    color: #06b6d4;
    font-size: 14px;
    font-weight: 600;
    padding: 2px;
}

/* ── FPS Counter ── */
QLabel#fps_label {
    color: #383858;
    font-size: 11px;
    font-weight: 600;
    font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
}

/* ── Mic Icon ── */
QLabel#mic_icon {
    font-size: 16px;
    padding: 4px;
}

/* ── Divider ── */
QFrame#divider {
    color: #181830;
    max-height: 1px;
}

/* ── Tooltip ── */
QToolTip {
    background-color: #181830;
    color: #b0b0d0;
    border: 1px solid #282848;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}

/* ── Scrollbar ── */
QScrollBar:vertical {
    background: #0e0e20;
    width: 6px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #282848;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #383868;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


class MainWindow(QMainWindow):
    SIGNS_DIR = resource_path("signs")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Sign Bridge — Real-Time ASL Translator")
        self.setMinimumSize(1150, 720)
        self.setStyleSheet(STYLESHEET)

        # Set window icon
        icon_path = resource_path("logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._detector = None
        self._listener = None
        self._speech_engine = SpeechEngine()
        self._history = []
        self._current_movie = None

        # ── Animation timers ──
        self._speaking_anim_frame = 0
        self._speaking_timer = QTimer(self)
        self._speaking_timer.setInterval(100)
        self._speaking_timer.timeout.connect(self._tick_speaking_animation)

        self._pulse_frame = 0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(800)
        self._pulse_timer.timeout.connect(self._tick_pulse)

        self._glow_effect = QGraphicsOpacityEffect()
        self._glow_effect.setOpacity(1.0)
        self._glow_direction = 1
        self._glow_timer = QTimer(self)
        self._glow_timer.setInterval(30)
        self._glow_timer.timeout.connect(self._tick_detection_glow)

        # ── Speaking engine signals ──
        # ── Mic mute state ──
        self._mic_muted = True  # Start muted by default

        # ── Speaking engine signals ──
        self._speech_engine.speaking_started.connect(self._on_speaking_started)
        self._speech_engine.speaking_finished.connect(self._on_speaking_finished)

        # Build the UI
        self._build_ui()

        # Status
        self._status("·  Ready. Press Start to begin.")

    # ══════════════════════════════════════════════════════════════════
    #  UI BUILD
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(14)

        # ── Header ──
        root.addLayout(self._make_header())

        # ── Main Content ──
        content = QHBoxLayout()
        content.setSpacing(16)
        content.addWidget(self._make_left_card(), 3)
        content.addWidget(self._make_right_panel(), 2)
        root.addLayout(content, 1)

        # ── Controls ──
        root.addLayout(self._make_controls())

        # ── Status Bar ──
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _make_header(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Brand
        brand = QHBoxLayout()
        brand.setSpacing(8)

        icon = QLabel("🤟")
        icon.setStyleSheet("font-size: 24px;")

        title = QLabel("AI Sign Bridge")
        title.setObjectName("header_title")

        subtitle = QLabel("Real-Time ASL Translator")
        subtitle.setObjectName("header_subtitle")

        version = QLabel("v1.0")
        version.setStyleSheet("color: #282850; font-size: 10px; font-weight: 600;")

        brand.addWidget(icon)
        brand.addWidget(title)
        brand.addWidget(subtitle)
        brand.addSpacing(4)
        brand.addWidget(version)
        layout.addLayout(brand)

        layout.addStretch()

        # Right side: status indicators
        status_area = QHBoxLayout()
        status_area.setSpacing(12)

        # Mic status indicator
        self.mic_icon = QLabel("🎤")
        self.mic_icon.setObjectName("mic_icon")
        self.mic_icon.setStyleSheet("font-size: 15px; opacity: 0.5;")

        # Live badge
        self.live_badge = QLabel("⏻  OFFLINE")
        self.live_badge.setObjectName("live_badge")
        self._set_live(False)

        status_area.addWidget(self.mic_icon)
        status_area.addWidget(self.live_badge)
        layout.addLayout(status_area)

        return layout

    def _make_left_card(self):
        """Webcam feed card."""
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header row
        header_row = QHBoxLayout()
        section_lbl = QLabel("LIVE CAMERA")
        section_lbl.setObjectName("section_title")

        self.fps_label = QLabel("— fps")
        self.fps_label.setObjectName("fps_label")

        header_row.addWidget(section_lbl)
        header_row.addStretch()
        header_row.addWidget(self.fps_label)
        layout.addLayout(header_row)

        # Webcam
        self.webcam_label = QLabel("Camera feed will appear here")
        self.webcam_label.setObjectName("webcam_label")
        self.webcam_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.webcam_label.setMinimumSize(480, 360)
        self.webcam_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        layout.addWidget(self.webcam_label, 1)

        # Camera info bar
        info_row = QHBoxLayout()
        self.cam_status = QLabel("●  Camera ready")
        self.cam_status.setStyleSheet("color: #22c55e; font-size: 11px; font-weight: 500;")
        info_row.addWidget(self.cam_status)
        info_row.addStretch()

        self.detection_status = QLabel("")
        self.detection_status.setStyleSheet("color: #484868; font-size: 11px;")
        info_row.addWidget(self.detection_status)
        layout.addLayout(info_row)

        return card

    def _make_right_panel(self):
        """Right panel with sign detection, speech->sign, transcript, and history."""
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(0)

        # ═══════════════════════════════════════════════
        # SECTION 1: Detected Sign (from camera)
        # ═══════════════════════════════════════════════
        detected_lbl = QLabel("DETECTED SIGN")
        detected_lbl.setObjectName("section_title")
        layout.addWidget(detected_lbl)
        layout.addSpacing(6)

        self.prediction_text = QLabel("—")
        self.prediction_text.setObjectName("prediction_text")
        self.prediction_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prediction_text.setWordWrap(True)
        self.prediction_text.setFixedHeight(76)
        layout.addWidget(self.prediction_text)
        layout.addSpacing(12)

        # Speaking indicator
        self.speaking_indicator = QLabel()
        self.speaking_indicator.setObjectName("speaking_indicator")
        self.speaking_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speaking_indicator.setFixedHeight(26)
        self.speaking_indicator.hide()
        layout.addWidget(self.speaking_indicator)

        # ── Divider ──
        divider1 = QFrame()
        divider1.setObjectName("divider")
        divider1.setFrameShape(QFrame.Shape.HLine)
        layout.addSpacing(10)
        layout.addWidget(divider1)
        layout.addSpacing(12)

        # ═══════════════════════════════════════════════
        # SECTION 2: Speech → Sign
        # ═══════════════════════════════════════════════
        speech_lbl = QLabel("SPEECH → SIGN")
        speech_lbl.setObjectName("section_title")
        layout.addWidget(speech_lbl)
        layout.addSpacing(8)

        self.sign_gif_label = QLabel("Speak a word\nto see its sign")
        self.sign_gif_label.setObjectName("sign_gif_label")
        self.sign_gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sign_gif_label.setMinimumHeight(160)
        layout.addWidget(self.sign_gif_label, 1)
        layout.addSpacing(12)

        # ── Divider ──
        divider2 = QFrame()
        divider2.setObjectName("divider")
        divider2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider2)
        layout.addSpacing(10)

        # ═══════════════════════════════════════════════
        # SECTION 3: Transcript
        # ═══════════════════════════════════════════════
        transcript_header = QHBoxLayout()
        transcript_lbl = QLabel("MIC TRANSCRIPT")
        transcript_lbl.setObjectName("section_title")

        self.mic_status_dot = QLabel("⚫")
        self.mic_status_dot.setStyleSheet("color: #282848; font-size: 8px;")
        transcript_header.addWidget(transcript_lbl)
        transcript_header.addStretch()
        transcript_header.addWidget(self.mic_status_dot)
        layout.addLayout(transcript_header)
        layout.addSpacing(6)

        self.transcript_label = QLabel("—")
        self.transcript_label.setObjectName("transcript_label")
        self.transcript_label.setWordWrap(True)
        layout.addWidget(self.transcript_label)
        layout.addSpacing(14)

        # ═══════════════════════════════════════════════
        # SECTION 4: History
        # ═══════════════════════════════════════════════
        history_header = QHBoxLayout()
        history_lbl = QLabel("HISTORY")
        history_lbl.setObjectName("section_title")
        self.history_count = QLabel("")
        self.history_count.setStyleSheet("color: #383858; font-size: 10px; font-weight: 600;")
        history_header.addWidget(history_lbl)
        history_header.addStretch()
        history_header.addWidget(self.history_count)
        layout.addLayout(history_header)
        layout.addSpacing(6)

        self.history_container = QHBoxLayout()
        self.history_container.setSpacing(6)
        self.history_container.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.history_container)
        layout.addStretch()

        return card

    def _make_controls(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.start_btn = QPushButton("▶  Start Translation")
        self.start_btn.setObjectName("start_btn")
        self.start_btn.setFixedHeight(44)
        self.start_btn.clicked.connect(self._start_detection)

        self.stop_btn = QPushButton("■  Stop")
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setFixedHeight(44)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_detection)

        self.mic_toggle_btn = QPushButton("🔇  Muted")
        self.mic_toggle_btn.setObjectName("mic_toggle_btn")
        self.mic_toggle_btn.setFixedHeight(44)
        self.mic_toggle_btn.setEnabled(False)
        self.mic_toggle_btn.setProperty("muted", True)
        self.mic_toggle_btn.clicked.connect(self._toggle_mic)

        hint = QLabel("Sign → Speech  ·  Speech → Sign  ·  Fully Offline")
        hint.setStyleSheet("color: #383858; font-size: 12px; font-weight: 500;")

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.mic_toggle_btn)
        layout.addStretch()
        layout.addWidget(hint)
        return layout

    # ══════════════════════════════════════════════════════════════════
    #  ACTIONS
    # ══════════════════════════════════════════════════════════════════

    def _start_detection(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self._set_live(True)
        self._status("ᐧ  Detection running…")

        # Start pulse animation
        self._pulse_frame = 0
        self._pulse_timer.start()

        # Enable mic toggle, start MUTED by default for privacy
        self._mic_muted = True
        self.mic_toggle_btn.setEnabled(True)
        self.mic_toggle_btn.setText("🔇  Muted")
        self.mic_toggle_btn.setStyleSheet("")
        self.mic_toggle_btn.setProperty("muted", True)
        self.mic_icon.setText("🔇")

        # Sign→Speech thread
        self._detector = SignDetector()
        self._detector.frame_ready.connect(self._update_frame)
        self._detector.prediction_ready.connect(self._on_prediction)
        self._detector.start()

        # Speech→Sign thread (starts muted by default)
        self._listener = SpeechListener()
        self._listener.set_muted(True)
        self._listener.word_recognized.connect(self._on_word_recognized)
        self._listener.status_message.connect(self._on_listener_status)
        self._listener.model_ready.connect(self._on_model_ready)
        self._download_dialog = None
        self._listener.start()

    def _stop_detection(self):
        # Stop glow animation — reset opacity but keep effect alive
        self._glow_timer.stop()
        self._glow_effect.setOpacity(1.0)

        # Stop pulse
        self._pulse_timer.stop()

        if self._detector:
            self._detector.stop()
            self._detector = None
        if self._listener:
            self._listener.stop()
            self._listener = None
        if self._speech_engine:
            self._speech_engine.stop()

        self._speaking_timer.stop()
        self.speaking_indicator.hide()

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.mic_toggle_btn.setEnabled(False)
        self.mic_toggle_btn.setText("🔇  Muted")
        self.mic_toggle_btn.setStyleSheet("")
        self.mic_icon.setText("🔇")
        self._set_live(False)
        self._status("ᐧ  Stopped.")

        self.webcam_label.setText("Camera feed will appear here")
        self.webcam_label.setPixmap(QPixmap())
        self.cam_status.setStyleSheet("color: #383858; font-size: 11px;")

    # ══════════════════════════════════════════════════════════════════
    #  MIC TOGGLE
    # ══════════════════════════════════════════════════════════════════

    def _toggle_mic(self):
        """Toggle the microphone between muted and unmuted states.
        When muted, audio is still captured but NOT sent to Vosk."""
        self._mic_muted = not self._mic_muted

        if self._listener:
            self._listener.set_muted(self._mic_muted)

        if self._mic_muted:
            self.mic_toggle_btn.setText("🔇  Muted")
            self.mic_toggle_btn.setProperty("muted", True)
            self.mic_toggle_btn.style().unpolish(self.mic_toggle_btn)
            self.mic_toggle_btn.style().polish(self.mic_toggle_btn)
            self.mic_icon.setText("🔇")
            self._status("·  Mic MUTED — speech recognition paused")
        else:
            self.mic_toggle_btn.setText("🎤  Unmuted")
            self.mic_toggle_btn.setProperty("muted", False)
            self.mic_toggle_btn.style().unpolish(self.mic_toggle_btn)
            self.mic_toggle_btn.style().polish(self.mic_toggle_btn)
            self.mic_icon.setText("🎤")
            self._status("·  Mic UNMUTED — listening for letters")

    # ══════════════════════════════════════════════════════════════════
    #  PHONETIC LETTER MAP
    # ══════════════════════════════════════════════════════════════════

    _NATO_ALPHABET = {
        "ALPHA": "A", "BRAVO": "B", "CHARLIE": "C", "DELTA": "D",
        "ECHO": "E", "FOXTROT": "F", "GOLF": "G", "HOTEL": "H",
        "INDIA": "I", "JULIET": "J", "KILO": "K", "LIMA": "L",
        "MIKE": "M", "NOVEMBER": "N", "OSCAR": "O", "PAPA": "P",
        "QUEBEC": "Q", "ROMEO": "R", "SIERRA": "S", "TANGO": "T",
        "UNIFORM": "U", "VICTOR": "V", "WHISKEY": "W", "XRAY": "X",
        "X-RAY": "X", "YANKEE": "Y", "ZULU": "Z",
    }

    _PRONUNCIATION_MAP = {
        "AY": "A", "A": "A", "EH": "A",
        "BEE": "B", "BE": "B", "BEA": "B",
        "SEE": "C", "SEA": "C", "SHE": "C", "CEE": "C",
        "DEE": "D", "DE": "D", "D": "D",
        "EE": "E", "E": "E", "HE": "E",
        "EFF": "F", "EF": "F", "F": "F",
        "GEE": "G", "GE": "G", "G": "G", "JEE": "G",
        "AITCH": "H", "HAYCH": "H", "H": "H", "AGE": "H",
        "EYE": "I", "AYE": "I", "I": "I",
        "JAY": "J", "J": "J",
        "KAY": "K", "KAYE": "K", "K": "K", "CAKE": "K", "KAE": "K",
        "ELL": "L", "EL": "L", "L": "L", "HELL": "L",
        "EM": "M", "M": "M", "THEM": "M",
        "EN": "N", "N": "N", "HEN": "N", "TEN": "N", "IN": "N",
        "OH": "O", "O": "O", "NO": "O", "OWE": "O",
        "PEE": "P", "PE": "P", "PEA": "P", "P": "P",
        "CUE": "Q", "QUEUE": "Q", "Q": "Q", "QU": "Q",
        "AR": "R", "ARE": "R", "R": "R", "OUR": "R", "RR": "R",
        "ESS": "S", "ES": "S", "S": "S", "YES": "S", "US": "S",
        "TEE": "T", "TE": "T", "T": "T", "TEA": "T",
        "YOU": "U", "U": "U", "EWE": "U", "YEW": "U", "EW": "U",
        "VEE": "V", "VE": "V", "V": "V",
        "DOUBLE": "W", "DUB": "W", "DOUBLEYOU": "W",
        "EX": "X", "X": "X", "EKS": "X",
        "WHY": "Y", "WYE": "Y", "Y": "Y", "WI": "Y",
        "ZEE": "Z", "ZED": "Z", "Z": "Z", "ZE": "Z",
    }

    _SPEECH_TO_LETTER = {**_NATO_ALPHABET, **_PRONUNCIATION_MAP, **{
        "ONE": "1", "TWO": "2", "THREE": "3", "FOUR": "4", "FIVE": "5",
        "SIX": "6", "SEVEN": "7", "EIGHT": "8", "NINE": "9", "ZERO": "0",
        "FOR": "4", "TO": "2", "TOO": "2",
    }}

    # ══════════════════════════════════════════════════════════════════
    #  SLOTS
    # ══════════════════════════════════════════════════════════════════

    @pyqtSlot(QImage)
    def _update_frame(self, qt_image):
        pixmap = QPixmap.fromImage(qt_image)
        scaled = pixmap.scaled(
            self.webcam_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.webcam_label.setPixmap(scaled)

    @pyqtSlot(str, float)
    def _on_prediction(self, label: str, confidence: float):
        # Update prediction display with animation glow
        self.prediction_text.setText(label)
        self.prediction_text.setProperty("class", "detected")
        self.prediction_text.style().unpolish(self.prediction_text)
        self.prediction_text.style().polish(self.prediction_text)

        # Start glow animation — apply opacity effect that fades in/out
        self._glow_effect.setOpacity(0.3)
        self.prediction_text.setGraphicsEffect(self._glow_effect)
        self._glow_direction = 1
        self._glow_timer.start()

        # Update history
        self._history.append(label)
        if len(self._history) > 8:
            self._history.pop(0)
        self._update_history()

        # Speak the word
        self._speech_engine.speak(label)
        self._show_sign_gif(label)

        # Status
        self._status(f"ᐧ  Detected: {label}")
        self.detection_status.setText(f"→ {label}")

    @pyqtSlot(str)
    def _on_word_recognized(self, word: str):
        """Handle recognized speech from Vosk.
        Vosk now uses grammar mode restricted to A-Z and 0-9, so the
        output should already be a letter or digit. We still check the
        pronunciation map as a safety net, but DO NOT fall back to
        taking the first character of a word — letters only."""
        raw = word.strip().lower()
        if not raw:
            return

        # Mic indicator flash
        self.mic_status_dot.setStyleSheet("color: #22c55e; font-size: 8px;")
        QTimer.singleShot(300, lambda: self.mic_status_dot.setStyleSheet("color: #282848; font-size: 8px;"))

        cleaned = raw.upper()

        # ── 1) Direct match: if it's already a single letter/digit, use it ──
        if len(cleaned) == 1 and (cleaned.isalpha() or cleaned.isdigit()):
            letter = cleaned
        else:
            # ── 2) Pronunciation map lookup (safety net for edge cases) ──
            letter = self._SPEECH_TO_LETTER.get(cleaned)
            if letter is None:
                # Substring match for multi-word phrases like "double u" → W
                for phrase, result in self._SPEECH_TO_LETTER.items():
                    if phrase in cleaned or cleaned in phrase:
                        letter = result
                        break

            # ── 3) NO first-character fallback! Words are not accepted ──
            if letter is None:
                self._status(f"·  Vosk: “{raw}” — not a letter, ignored")
                self.transcript_label.setText(f"“{raw}” (ignored)")
                return

        # Only proceed if it's a recognizable sign (A-Z, 0-9)
        if len(letter) == 1 and (letter.isalpha() or letter.isdigit()):
            display_word = raw[:20]
            self.transcript_label.setText(f"“{display_word}” → “{letter}”")
            self._status(f"·  Vosk: “{raw}” → “{letter}”")
            # Also update the DETECTED SIGN text at the top of the panel
            self.prediction_text.setText(letter)
            self.prediction_text.setProperty("class", "detected")
            self.prediction_text.style().unpolish(self.prediction_text)
            self.prediction_text.style().polish(self.prediction_text)
            self._show_sign_gif(letter)

    def _on_listener_status(self, msg: str):
        """Handle listener status messages, showing modal dialog for downloads."""
        if msg.startswith("MODAL_DOWNLOAD:"):
            text = msg.replace("MODAL_DOWNLOAD:", "")
            if self._download_dialog is None:
                self._download_dialog = QProgressDialog(text, None, 0, 100, self)
                self._download_dialog.setWindowTitle("Downloading Model")
                self._download_dialog.setWindowModality(Qt.WindowModality.WindowModal)
                self._download_dialog.setMinimumWidth(400)
                self._download_dialog.setCancelButton(None)
                self._download_dialog.show()
            else:
                self._download_dialog.setLabelText(text)
        elif msg.startswith("MODAL_PROGRESS:"):
            pct = int(msg.replace("MODAL_PROGRESS:", ""))
            if self._download_dialog:
                self._download_dialog.setValue(pct)
        elif msg.startswith("MODAL_EXTRACT:"):
            text = msg.replace("MODAL_EXTRACT:", "")
            if self._download_dialog:
                self._download_dialog.setLabelText(text)
        elif msg.startswith("MODAL_FAIL:"):
            text = msg.replace("MODAL_FAIL:", "")
            if self._download_dialog:
                self._download_dialog.close()
                self._download_dialog = None
            self._status(text)
        else:
            self._status(msg)

    def _on_model_ready(self, success: bool):
        """Called when the Vosk model finishes loading."""
        if self._download_dialog:
            self._download_dialog.close()
            self._download_dialog = None
        if success:
            self._status("·  Speech→Sign ready")
        else:
            self._status("·  Speech→Sign unavailable (no model)")

    @pyqtSlot(str)
    def _on_speaking_started(self, word: str):
        self._speaking_anim_frame = 0
        self.speaking_indicator.show()
        self._speaking_timer.start()

    @pyqtSlot()
    def _on_speaking_finished(self):
        self._speaking_timer.stop()
        self.speaking_indicator.hide()

    # ══════════════════════════════════════════════════════════════════
    #  ANIMATIONS
    # ══════════════════════════════════════════════════════════════════

    def _tick_pulse(self):
        """Pulse the live badge opacity for a heartbeat effect."""
        self._pulse_frame += 1
        phase = math.sin(self._pulse_frame * 0.5) * 0.3 + 0.7
        self.live_badge.setStyleSheet(
            f"background-color: rgba(248, 113, 113, {phase * 0.85:.2f});"
            f"color: white; border-radius: 8px;"
            f"padding: 2px 12px; font-size: 11px; font-weight: 700;"
        )

    def _tick_detection_glow(self):
        """Animate a subtle glow effect on the prediction text via opacity."""
        current = self._glow_effect.opacity()
        new_opacity = current + 0.04 * self._glow_direction
        
        if new_opacity >= 1.0:
            new_opacity = 1.0
            self._glow_direction = -1
        elif new_opacity <= 0.3:
            new_opacity = 0.3
            self._glow_direction = 1
            self._glow_timer.stop()
            # Reset opacity to 1.0 but DON'T delete the effect via
            # setGraphicsEffect(None) — that destroys the C++ object and
            # the next detection would crash. At opacity 1.0 the effect
            # is a visual no-op pass-through.
            self._glow_effect.setOpacity(1.0)
            self.prediction_text.setProperty("class", "")
            self.prediction_text.style().unpolish(self.prediction_text)
            self.prediction_text.style().polish(self.prediction_text)
            return  # Don't fall through to setOpacity at the bottom

    def _tick_speaking_animation(self):
        """Animate the equalizer bars with a smoother waveform."""
        bars = [
            "▁ ▂ ▃ ▄ ▅ ▆ ▇ █",
            " ▂ ▃ ▄ ▅ ▆ ▇ █ ▇",
            "  ▃ ▄ ▅ ▆ ▇ █ ▇ ▆",
            "   ▄ ▅ ▆ ▇ █ ▇ ▆ ▅",
            "    ▅ ▆ ▇ █ ▇ ▆ ▅ ▄",
            "     ▆ ▇ █ ▇ ▆ ▅ ▄ ▃",
            "      ▇ █ ▇ ▆ ▅ ▄ ▃ ▂",
            "       █ ▇ ▆ ▅ ▄ ▃ ▂ ▁",
            "      ▇ █ ▇ ▆ ▅ ▄ ▃ ▂",
            "     ▆ ▇ █ ▇ ▆ ▅ ▄ ▃",
            "    ▅ ▆ ▇ █ ▇ ▆ ▅ ▄",
            "   ▄ ▅ ▆ ▇ █ ▇ ▆ ▅",
            "  ▃ ▄ ▅ ▆ ▇ █ ▇ ▆",
            " ▂ ▃ ▄ ▅ ▆ ▇ █ ▇",
        ]
        self._speaking_anim_frame = (self._speaking_anim_frame + 1) % len(bars)
        self.speaking_indicator.setText(bars[self._speaking_anim_frame].ljust(16))

    # ══════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════

    def _show_sign_gif(self, word: str):
        """Display an image for the recognized word."""
        word_upper = word.strip().upper()
        if not word_upper:
            return

        if self._current_movie:
            self._current_movie.stop()
            self._current_movie = None

        # 1) data/raw_images/<LABEL>/
        if len(word_upper) == 1:
            raw_dir = resource_path(os.path.join("data", "raw_images", word_upper))
            if os.path.exists(raw_dir):
                images = [
                    img for img in os.listdir(raw_dir)
                    if img.lower().endswith(('.png', '.jpg', '.jpeg'))
                ]
                if images:
                    images.sort()
                    img_path = os.path.join(raw_dir, images[0])
                    pixmap = QPixmap(img_path)
                    if not pixmap.isNull():
                        self.sign_gif_label.setPixmap(
                            pixmap.scaled(
                                260, 200,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation
                            )
                        )
                        return

        # 2) signs/ directory
        candidates = [
            os.path.join(self.SIGNS_DIR, f"{word.lower()}.gif"),
            os.path.join(self.SIGNS_DIR, f"{word.lower().replace(' ', '_')}.gif"),
            os.path.join(self.SIGNS_DIR, f"{word.lower()}.png"),
            os.path.join(self.SIGNS_DIR, f"{word.lower().replace(' ', '_')}.png"),
        ]
        for path in candidates:
            if os.path.exists(path):
                if path.endswith(".gif"):
                    movie = QMovie(path)
                    self._current_movie = movie
                    self.sign_gif_label.setMovie(movie)
                    movie.start()
                else:
                    self.sign_gif_label.setPixmap(
                        QPixmap(path).scaled(
                            260, 200,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                    )
                return

        # 3) Placeholder card
        self._generate_placeholder_card(word_upper)

    def _generate_placeholder_card(self, letter: str):
        """Generate a refined QPixmap placeholder using the new design language."""
        size = (260, 200)
        pixmap = QPixmap(*size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = size

        # ── Background rounded rect ──
        rect = QPainterPath()
        rect.addRoundedRect(6, 6, w - 12, h - 12, 16, 16)

        # Fill with gradient
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, QColor(14, 14, 30))
        grad.setColorAt(1.0, QColor(10, 10, 22))
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor(28, 28, 55), 1.5))
        painter.drawPath(rect)

        # ── Radial glow in center ──
        glow = QRadialGradient(w / 2, h / 2, 70)
        glow.setColorAt(0.0, QColor(6, 182, 212, 30))
        glow.setColorAt(0.6, QColor(59, 130, 246, 15))
        glow.setColorAt(1.0, QColor(6, 182, 212, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(w / 2 - 70, h / 2 - 70, 140, 140)

        # ── Subtle border ring ──
        ring = QPainterPath()
        ring.addEllipse(w / 2 - 44, h / 2 - 48, 88, 88)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(99, 102, 241, 60), 1.5))
        painter.drawPath(ring)

        # ── The letter ──
        font = QFont("Segoe UI", 60, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(230, 230, 250))
        painter.drawText(
            6, 10, w - 12, h - 40,
            Qt.AlignmentFlag.AlignCenter, letter
        )

        # ── Small label ──
        small_font = QFont("Segoe UI", 8, QFont.Weight.Semibold)
        painter.setFont(small_font)
        painter.setPen(QColor(58, 58, 90))
        painter.drawText(
            6, h - 28, w - 12, 18,
            Qt.AlignmentFlag.AlignCenter, "ASL SIGN"
        )

        painter.end()
        self.sign_gif_label.setPixmap(pixmap)

    def _update_history(self):
        """Rebuild history badges."""
        # Clear existing
        while self.history_container.count():
            item = self.history_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for item in self._history:
            badge = QLabel(item)
            badge.setObjectName("history_badge")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_container.addWidget(badge)

        self.history_container.addStretch()

        count = len(self._history)
        self.history_count.setText(f"{count} items" if count > 0 else "")

    def _set_live(self, is_live: bool):
        if is_live:
            self.live_badge.setText("●  LIVE")
            self.live_badge.setStyleSheet(
                "background-color: rgba(248, 113, 113, 0.85);"
                "color: white; border-radius: 8px;"
                "padding: 2px 12px; font-size: 11px; font-weight: 700;"
            )
            self.cam_status.setStyleSheet("color: #22c55e; font-size: 11px; font-weight: 500;")
            self.cam_status.setText("●  Camera active")
        else:
            self.live_badge.setText("⏻  OFFLINE")
            self.live_badge.setStyleSheet(
                "background-color: #141428; color: #484868; border-radius: 8px;"
                "padding: 2px 12px; font-size: 11px; font-weight: 700;"
            )

    def _status(self, msg: str):
        self.status_bar.showMessage(f"  {msg}")

    def closeEvent(self, event):
        self._stop_detection()
        super().closeEvent(event)

