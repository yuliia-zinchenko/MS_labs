from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QRect, Qt, QTimer, QUrl
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtMultimedia import QAudio, QAudioOutput, QMediaMetaData, QMediaPlayer
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QInputDialog, QLineEdit, QMainWindow,
    QMessageBox, QStackedWidget, QWidget,
)

from .analyzer import SpectrumAnalyzer
from .controls import ControlBar, native_keys
from .utils import (
    describe_source, display_name, file_dialog_filter, format_time, parse_stream_url, to_qurl,
)
from .widgets import Visualizer, VideoCanvas

SEEK_STEP_MS = 10_000
KEY_SEEK_STEP_MS = 5_000
VOLUME_STEP = 5
IDLE_HIDE_MS = 5_000

CONTROLS_MARGIN = 16
CONTROLS_MAX_WIDTH = 980

SCREEN_VISUALIZER, SCREEN_VIDEO = 0, 1

ERROR_MESSAGES = {
    QMediaPlayer.Error.ResourceError:
        "Could not open the source. Check that the file exists, the link is correct "
        "and the server is reachable.",
    QMediaPlayer.Error.FormatError: "The format of this file or stream is not supported.",
    QMediaPlayer.Error.NetworkError: "Network error. Check your internet connection.",
    QMediaPlayer.Error.AccessDeniedError: "Access to the resource is denied.",
}

ACTIVITY_EVENTS = {
    QEvent.Type.MouseMove, QEvent.Type.HoverMove, QEvent.Type.MouseButtonPress,
    QEvent.Type.Wheel, QEvent.Type.KeyPress,
}


class PlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Player")
        self.resize(1000, 640)
        self.setMinimumSize(760, 460)
        self.setAcceptDrops(True)

        self._source = QUrl()
        self._user_seeking = False
        self._volume_before_mute = 70

        self._build_player()
        self._build_ui()
        self._build_autohide()
        self._connect_signals()
        self._build_shortcuts()

        self.controls.volume_slider.setValue(self._volume_before_mute)
        self._reset_now_playing()


    def _build_player(self) -> None:
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self.analyzer = SpectrumAnalyzer(parent=self)
        self.player.setAudioBufferOutput(self.analyzer.output)

    def _build_ui(self) -> None:
        self.stage = QWidget(objectName="stage")
        self.setCentralWidget(self.stage)

        self.screens = QStackedWidget(self.stage)
        self.visualizer = Visualizer()
        self.video_canvas = VideoCanvas()
        self.player.setVideoSink(self.video_canvas.sink)
        self.screens.addWidget(self.visualizer)
        self.screens.addWidget(self.video_canvas)

        self.controls = ControlBar(self.stage)
        self.controls.raise_()

        for widget in (self.stage, self.screens, self.visualizer, self.video_canvas):
            widget.setMouseTracking(True)
        self.visualizer.installEventFilter(self)
        self.video_canvas.installEventFilter(self)

    def _build_autohide(self) -> None:
        self._controls_shown = True
        self._slide = QPropertyAnimation(self.controls, b"pos", self)
        self._slide.setDuration(320)
        self._slide.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._slide.finished.connect(self._on_slide_finished)

        self._idle_timer = QTimer(self, singleShot=True, interval=IDLE_HIDE_MS)
        self._idle_timer.timeout.connect(self._hide_controls)

        self.stage.installEventFilter(self)
        QApplication.instance().installEventFilter(self)

    def _connect_signals(self) -> None:
        c = self.controls

        c.source_menu.file_requested.connect(self.open_file)
        c.source_menu.url_requested.connect(self.open_url)
        c.play_button.clicked.connect(self.toggle_play)
        c.stop_button.clicked.connect(self.player.stop)
        c.back_button.clicked.connect(lambda: self.seek_by(-SEEK_STEP_MS))
        c.forward_button.clicked.connect(lambda: self.seek_by(SEEK_STEP_MS))
        c.mute_button.clicked.connect(self.toggle_mute)
        c.fullscreen_button.clicked.connect(self.toggle_fullscreen)

        c.seek_slider.sliderPressed.connect(self._on_seek_pressed)
        c.seek_slider.sliderMoved.connect(self._on_seek_moved)
        c.seek_slider.sliderReleased.connect(self._on_seek_released)
        c.volume_slider.valueChanged.connect(self._on_volume_changed)

        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.hasVideoChanged.connect(self._on_has_video_changed)
        self.player.metaDataChanged.connect(self._update_title)
        self.player.seekableChanged.connect(c.seek_slider.setEnabled)
        self.player.errorOccurred.connect(self._on_error)
        self.analyzer.levels_ready.connect(self.visualizer.set_levels)

    def _build_shortcuts(self) -> None:
        volume = self.controls.volume_slider
        bindings = {
            "Space": self.toggle_play,
            "S": self.player.stop,
            "Left": lambda: self.seek_by(-KEY_SEEK_STEP_MS),
            "Right": lambda: self.seek_by(KEY_SEEK_STEP_MS),
            "Up": lambda: volume.setValue(volume.value() + VOLUME_STEP),
            "Down": lambda: volume.setValue(volume.value() - VOLUME_STEP),
            "M": self.toggle_mute,
            "F": self.toggle_fullscreen,
            "Escape": lambda: self.isFullScreen() and self.toggle_fullscreen(),
            "Ctrl+O": self.open_file,
            "Ctrl+L": self.open_url,
        }
        for keys, handler in bindings.items():
            QShortcut(QKeySequence(keys), self, activated=handler)


    def open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open media file", "", file_dialog_filter())
        if path:
            self.load(QUrl.fromLocalFile(path))

    def open_url(self) -> None:
        text = "https://"
        while True:
            text, ok = QInputDialog.getText(
                self, "Open URL", "Link to audio, video or a stream (http, https, rtsp…):",
                QLineEdit.EchoMode.Normal, text,
            )
            if not ok:
                return
            url, problem = parse_stream_url(text)
            if url is not None:
                self.load(url)
                return
            QMessageBox.warning(self, "Invalid link", problem)

    def load_source(self, source: str) -> None:
        self.load(to_qurl(source))

    def load(self, url: QUrl) -> None:
        self._source = url
        self.video_canvas.clear()
        self.player.setSource(url)
        self.controls.title_label.setText(display_name(url))
        self.controls.subtitle_label.setText(describe_source(url))
        self.visualizer.set_hint("")
        self.player.play()


    def toggle_play(self) -> None:
        if self._source.isEmpty():
            self.open_file()
        elif self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def seek_by(self, delta_ms: int) -> None:
        if not self.player.isSeekable():
            return
        target = self.player.position() + delta_ms
        self.player.setPosition(max(0, min(target, self.player.duration())))

    def toggle_mute(self) -> None:
        self.audio_output.setMuted(not self.audio_output.isMuted())
        self._update_volume_icon()

    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()


    def _is_playing(self) -> bool:
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _on_activity(self) -> None:
        if not self._controls_shown:
            self._controls_shown = True
            self.controls.show()
            self.stage.unsetCursor()
            self._animate_controls()
        if self._is_playing():
            self._idle_timer.start()

    def _hide_controls(self) -> None:
        if not self._is_playing() or self.controls.underMouse():
            self._idle_timer.start()
            return
        self._controls_shown = False
        self.stage.setCursor(Qt.CursorShape.BlankCursor)
        self._animate_controls()

    def _controls_rect(self) -> QRect:
        rect = self.stage.rect()
        width = min(rect.width() - 2 * CONTROLS_MARGIN, CONTROLS_MAX_WIDTH)
        height = self.controls.sizeHint().height()
        y = rect.height() - height - CONTROLS_MARGIN if self._controls_shown else rect.height()
        return QRect((rect.width() - width) // 2, y, width, height)

    def _animate_controls(self) -> None:
        self._slide.stop()
        self._slide.setStartValue(self.controls.pos())
        self._slide.setEndValue(self._controls_rect().topLeft())
        self._slide.start()

    def _on_slide_finished(self) -> None:
        if not self._controls_shown:
            self.controls.hide()

    def _layout_overlay(self) -> None:
        self._slide.stop()
        self.screens.setGeometry(self.stage.rect())
        self.controls.setGeometry(self._controls_rect())
        self.visualizer.set_bottom_inset(self.controls.sizeHint().height() + CONTROLS_MARGIN)


    def _on_seek_pressed(self) -> None:
        self._user_seeking = True

    def _on_seek_moved(self, value: int) -> None:
        self.controls.position_label.setText(format_time(value))

    def _on_seek_released(self) -> None:
        self._user_seeking = False
        self.player.setPosition(self.controls.seek_slider.value())

    def _on_volume_changed(self, value: int) -> None:
        linear = QAudio.convertVolume(
            value / 100,
            QAudio.VolumeScale.LogarithmicVolumeScale,
            QAudio.VolumeScale.LinearVolumeScale,
        )
        self.audio_output.setVolume(linear)
        if value > 0 and self.audio_output.isMuted():
            self.audio_output.setMuted(False)
        self._update_volume_icon()

    def _update_volume_icon(self) -> None:
        muted = self.audio_output.isMuted() or self.controls.volume_slider.value() == 0
        self.controls.mute_button.set_icon("mute" if muted else "volume")


    def _on_position_changed(self, position: int) -> None:
        if not self._user_seeking:
            self.controls.seek_slider.setValue(position)
            self.controls.position_label.setText(format_time(position))

    def _on_duration_changed(self, duration: int) -> None:
        self.controls.seek_slider.setRange(0, duration)
        self.controls.duration_label.setText(format_time(duration) if duration > 0 else "LIVE")

    def _on_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.controls.play_button.set_icon("pause" if playing else "play")
        self.visualizer.set_active(playing)
        self._on_activity()

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        Status = QMediaPlayer.MediaStatus
        subtitle = self.controls.subtitle_label
        if status in (Status.LoadingMedia, Status.StalledMedia):
            subtitle.setText("Loading…")
        elif status == Status.BufferingMedia:
            subtitle.setText("Buffering…")
        elif status in (Status.LoadedMedia, Status.BufferedMedia):
            subtitle.setText(describe_source(self._source))
        elif status == Status.EndOfMedia:
            self.player.setPosition(0)

    def _on_has_video_changed(self, has_video: bool) -> None:
        self.screens.setCurrentIndex(SCREEN_VIDEO if has_video else SCREEN_VISUALIZER)

    def _update_title(self) -> None:
        if self._source.isEmpty():
            return
        meta = self.player.metaData()
        title = meta.stringValue(QMediaMetaData.Key.Title)
        artist = meta.stringValue(QMediaMetaData.Key.ContributingArtist) or \
            meta.stringValue(QMediaMetaData.Key.AlbumArtist)
        self.controls.title_label.setText(title or display_name(self._source))
        if artist:
            self.controls.subtitle_label.setText(f"{artist} · {describe_source(self._source)}")

    def _on_error(self, error: QMediaPlayer.Error, message: str) -> None:
        if error == QMediaPlayer.Error.NoError:
            return
        failed = self._source
        self._source = QUrl()
        self.player.setSource(QUrl())
        self._reset_now_playing()

        explanation = ERROR_MESSAGES.get(error, "Could not play the media.")
        box = QMessageBox(QMessageBox.Icon.Warning, "Playback error", explanation,
                          parent=self)
        box.setInformativeText(failed.toDisplayString())
        if message:
            box.setDetailedText(message)
        box.exec()

    def _reset_now_playing(self) -> None:
        c = self.controls
        c.title_label.setText("Nothing playing")
        c.subtitle_label.setText("")
        c.position_label.setText(format_time(0))
        c.duration_label.setText(format_time(0))
        c.seek_slider.setRange(0, 0)
        self.video_canvas.clear()
        self.screens.setCurrentIndex(SCREEN_VISUALIZER)
        self.visualizer.set_hint(
            f"Drop a file here, press {native_keys('Ctrl+O')} or use \"+\" below"
        )


    def eventFilter(self, watched, event):
        kind = event.type()
        if kind in ACTIVITY_EVENTS and self.isActiveWindow():
            self._on_activity()
        if watched is self.stage and kind == QEvent.Type.Resize:
            self._layout_overlay()
        elif watched in (self.visualizer, self.video_canvas) and \
                kind == QEvent.Type.MouseButtonDblClick:
            self.toggle_fullscreen()
            return True
        return super().eventFilter(watched, event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self.load(urls[0])

    def closeEvent(self, event):
        QApplication.instance().removeEventFilter(self)
        self.player.stop()
        super().closeEvent(event)
