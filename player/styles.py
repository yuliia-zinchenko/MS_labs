BG = "#0b0b0c"
SURFACE = "#18181b"
TEXT = "#f4f4f5"
MUTED = "#a1a1aa"
ACCENT = "#f4f4f5"

STYLESHEET = f"""
QWidget#stage {{ background: {BG}; }}

QLabel {{ color: {TEXT}; background: transparent; }}
QLabel#title {{ font-size: 15px; font-weight: 600; }}
QLabel#subtitle {{ color: {MUTED}; font-size: 12px; }}
QLabel#time {{ color: {MUTED}; font-size: 12px; font-family: Menlo, Consolas, monospace; }}

QFrame#controls {{
    background: rgba(24, 24, 27, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
}}

QPushButton {{
    color: {TEXT};
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 6px 12px;
    font-size: 13px;
}}
QPushButton:hover {{ background: rgba(255, 255, 255, 0.14); }}
QPushButton:pressed {{ background: rgba(255, 255, 255, 0.20); }}

QPushButton#ghost {{
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 6px;
}}
QPushButton#ghost:hover {{ background: rgba(255, 255, 255, 0.10); }}
QPushButton#ghost:pressed {{ background: rgba(255, 255, 255, 0.16); }}

QPushButton#pill {{
    background: rgba(255, 255, 255, 0.08);
    border: none;
    border-radius: 10px;
    padding: 6px 10px;
}}
QPushButton#pill:hover {{ background: rgba(255, 255, 255, 0.16); }}

QPushButton#play {{
    border: none;
    border-radius: 24px;
    padding: 0;
    background: {ACCENT};
}}
QPushButton#play:hover {{ background: #ffffff; }}
QPushButton#play:pressed {{ background: #d4d4d8; }}

QSlider {{ background: transparent; }}
QSlider::groove:horizontal {{
    height: 4px;
    background: rgba(255, 255, 255, 0.16);
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: #ffffff;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
QSlider::handle:horizontal:hover {{
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

QDialog, QMessageBox, QInputDialog {{ background: {SURFACE}; }}
QLineEdit {{
    color: {TEXT};
    background: #232327;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 10px;
    padding: 8px 10px;
    min-width: 420px;
    selection-background-color: #52525b;
}}
QLineEdit:focus {{ border: 1px solid rgba(255, 255, 255, 0.40); }}

QToolTip {{
    color: {TEXT};
    background: {SURFACE};
    border: 1px solid rgba(255, 255, 255, 0.10);
    padding: 4px 8px;
}}
"""
