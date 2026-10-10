from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_FILL = 'fill="currentColor"'
_STROKE = 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'

_ICONS = {
    "play": f'<path {_FILL} d="M8 5.14v13.72a1 1 0 0 0 1.52.85l10.6-6.86a1 1 0 0 0 0-1.7L9.52 4.29A1 1 0 0 0 8 5.14z"/>',
    "pause": f'<rect {_FILL} x="6" y="5" width="4" height="14" rx="1.3"/>'
             f'<rect {_FILL} x="14" y="5" width="4" height="14" rx="1.3"/>',
    "stop": f'<rect {_FILL} x="6" y="6" width="12" height="12" rx="2.5"/>',
    "back": f'<path {_FILL} stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" d="M11 6.5v11L3 12zM20.5 6.5v11l-8-5.5z"/>',
    "forward": f'<path {_FILL} stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" d="M3.5 6.5v11l8-5.5zM13 6.5v11l8-5.5z"/>',
    "volume": f'<path {_FILL} d="M4 9.5v5a1 1 0 0 0 1 1h3l4.4 3.6a.6.6 0 0 0 1-.47V5.37a.6.6 0 0 0-1-.47L8 8.5H5a1 1 0 0 0-1 1z"/>'
              f'<path {_STROKE} d="M16.5 9a4.2 4.2 0 0 1 0 6M19 6.5a7.8 7.8 0 0 1 0 11"/>',
    "mute": f'<path {_FILL} d="M4 9.5v5a1 1 0 0 0 1 1h3l4.4 3.6a.6.6 0 0 0 1-.47V5.37a.6.6 0 0 0-1-.47L8 8.5H5a1 1 0 0 0-1 1z"/>'
            f'<path {_STROKE} d="M16.5 9.5l5 5M21.5 9.5l-5 5"/>',
    "folder": f'<path {_STROKE} d="M3 7.5A2.5 2.5 0 0 1 5.5 5h3.6l2 2.2h7.4A2.5 2.5 0 0 1 21 9.7v7.8a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 17.5z"/>',
    "link": f'<path {_STROKE} d="M10 14a4 4 0 0 0 5.66 0l3-3a4 4 0 0 0-5.66-5.66l-1 1"/>'
            f'<path {_STROKE} d="M14 10a4 4 0 0 0-5.66 0l-3 3a4 4 0 0 0 5.66 5.66l1-1"/>',
    "plus": f'<path {_STROKE} d="M12 5v14M5 12h14"/>',
    "fullscreen": f'<path {_STROKE} d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
}


def make_icon(name: str, color: str = "#ecebf5", size: int = 24) -> QIcon:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" color="{color}">'
        f"{_ICONS[name]}</svg>"
    )
    renderer = QSvgRenderer(QByteArray(svg.encode()))

    scale = 3
    pixmap = QPixmap(size * scale, size * scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size * scale, size * scale))
    painter.end()
    pixmap.setDevicePixelRatio(scale)
    return QIcon(pixmap)
