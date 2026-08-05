"""
app/lucide_icons.py
===================
Minimal embedded Lucide icon renderer for the PyQt6 desktop app.

Lucide icons (ISC license) are embedded as SVG strings so the app needs no
extra asset files and the PyInstaller spec stays untouched. Icons are
colorized at render time to match the dark UI theme.

Usage:
    pixmap = render_icon("mic", "#5f9e6f", 16)               # -> QPixmap
    html   = icon_html("circle", "#d97757", 10, filled=True)  # -> rich-text <img>
"""

import base64

from PyQt6.QtCore import Qt, QByteArray, QRectF
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer

# Lucide SVG bodies (ISC license, https://lucide.dev) — <svg> wrapper re-added below.
_ICON_PATHS = {
    "hand": (
        '<path d="M18 11V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2"/>'
        '<path d="M14 10V4a2 2 0 0 0-2-2a2 2 0 0 0-2 2v2"/>'
        '<path d="M10 10.5V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2v8"/>'
        '<path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/>'
    ),
    "mic": (
        '<path d="M12 19v3"/>'
        '<path d="M19 10v2a7 7 0 0 1-14 0v-2"/>'
        '<rect x="9" y="2" width="6" height="13" rx="3"/>'
    ),
    "mic-off": (
        '<path d="M12 19v3"/>'
        '<path d="M15 9.34V5a3 3 0 0 0-5.68-1.33"/>'
        '<path d="M16.95 16.95A7 7 0 0 1 5 12v-2"/>'
        '<path d="M18.89 13.23A7 7 0 0 0 19 12v-2"/>'
        '<path d="m2 2 20 20"/>'
        '<path d="M9 9v3a3 3 0 0 0 5.12 2.12"/>'
    ),
    "play": (
        '<path d="M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z"/>'
    ),
    "square": (
        '<rect width="18" height="18" x="3" y="3" rx="2"/>'
    ),
    "power": (
        '<path d="M12 2v10"/>'
        '<path d="M18.4 6.6a9 9 0 1 1-12.77.04"/>'
    ),
    "circle": (
        '<circle cx="12" cy="12" r="10"/>'
    ),
}

_SVG_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
)


def _colorize(name, color, filled=False):
    """Return the SVG markup for icon ``name`` tinted with ``color``."""
    svg = _SVG_TEMPLATE.format(body=_ICON_PATHS[name])
    if filled:
        svg = svg.replace('fill="none"', 'fill="currentColor"')
    svg = svg.replace('stroke="currentColor"', f'stroke="{color}"')
    if filled:
        svg = svg.replace('fill="currentColor"', f'fill="{color}"')
    return svg


def render_icon(name, color, size, filled=False):
    """Render a Lucide icon to a QPixmap of ``size`` x ``size`` pixels."""
    renderer = QSvgRenderer(QByteArray(_colorize(name, color, filled).encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return pixmap


def icon_html(name, color, size, filled=False):
    """Return an HTML <img> data-URI for use inside QLabel rich text."""
    svg = _colorize(name, color, filled)
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (
        f'<img src="data:image/svg+xml;base64,{b64}" '
        f'width="{size}" height="{size}" style="vertical-align:middle">'
    )
