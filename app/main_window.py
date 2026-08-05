"""
app/main_window.py
==================
Main PyQt6 window for AI Sign Bridge.
Warm claymorphism UI — puffy clay cards, chunky extruded buttons,
soft pastel blobs, recessed camera/sign wells, smooth animations
and playful micro-interactions.

Layout: Webcam feed (left) | Sign output + GIF (right) | Status bar (bottom)
"""

import os
import math
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStatusBar, QSizePolicy,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QProgressDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QSize
from PyQt6.QtGui import (
    QPixmap, QFont, QMovie, QColor, QImage, QIcon,
    QPainter, QLinearGradient, QPen, QPainterPath,
    QBrush, QRadialGradient
)

from app.sign_detector import SignDetector
from app.speech_engine import SpeechEngine
from app.speech_listener import SpeechListener
from app.paths import resource_path
from app.lucide_icons import render_icon, icon_html


# ─── Claymorphism Stylesheet ──────────────────────────────────────────
# Design: warm cream background with soft pastel clay blobs, puffy clay
# cards with top-light gradients and dark bottom "extrusions", chunky
# rounded buttons that sink into the clay when pressed, and recessed
# wells for the camera feed and sign image.

STYLESHEET = """
QMainWindow {
    background-color: #efe6d7;
    color: #5d4e3a;
    font-family: 'Fredoka', 'Baloo 2', 'Nunito', 'Quicksand', 'Segoe UI', sans-serif;
    font-size: 13px;
}

QLabel {
    color: #5d4e3a;
}

/* ── Cards (opaque liquid glass) ── */
QFrame#card {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #fefdf9, stop:0.2 #f6f0e4, stop:0.44 #eee4cf,
        stop:0.49 #fdfbf5, stop:0.72 #e9dfc9, stop:1 #dfd3bb);
    border: none;
    border-top: 1px solid #ffffff;
    border-left: 1px solid #ffffff;
    border-right: 1px solid #ddd1b8;
    border-bottom: 1px solid #d7c9ae;
    border-radius: 26px;
}

QFrame#card_accent {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #fefdf9, stop:0.2 #f6f0e4, stop:0.44 #eee4cf,
        stop:0.49 #fdfbf5, stop:0.72 #e9dfc9, stop:1 #dfd3bb);
    border: none;
    border-top: 2px solid qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #f6ad6d, stop:0.5 #93c8ae, stop:1 #e39a8d);
    border-left: 1px solid #ffffff;
    border-right: 1px solid #ddd1b8;
    border-bottom: 1px solid #d7c9ae;
    border-radius: 26px;
}

/* ── Section Titles ── */
QLabel#section_title {
    color: #a08b6f;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 2px;
}

/* ── Webcam well (recessed clay) ── */
QLabel#webcam_label {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #e8dbc4, stop:1 #f6efe1);
    border: none;
    border-top: 3px solid #d4c4a8;
    border-bottom: 1px solid #fdf9f0;
    border-radius: 20px;
    color: #b3a184;
    font-size: 13px;
}

/* ── Prediction Display ── */
QLabel#prediction_text {
    color: #5d4e3a;
    font-size: 60px;
    font-weight: 800;
    letter-spacing: -2px;
}
QLabel#prediction_text[class="detected"] {
    color: #7da86b;
}

/* ── Sign Image well (recessed clay) ── */
QLabel#sign_gif_label {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #e8dbc4, stop:1 #f6efe1);
    border: none;
    border-top: 3px solid #d4c4a8;
    border-bottom: 1px solid #fdf9f0;
    border-radius: 20px;
    color: #b3a184;
    font-size: 13px;
}

/* ── Transcript chip (inset) ── */
QLabel#transcript_label {
    color: #7a6850;
    font-size: 14px;
    font-weight: 600;
    padding: 8px 14px;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #f1e7d4, stop:1 #fbf6ec);
    border: none;
    border-top: 2px solid #dfd2b8;
    border-radius: 14px;
}

/* ── History chips ── */
QLabel#history_badge {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #ffddb0, stop:1 #f7c48f);
    color: #8a5a26;
    border: none;
    border-bottom: 3px solid #dfa363;
    border-radius: 11px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: 800;
}

/* ── Start button (peach clay) ── */
QPushButton#start_btn {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #ffd9a9, stop:1 #f6ad6d);
    color: #7c4a1e;
    border: none;
    border-top: 2px solid #ffe9cb;
    border-bottom: 5px solid #d98f4f;
    border-radius: 16px;
    padding: 10px 28px;
    font-size: 14px;
    font-weight: 800;
    min-width: 130px;
}
QPushButton#start_btn:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #ffdfb6, stop:1 #f9b87c);
}
QPushButton#start_btn:pressed {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #ef9f59, stop:1 #ffd3a0);
    border-top: 5px solid #d98f4f;
    border-bottom: 1px solid #d98f4f;
    padding-top: 14px;
    padding-bottom: 6px;
}
QPushButton#start_btn:disabled {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #eee4d1, stop:1 #e4d7bf);
    color: #b7a689;
    border-bottom: 4px solid #d4c6aa;
    border-top: 1px solid #f8f2e6;
}

/* ── Stop button (rose clay) ── */
QPushButton#stop_btn {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #f9cbc4, stop:1 #e79a8c);
    color: #7c3a28;
    border: none;
    border-top: 2px solid #fde4de;
    border-bottom: 5px solid #c07668;
    border-radius: 16px;
    padding: 10px 28px;
    font-size: 14px;
    font-weight: 800;
    min-width: 130px;
}
QPushButton#stop_btn:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #fbd5ce, stop:1 #eba89a);
}
QPushButton#stop_btn:pressed {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #dc8a79, stop:1 #f9cfc8);
    border-top: 5px solid #c07668;
    border-bottom: 1px solid #c07668;
    padding-top: 14px;
    padding-bottom: 6px;
}
QPushButton#stop_btn:disabled {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #eee4d1, stop:1 #e4d7bf);
    color: #b7a689;
    border-bottom: 4px solid #d4c6aa;
    border-top: 1px solid #f8f2e6;
}

/* ── Mic toggle (mint clay / rose when muted) ── */
QPushButton#mic_toggle_btn {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #cde8d8, stop:1 #9ccdb4);
    color: #2f6b50;
    border: none;
    border-top: 2px solid #e5f4eb;
    border-bottom: 5px solid #6faa8d;
    border-radius: 16px;
    padding: 10px 18px;
    font-size: 14px;
    font-weight: 800;
    min-width: 100px;
}
QPushButton#mic_toggle_btn:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #d5ecdd, stop:1 #a8d4bc);
}
QPushButton#mic_toggle_btn:pressed {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #8fc0a6, stop:1 #cfe9dc);
    border-top: 5px solid #6faa8d;
    border-bottom: 1px solid #6faa8d;
    padding-top: 14px;
    padding-bottom: 6px;
}
QPushButton#mic_toggle_btn[muted="true"] {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #f8cbc4, stop:1 #e6a093);
    color: #7c3a28;
    border-top: 2px solid #fde4de;
    border-bottom: 5px solid #c07668;
}
QPushButton#mic_toggle_btn[muted="true"]:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #fad5cf, stop:1 #ebac9f);
}
QPushButton#mic_toggle_btn[muted="true"]:pressed {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #d98c7c, stop:1 #f8cfc8);
    border-top: 5px solid #c07668;
    border-bottom: 1px solid #c07668;
    padding-top: 14px;
    padding-bottom: 6px;
}
QPushButton#mic_toggle_btn:disabled {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #eee4d1, stop:1 #e4d7bf);
    color: #b7a689;
    border-bottom: 4px solid #d4c6aa;
    border-top: 1px solid #f8f2e6;
}

/* ── Status Bar ── */
QStatusBar {
    background-color: #eadfc9;
    color: #a08b6f;
    border-top: 2px solid #dccfb4;
    font-size: 12px;
    padding: 5px 14px;
}

/* ── Live Badge ── */
QLabel#live_badge {
    border-radius: 11px;
    padding: 4px 14px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

/* ── Header ── */
QLabel#header_title {
    color: #5d4e3a;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.3px;
}

QLabel#header_subtitle {
    color: #a08b6f;
    font-size: 12px;
    font-weight: 600;
}

/* ── Speaking Indicator ── */
QLabel#speaking_indicator {
    color: #7da86b;
    font-size: 14px;
    font-weight: 800;
    padding: 2px;
}

/* ── FPS Counter ── */
QLabel#fps_label {
    color: #b3a184;
    font-size: 11px;
    font-weight: 700;
    font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
}

/* ── Mic Icon ── */
QLabel#mic_icon {
    font-size: 16px;
    padding: 4px;
}

/* ── Divider ── */
QFrame#divider {
    color: #dccfb4;
    max-height: 1px;
}

/* ── Tooltip ── */
QToolTip {
    background-color: #f7f1e5;
    color: #5d4e3a;
    border: 1px solid #d9ccb2;
    border-radius: 10px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ── Download dialog ── */
QProgressDialog {
    background-color: #f7f1e5;
    border-radius: 18px;
}
QProgressDialog QLabel {
    color: #5d4e3a;
    font-size: 13px;
}
QProgressBar {
    background-color: #e4d8c2;
    border: none;
    border-radius: 10px;
    min-height: 16px;
    font-size: 11px;
    color: #5d4e3a;
}
QProgressBar::chunk {
    background-color: #f6ad6d;
    border-radius: 10px;
}

/* ── Scrollbar ── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #cfc0a4;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #bda98a;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


class ClayBackdrop(QWidget):
    """Paints soft pastel clay blobs and a subtle dot texture behind the UI."""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(self.rect(), QColor(239, 230, 215))

        blobs = [
            (w * 0.06, h * 0.02, w * 0.34, QColor(255, 213, 160, 110)),
            (w * 0.93, h * 0.10, w * 0.30, QColor(194, 227, 210, 95)),
            (w * 0.03, h * 0.78, w * 0.32, QColor(246, 196, 190, 85)),
            (w * 0.88, h * 0.86, w * 0.36, QColor(188, 215, 238, 90)),
            (w * 0.60, h * 0.00, w * 0.24, QColor(217, 207, 232, 80)),
        ]
        for cx, cy, radius, color in blobs:
            grad = QRadialGradient(cx, cy, radius)
            grad.setColorAt(0.0, color)
            grad.setColorAt(
                1.0, QColor(color.red(), color.green(), color.blue(), 0)
            )
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2)
            )

        painter.setPen(QColor(160, 139, 111, 22))
        step = 26
        for x in range(step, w, step):
            for y in range(step, h, step):
                painter.drawPoint(x, y)
        painter.end()


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
        backdrop = ClayBackdrop()
        self.setCentralWidget(backdrop)
        root = QVBoxLayout(backdrop)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(16)

        # ── Header ──
        root.addLayout(self._make_header())

        # ── Main Content ──
        content = QHBoxLayout()
        content.setSpacing(20)

        left_card = self._make_left_card()
        right_card = self._make_right_panel()
        self._clay_shadow(left_card, blur=32, dy=10, alpha=70)
        self._clay_shadow(right_card, blur=32, dy=10, alpha=70)

        content.addWidget(left_card, 3)
        content.addWidget(right_card, 2)
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

        icon = QLabel()
        icon.setPixmap(render_icon("hand", "#5d4e3a", 24))

        title = QLabel("AI Sign Bridge")
        title.setObjectName("header_title")

        subtitle = QLabel("Real-Time ASL Translator")
        subtitle.setObjectName("header_subtitle")

        version = QLabel("v1.0")
        version.setStyleSheet("color: #c9bca3; font-size: 10px; font-weight: 700;")

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
        self.mic_icon = QLabel()
        self.mic_icon.setObjectName("mic_icon")
        self._update_mic_icon()

        # Live badge
        self.live_badge = QLabel()
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
        self.cam_status = QLabel()
        self.cam_status.setStyleSheet("color: #7da86b; font-size: 11px; font-weight: 500;")
        self._set_cam_status("Camera ready")
        info_row.addWidget(self.cam_status)
        info_row.addStretch()

        self.detection_status = QLabel("")
        self.detection_status.setStyleSheet("color: #b3a184; font-size: 11px;")
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

        self.mic_status_dot = QLabel()
        self.mic_status_dot.setPixmap(render_icon("circle", "#c9bca3", 8, filled=True))
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
        self.history_count.setStyleSheet("color: #c9bca3; font-size: 10px; font-weight: 700;")
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

        self.start_btn = QPushButton("  Start Translation")
        self.start_btn.setObjectName("start_btn")
        self.start_btn.setIcon(QIcon(render_icon("play", "#7c4a1e", 16)))
        self.start_btn.setIconSize(QSize(16, 16))
        self.start_btn.setFixedHeight(44)
        self.start_btn.clicked.connect(self._start_detection)

        self.stop_btn = QPushButton("  Stop")
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setIcon(QIcon(render_icon("square", "#7c3a28", 16)))
        self.stop_btn.setIconSize(QSize(16, 16))
        self.stop_btn.setFixedHeight(44)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_detection)

        self.mic_toggle_btn = QPushButton("  Muted")
        self.mic_toggle_btn.setObjectName("mic_toggle_btn")
        self.mic_toggle_btn.setIconSize(QSize(16, 16))
        self.mic_toggle_btn.setFixedHeight(44)
        self.mic_toggle_btn.setEnabled(False)
        self.mic_toggle_btn.setProperty("muted", True)
        self.mic_toggle_btn.clicked.connect(self._toggle_mic)
        self._set_mic_button_state()

        for btn in (self.start_btn, self.stop_btn, self.mic_toggle_btn):
            self._clay_shadow(btn, blur=16, dy=5, alpha=55)

        hint = QLabel("Sign → Speech  ·  Speech → Sign  ·  Fully Offline")
        hint.setStyleSheet("color: #a08b6f; font-size: 12px; font-weight: 600;")

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
        self.mic_toggle_btn.setStyleSheet("")
        self.mic_toggle_btn.setProperty("muted", True)
        self._set_mic_button_state()
        self._update_mic_icon()

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
        self.mic_toggle_btn.setStyleSheet("")
        self._mic_muted = True
        self._set_mic_button_state()
        self._update_mic_icon()
        self._set_live(False)
        self._status("ᐧ  Stopped.")

        self.webcam_label.setText("Camera feed will appear here")
        self.webcam_label.setPixmap(QPixmap())
        self.cam_status.setStyleSheet("color: #b3a184; font-size: 11px;")
        self._set_cam_status("Camera ready", "#b3a184")

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
            self.mic_toggle_btn.setProperty("muted", True)
            self.mic_toggle_btn.style().unpolish(self.mic_toggle_btn)
            self.mic_toggle_btn.style().polish(self.mic_toggle_btn)
            self._set_mic_button_state()
            self._update_mic_icon()
            self._status("·  Mic MUTED — speech recognition paused")
        else:
            self.mic_toggle_btn.setProperty("muted", False)
            self.mic_toggle_btn.style().unpolish(self.mic_toggle_btn)
            self.mic_toggle_btn.style().polish(self.mic_toggle_btn)
            self._set_mic_button_state()
            self._update_mic_icon()
            self._status("·  Mic UNMUTED — listening for letters")

    # ══════════════════════════════════════════════════════════════════
    #  ICON STATE HELPERS (Lucide icons)
    # ══════════════════════════════════════════════════════════════════

    def _mic_icon_state(self):
        """Return the (icon name, color) for the current mute state."""
        if self._mic_muted:
            return "mic-off", "#d97757"
        return "mic", "#5f9e6f"

    def _set_mic_button_state(self):
        """Refresh the mic toggle button icon + label from the current mute state."""
        icon, color = self._mic_icon_state()
        self.mic_toggle_btn.setIcon(QIcon(render_icon(icon, color, 16)))
        self.mic_toggle_btn.setText("  Muted" if self._mic_muted else "  Unmuted")

    def _update_mic_icon(self):
        """Refresh the header mic status icon from the current mute state."""
        icon, color = self._mic_icon_state()
        self.mic_icon.setPixmap(render_icon(icon, color, 16))

    def _set_cam_status(self, text, color="#7da86b"):
        """Update the camera status label with a colored status dot."""
        self.cam_status.setText(f'{icon_html("circle", color, 9, filled=True)}  {text}')

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
        self.mic_status_dot.setPixmap(render_icon("circle", "#5f9e6f", 8, filled=True))
        QTimer.singleShot(300, lambda: self.mic_status_dot.setPixmap(render_icon("circle", "#c9bca3", 8, filled=True)))

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
            f"background-color: rgba(217, 119, 87, {phase * 0.95:.2f});"
            f"color: #fff7ef; border-radius: 11px;"
            f"padding: 4px 14px; font-size: 11px; font-weight: 800;"
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

    def _clay_shadow(self, widget, blur=28, dy=9, alpha=60):
        """Soft extruded drop shadow — the claymorphism signature."""
        effect = QGraphicsDropShadowEffect(widget)
        effect.setBlurRadius(blur)
        effect.setOffset(0, dy)
        effect.setColor(QColor(0, 0, 0, alpha))
        widget.setGraphicsEffect(effect)

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
        """Generate a clay-styled QPixmap placeholder."""
        size = (260, 200)
        pixmap = QPixmap(*size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = size

        # ── Clay body ──
        rect = QPainterPath()
        rect.addRoundedRect(4, 4, w - 8, h - 8, 22, 22)

        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(255, 251, 244))
        grad.setColorAt(1.0, QColor(238, 228, 208))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(rect)

        # ── Clay extrusion (bottom edge) ──
        edge = QPainterPath()
        edge.addRoundedRect(4, h - 16, w - 8, 12, 10, 10)
        painter.setBrush(QColor(217, 204, 178))
        painter.drawPath(edge)

        # ── Soft peach glow ──
        glow = QRadialGradient(w / 2, h / 2, 80)
        glow.setColorAt(0.0, QColor(246, 173, 109, 46))
        glow.setColorAt(0.6, QColor(246, 173, 109, 18))
        glow.setColorAt(1.0, QColor(246, 173, 109, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(w / 2 - 80, h / 2 - 80, 160, 160)

        # ── Peach clay ring ──
        ring = QPainterPath()
        ring.addEllipse(w / 2 - 46, h / 2 - 50, 92, 92)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(222, 154, 92, 90), 2))
        painter.drawPath(ring)

        # ── The letter ──
        font = QFont("Fredoka", 60, QFont.Weight.Bold)
        font.setFamilies(["Fredoka", "Baloo 2", "Nunito", "Segoe UI", "sans-serif"])
        painter.setFont(font)
        painter.setPen(QColor(93, 78, 58))
        painter.drawText(
            6, 10, w - 12, h - 40,
            Qt.AlignmentFlag.AlignCenter, letter
        )

        # ── Small label ──
        small_font = QFont("Fredoka", 8, QFont.Weight.Semibold)
        small_font.setFamilies(["Fredoka", "Baloo 2", "Nunito", "Segoe UI", "sans-serif"])
        painter.setFont(small_font)
        painter.setPen(QColor(176, 155, 128))
        painter.drawText(
            6, h - 26, w - 12, 18,
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
            self.live_badge.setText(f'{icon_html("circle", "#fff1e8", 10, filled=True)}  LIVE')
            self.live_badge.setStyleSheet(
                "background-color: #d97757; color: #fff7ef; border-radius: 11px;"
                "padding: 4px 14px; font-size: 11px; font-weight: 800;"
            )
            self.cam_status.setStyleSheet("color: #7da86b; font-size: 11px; font-weight: 500;")
            self.cam_status.setText(f'{icon_html("circle", "#7da86b", 9, filled=True)}  Camera active')
        else:
            self.live_badge.setText(f'{icon_html("power", "#a08b6f", 10)}  OFFLINE')
            self.live_badge.setStyleSheet(
                "background-color: #e6dbc6; color: #a08b6f; border-radius: 11px;"
                "padding: 4px 14px; font-size: 11px; font-weight: 800;"
            )

    def _status(self, msg: str):
        self.status_bar.showMessage(f"  {msg}")

    def closeEvent(self, event):
        self._stop_detection()
        super().closeEvent(event)

