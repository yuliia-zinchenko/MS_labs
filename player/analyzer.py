import numpy as np
from PySide6.QtCore import QObject, Signal
from PySide6.QtMultimedia import QAudioBuffer, QAudioBufferOutput, QAudioFormat

SAMPLE_RATE = 44100
FFT_SIZE = 2048
MIN_FREQ, MAX_FREQ = 40, 16000
DB_FLOOR = -70.0


class SpectrumAnalyzer(QObject):

    levels_ready = Signal(list)

    def __init__(self, bands: int = 48, parent=None):
        super().__init__(parent)

        fmt = QAudioFormat()
        fmt.setSampleRate(SAMPLE_RATE)
        fmt.setChannelCount(1)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Float)
        self.output = QAudioBufferOutput(fmt, self)
        self.output.audioBufferReceived.connect(self._on_buffer)

        self._samples = np.zeros(FFT_SIZE, dtype=np.float32)
        self._window = np.hanning(FFT_SIZE).astype(np.float32)

        freqs = np.fft.rfftfreq(FFT_SIZE, 1 / SAMPLE_RATE)
        edges = np.geomspace(MIN_FREQ, MAX_FREQ, bands + 1)
        starts = np.searchsorted(freqs, edges[:-1])
        stops = np.maximum(starts + 1, np.searchsorted(freqs, edges[1:]))
        self._band_slices = [slice(a, b) for a, b in zip(starts, stops)]

    def _on_buffer(self, buffer: QAudioBuffer) -> None:
        chunk = np.frombuffer(bytes(buffer.constData()), dtype=np.float32)
        if chunk.size == 0:
            return

        chunk = chunk[-FFT_SIZE:]
        self._samples = np.roll(self._samples, -chunk.size)
        self._samples[-chunk.size:] = chunk

        spectrum = np.abs(np.fft.rfft(self._samples * self._window)) / (FFT_SIZE / 2)
        levels = []
        for band in self._band_slices:
            magnitude = spectrum[band].max()
            db = 20 * np.log10(magnitude + 1e-9)
            levels.append(float(np.clip((db - DB_FLOOR) / -DB_FLOOR, 0.0, 1.0)))
        self.levels_ready.emit(levels)
