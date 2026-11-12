import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

from .styles import BG, DCT_COLOR, DWT_COLOR, GRID, MUTED, SURFACE, TEXT


def to_qimage(image: np.ndarray) -> QImage:
    data = np.ascontiguousarray(image)
    h, w = data.shape
    return QImage(data.data, w, h, w, QImage.Format.Format_Grayscale8).copy()


class ImageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = QImage()
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_image(self, image: np.ndarray) -> None:
        self._image = to_qimage(image)
        self.update()

    def paintEvent(self, event):
        if self._image.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        scale = min(self.width() / self._image.width(), self.height() / self._image.height())
        w, h = self._image.width() * scale, self._image.height() * scale
        painter.drawImage(QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h), self._image)


class ImagePanel(QFrame):

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)

        self.title = QLabel(title)
        self.title.setObjectName("title")
        self.view = ImageView()
        self.metrics = QLabel()
        self.metrics.setObjectName("metric")
        self.metrics.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout.addWidget(self.title)
        layout.addWidget(self.view, 1)
        layout.addWidget(self.metrics)

    def show_image(self, image: np.ndarray, metrics: str) -> None:
        self.view.set_image(image)
        self.metrics.setText(metrics)


class PsnrChart(FigureCanvasQTAgg):

    def __init__(self, parent=None):
        super().__init__(Figure(figsize=(8, 2.4), facecolor=SURFACE, layout="constrained"))
        self.setParent(parent)
        self.setMinimumHeight(200)
        self.axes = self.figure.add_subplot()
        self._marker = None

    def plot(self, percents, dct_psnr, dwt_psnr) -> None:
        ax = self.axes
        ax.clear()
        ax.set_facecolor(BG)
        ax.plot(percents, dct_psnr, color=DCT_COLOR, lw=2, label="DCT 8×8")
        ax.plot(percents, dwt_psnr, color=DWT_COLOR, lw=2, label="DWT Haar")
        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
        ax.set_xlabel("Kept coefficients, %", color=MUTED)
        ax.set_ylabel("PSNR, dB", color=MUTED)
        ax.tick_params(colors=MUTED)
        ax.grid(True, which="both", color=GRID, lw=0.5)
        for spine in ax.spines.values():
            spine.set_color(GRID)
        ax.legend(facecolor=SURFACE, edgecolor=GRID, labelcolor=TEXT, loc="lower right")
        self._marker = ax.axvline(percents[0], color=TEXT, lw=1, ls="--")
        self.draw_idle()

    def mark(self, percent: float) -> None:
        if self._marker is not None:
            self._marker.set_xdata([percent, percent])
            self.draw_idle()
