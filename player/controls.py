from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .styles import BG
from .widgets import IconButton, SeekSlider, SourceMenu

SIDE_WIDTH = 210


def native_keys(keys: str) -> str:
    return QKeySequence(keys).toString(QKeySequence.SequenceFormat.NativeText)


class ControlBar(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controls")
        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 10)
        layout.setSpacing(6)
        layout.addLayout(self._build_info_row())
        layout.addLayout(self._build_progress_row())
        layout.addLayout(self._build_buttons_row())

    def _build_info_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        self.title_label = QLabel(objectName="title")
        self.subtitle_label = QLabel(objectName="subtitle")
        row.addWidget(self.title_label)
        row.addWidget(self.subtitle_label)
        row.addStretch()
        return row

    def _build_progress_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        self.position_label = QLabel("0:00", objectName="time")
        self.duration_label = QLabel("0:00", objectName="time")
        self.seek_slider = SeekSlider()
        self.seek_slider.setEnabled(False)
        row.addWidget(self.position_label)
        row.addWidget(self.seek_slider, stretch=1)
        row.addWidget(self.duration_label)
        return row

    def _build_buttons_row(self) -> QHBoxLayout:
        self.source_menu = SourceMenu(
            f"Open file ({native_keys('Ctrl+O')})",
            f"Open URL ({native_keys('Ctrl+L')})",
        )

        self.stop_button = IconButton("stop", "Stop (S)", 18)
        self.back_button = IconButton("back", "Back 10 s (←: 5 s)")
        self.play_button = IconButton("play", "Play / Pause (Space)", 22, "play", color=BG)
        self.play_button.setFixedSize(48, 48)
        self.forward_button = IconButton("forward", "Forward 10 s (→: 5 s)")

        transport = QHBoxLayout()
        transport.setSpacing(12)
        for button in (self.stop_button, self.back_button, self.play_button, self.forward_button):
            transport.addWidget(button)
        twin = QWidget()
        twin.setFixedSize(self.stop_button.sizeHint())
        transport.addWidget(twin)

        self.mute_button = IconButton("volume", "Mute (M)", 18)
        self.volume_slider = SeekSlider()
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setFixedWidth(90)
        self.volume_slider.setToolTip("Volume (↑ / ↓)")
        self.fullscreen_button = IconButton("fullscreen", "Fullscreen (F)", 18)

        right = QWidget()
        right_layout = QHBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)
        right_layout.addStretch()
        right_layout.addWidget(self.mute_button)
        right_layout.addWidget(self.volume_slider)
        right_layout.addSpacing(8)
        right_layout.addWidget(self.fullscreen_button)

        for side in (self.source_menu, right):
            side.setFixedWidth(SIDE_WIDTH)

        row = QHBoxLayout()
        row.addWidget(self.source_menu, alignment=Qt.AlignmentFlag.AlignVCenter)
        row.addStretch()
        row.addLayout(transport)
        row.addStretch()
        row.addWidget(right)
        return row
