import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from viewer.styles import STYLESHEET
from viewer.window import CompressionWindow

DEFAULT_IMAGE = Path(__file__).parent / "samples" / "swan.png"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("DCT vs DWT")
    app.setStyleSheet(STYLESHEET)

    window = CompressionWindow()
    window.show()
    window.load_image(sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_IMAGE))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
