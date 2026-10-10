import math

from PySide6.QtCore import (
    QEasingCurve, QPointF, QPropertyAnimation, QRect, QRectF, QSize, Qt, QTimer, Signal,
)
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QRadialGradient
from PySide6.QtMultimedia import QVideoFrame, QVideoSink
from PySide6.QtWidgets import (
    QHBoxLayout, QPushButton, QSlider, QStyle, QStyleOptionSlider, QWidget,
)

from .icons import make_icon
from .styles import BG, MUTED, TEXT


class IconButton(QPushButton):

    def __init__(self, icon_name: str, tooltip: str = "", icon_size: int = 20,
                 object_name: str = "ghost", color: str = TEXT, parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._icon_size = icon_size
        self._color = color
        self.set_icon(icon_name)

    def set_icon(self, icon_name: str) -> None:
        self.setIcon(make_icon(icon_name, self._color, self._icon_size))
        self.setIconSize(QSize(self._icon_size, self._icon_size))


class SeekSlider(QSlider):

    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            option = QStyleOptionSlider()
            self.initStyleOption(option)
            handle = self.style().subControlRect(
                QStyle.ComplexControl.CC_Slider, option, QStyle.SubControl.SC_SliderHandle, self
            )
            if not handle.contains(event.position().toPoint()):
                value = QStyle.sliderValueFromPosition(
                    self.minimum(), self.maximum(), int(event.position().x()), self.width()
                )
                self.setValue(value)
                self.sliderMoved.emit(value)
        super().mousePressEvent(event)


class SourceMenu(QWidget):

    file_requested = Signal()
    url_requested = Signal()

    def __init__(self, file_tooltip: str, url_tooltip: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.plus_button = IconButton("plus", "Open…")
        layout.addWidget(self.plus_button)

        self.drawer = QWidget()
        drawer_layout = QHBoxLayout(self.drawer)
        drawer_layout.setContentsMargins(0, 0, 0, 0)
        drawer_layout.setSpacing(6)
        file_button = IconButton("folder", file_tooltip, 16, "pill")
        file_button.setText(" File")
        url_button = IconButton("link", url_tooltip, 16, "pill")
        url_button.setText(" URL")
        drawer_layout.addWidget(file_button)
        drawer_layout.addWidget(url_button)
        layout.addWidget(self.drawer)
        layout.addStretch()

        self.drawer.setMaximumWidth(0)
        self._animation = QPropertyAnimation(self.drawer, b"maximumWidth", self)
        self._animation.setDuration(220)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._close_timer = QTimer(self, singleShot=True, interval=350)
        self._close_timer.timeout.connect(lambda: self._slide(open_=False))

        self.plus_button.clicked.connect(lambda: self._slide(open_=True))
        file_button.clicked.connect(self.file_requested)
        url_button.clicked.connect(self.url_requested)

    def _slide(self, open_: bool) -> None:
        self._animation.stop()
        self._animation.setStartValue(self.drawer.maximumWidth())
        self._animation.setEndValue(self.drawer.sizeHint().width() if open_ else 0)
        self._animation.start()

    def enterEvent(self, event):
        self._close_timer.stop()
        self._slide(open_=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._close_timer.start()
        super().leaveEvent(event)


class VideoCanvas(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sink = QVideoSink(self)
        self.sink.videoFrameChanged.connect(self._on_frame)
        self._image = QImage()

    def clear(self) -> None:
        self._image = QImage()
        self.update()

    def _on_frame(self, frame: QVideoFrame) -> None:
        if frame.isValid():
            self._image = frame.toImage()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#000000"))
        if self._image.isNull():
            return
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        size = self._image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        target = QRect(0, 0, size.width(), size.height())
        target.moveCenter(self.rect().center())
        painter.drawImage(target, self._image)


class Visualizer(QWidget):

    def __init__(self, bands: int = 48, parent=None):
        super().__init__(parent)
        self._bands = bands
        self._target = [0.0] * bands
        self._levels = [0.0] * bands
        self._phase = 0.0
        self._hint = ""
        self._bottom_inset = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)


    def set_levels(self, levels: list) -> None:
        self._target = levels

    def set_active(self, active: bool) -> None:
        if not active:
            self._target = [0.0] * self._bands

    def set_bottom_inset(self, inset: int) -> None:
        self._bottom_inset = inset
        self.update()

    def set_hint(self, text: str) -> None:
        self._hint = text
        self.update()


    def _tick(self) -> None:
        self._phase += 0.02
        for i, target in enumerate(self._target):
            current = self._levels[i]
            speed = 0.5 if target > current else 0.08
            self._levels[i] = current + (target - current) * speed
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(BG))

        w = self.width()
        h = max(1, self.height() - self._bottom_inset - (40 if self._hint else 0))
        center = QPointF(w / 2, h / 2)
        base = min(w, h) * 0.15
        energy = sum(self._levels) / self._bands
        breathing = 0.04 * math.sin(self._phase * 1.5)
        radius = base * (1 + breathing + energy * 0.35)

        self._paint_glow(painter, center, radius, energy)
        self._paint_bars(painter, center, radius)
        self._paint_orb(painter, center, radius)
        if self._hint:
            self._paint_hint(painter)

    def _paint_glow(self, painter, center, radius, energy):
        glow = QRadialGradient(center, radius * 3.2)
        glow.setColorAt(0.0, QColor(255, 255, 255, int(18 + energy * 50)))
        glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(center, radius * 3.2, radius * 3.2)

    def _paint_bars(self, painter, center, radius):
        count = self._bands * 2
        for i in range(count):
            band = i if i < self._bands else count - 1 - i
            level = self._levels[band]
            idle = 0.05 + 0.03 * math.sin(self._phase * 2 + i * 0.4)
            length = radius * (0.12 + max(level, idle) * 1.1)

            angle = -math.pi / 2 + 2 * math.pi * i / count
            direction = QPointF(math.cos(angle), math.sin(angle))
            start = center + direction * (radius * 1.18)
            end = center + direction * (radius * 1.18 + length)

            color = QColor(255, 255, 255, int(255 * (0.35 + 0.6 * level)))
            painter.setPen(QPen(color, max(2.0, radius * 0.045), Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap))
            painter.drawLine(start, end)

    def _paint_orb(self, painter, center, radius):
        orb = QRadialGradient(center + QPointF(-radius * 0.35, -radius * 0.45), radius * 1.7)
        orb.setColorAt(0.0, QColor("#fafafa"))
        orb.setColorAt(0.45, QColor("#a1a1aa"))
        orb.setColorAt(1.0, QColor("#3f3f46"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(orb)
        painter.drawEllipse(center, radius, radius)

    def _paint_hint(self, painter):
        font = QFont(self.font())
        font.setPointSize(13)
        painter.setFont(font)
        painter.setPen(QColor(MUTED))
        rect = QRectF(0, self.height() - self._bottom_inset - 46, self.width(), 30)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._hint)
