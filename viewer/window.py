from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton,
    QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from codec import haar
from codec.pipeline import Codec, Result, load_grayscale

from .widgets import ImagePanel, PsnrChart

SLIDER_STEPS = 1000
MIN_PERCENT = 0.1
DEFAULT_PERCENT = 5.0
DEFAULT_LEVELS = 5
MAX_LEVELS = 8
CHART_PERCENTS = np.geomspace(MIN_PERCENT, 100, 25)
IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"


def slider_to_percent(value: int) -> float:
    return MIN_PERCENT * (100 / MIN_PERCENT) ** (value / SLIDER_STEPS)


def percent_to_slider(percent: float) -> int:
    return round(SLIDER_STEPS * np.log(percent / MIN_PERCENT) / np.log(100 / MIN_PERCENT))


def describe(result: Result) -> str:
    psnr = "∞" if np.isinf(result.psnr) else f"{result.psnr:.2f} dB"
    return (f"PSNR {psnr}\n"
            f"kept {result.kept:,} / {result.total:,} ({result.fraction:.2%})\n"
            f"CR ≈ {result.ratio:.1f} : 1")


class CompressionWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DCT vs DWT compression")
        self.resize(1280, 820)
        self.codec: Codec | None = None
        self.image: np.ndarray | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        open_button = QPushButton("Open image…")
        open_button.clicked.connect(self.choose_image)
        self.file_label = QLabel("no image")
        self.file_label.setObjectName("muted")

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, SLIDER_STEPS)
        self.slider.setValue(percent_to_slider(DEFAULT_PERCENT))
        self.slider.setMinimumWidth(320)
        self.slider.valueChanged.connect(self.refresh)
        self.percent_label = QLabel()
        self.percent_label.setMinimumWidth(64)

        self.levels = QSpinBox()
        self.levels.setRange(1, MAX_LEVELS)
        self.levels.setValue(DEFAULT_LEVELS)
        self.levels.valueChanged.connect(self.rebuild)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        toolbar.addWidget(open_button)
        toolbar.addWidget(self.file_label)
        toolbar.addStretch(1)
        toolbar.addWidget(QLabel("Kept coefficients"))
        toolbar.addWidget(self.slider)
        toolbar.addWidget(self.percent_label)
        toolbar.addSpacing(12)
        toolbar.addWidget(QLabel("Haar levels"))
        toolbar.addWidget(self.levels)

        self.original_panel = ImagePanel("Original")
        self.dct_panel = ImagePanel("DCT 8×8")
        self.dwt_panel = ImagePanel("DWT Haar")
        panels = QHBoxLayout()
        panels.setSpacing(12)
        for panel in (self.original_panel, self.dct_panel, self.dwt_panel):
            panels.addWidget(panel, 1)

        self.chart = PsnrChart()

        layout.addLayout(toolbar)
        layout.addLayout(panels, 1)
        layout.addWidget(self.chart)
        self.setCentralWidget(root)
        self.refresh()

    def choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open image", "", IMAGE_FILTER)
        if path:
            self.load_image(path)

    def load_image(self, path: str) -> None:
        try:
            image = load_grayscale(path)
        except OSError as error:
            QMessageBox.warning(self, "Open image", f"Could not open the image:\n{error}")
            return
        self.image = image
        h, w = image.shape
        self.file_label.setText(f"{Path(path).name}  ·  {w}×{h}")
        self.original_panel.show_image(image, f"{w}×{h} px\n{image.size:,} pixels\ngrayscale 8 bit")
        self.levels.blockSignals(True)
        self.levels.setMaximum(max(1, min(haar.max_levels(image.shape), MAX_LEVELS)))
        self.levels.blockSignals(False)
        self.rebuild()

    def rebuild(self) -> None:
        if self.image is None:
            return
        self.codec = Codec(self.image, self.levels.value())
        fractions = CHART_PERCENTS / 100
        self.chart.plot(CHART_PERCENTS,
                        [self.codec.dct(f).psnr for f in fractions],
                        [self.codec.dwt(f).psnr for f in fractions])
        self.refresh()

    def refresh(self) -> None:
        percent = slider_to_percent(self.slider.value())
        self.percent_label.setText(f"{percent:.2f} %")
        if self.codec is None:
            return
        dct_result = self.codec.dct(percent / 100)
        dwt_result = self.codec.dwt(percent / 100)
        self.dct_panel.show_image(dct_result.image, describe(dct_result))
        self.dwt_panel.show_image(dwt_result.image, describe(dwt_result))
        self.chart.mark(percent)
