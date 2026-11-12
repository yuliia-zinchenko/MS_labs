BG = "#0b0b0c"
SURFACE = "#18181b"
TEXT = "#f4f4f5"
MUTED = "#a1a1aa"
GRID = "#3f3f46"
DCT_COLOR = "#60a5fa"
DWT_COLOR = "#f59e0b"

STYLESHEET = f"""
QMainWindow, QWidget#root {{ background: {BG}; }}

QLabel {{ color: {TEXT}; background: transparent; font-size: 13px; }}
QLabel#muted {{ color: {MUTED}; }}
QLabel#title {{ font-size: 15px; font-weight: 600; }}
QLabel#metric {{ color: {MUTED}; font-family: Consolas, Menlo, monospace; font-size: 12px; }}

QFrame#panel {{
    background: {SURFACE};
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
}}

QPushButton {{
    color: {TEXT};
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 6px 14px;
    font-size: 13px;
}}
QPushButton:hover {{ background: rgba(255, 255, 255, 0.14); }}
QPushButton:pressed {{ background: rgba(255, 255, 255, 0.20); }}

QSpinBox {{
    color: {TEXT};
    background: #232327;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 8px;
    padding: 4px 8px;
}}

QSlider {{ background: transparent; }}
QSlider::groove:horizontal {{
    height: 4px;
    background: rgba(255, 255, 255, 0.16);
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{ background: {TEXT}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: #ffffff;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

QMessageBox {{ background: {SURFACE}; }}
"""
