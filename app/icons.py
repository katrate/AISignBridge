

from urllib.parse import quote

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from app.paths import resource_path


_CACHE = {}


def _svg_source(name, color):
    with open(resource_path(f"assets/icons/{name}.svg"), encoding="utf-8") as f:
        return f.read().replace("currentColor", color)


def icon_data_uri(name, color="#ededf5"):
    svg = _svg_source(name, color)
    return "data:image/svg+xml," + quote(svg)


def _render_pixmap(name, size, color):
    key = (name, size, color)
    if key in _CACHE:
        return _CACHE[key]
    try:
        svg = _svg_source(name, color)
    except OSError:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        _CACHE[key] = pixmap
        return pixmap
    svg = svg.replace("currentColor", color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    pixmap = QPixmap.fromImage(image)
    _CACHE[key] = pixmap
    return pixmap


def icon_pixmap(name, size=24, color="#ededf5"):
    return _render_pixmap(name, size, color)


def icon(name, size=24, color="#ededf5"):
    return QIcon(_render_pixmap(name, size, color))
