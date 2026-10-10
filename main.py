import sys

from PySide6.QtWidgets import QApplication

from player.styles import STYLESHEET
from player.window import PlayerWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Media Player")
    app.setStyleSheet(STYLESHEET)

    window = PlayerWindow()
    app.aboutToQuit.connect(window.player.stop)
    window.show()
    if len(sys.argv) > 1:
        window.load_source(sys.argv[1])
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
