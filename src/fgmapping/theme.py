"""Worksheet-style theme tokens from owner document EIE-STANDALONE-BUILD-PROMPT-01."""
from __future__ import annotations

THEMES = {
    "grey": dict(window="#d6d6d6", cells="#e7e7e7", alternate="#dcdcdc", headers="#bdbdbd", text="#141414", secondary="#454545", buttons="#cfcfcf", selection="#0b5a63", selected_text="#ffffff", accent="#0b5a63", border="#626262"),
    "dark": dict(window="#232323", cells="#1b1b1b", alternate="#262626", headers="#303030", text="#e6e6e6", secondary="#a8a8a8", buttons="#353535", selection="#3a6db3", selected_text="#ffffff", accent="#7ab8ff", border="#808080"),
    "light": dict(window="#f3f0e8", cells="#fbfaf6", alternate="#f1eee6", headers="#e4dfd2", text="#1a1a1a", secondary="#4a4a4a", buttons="#ebe7dc", selection="#164b8f", selected_text="#ffffff", accent="#164b8f", border="#76736a"),
}

def luminance(color: str) -> float:
    v = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [x / 12.92 if x <= 0.04045 else ((x + .055) / 1.055) ** 2.4 for x in v]
    return .2126*r + .7152*g + .0722*b

def contrast(a: str, b: str) -> float:
    x, y = sorted((luminance(a), luminance(b)), reverse=True)
    return (x + .05)/(y + .05)

def stylesheet(name: str) -> str:
    t = THEMES[name]
    return f"""
      QWidget {{ background: {t['window']}; color: {t['text']}; font-size: 11pt; }}
      QTableWidget, QTableView, QLineEdit {{ background: {t['cells']}; color: {t['text']}; gridline-color: {t['border']}; font-size: 15pt; }}
      QHeaderView::section {{ background: {t['headers']}; color: {t['text']}; font-size: 14pt; padding: 5px; }}
      QAbstractItemView::item:selected {{ background: {t['selection']}; color: {t['selected_text']}; }}
      QPushButton {{ background: {t['buttons']}; border: 1px solid {t['border']}; padding: 7px; }}
      QPushButton:hover {{ border: 2px solid {t['accent']}; }}
      QGroupBox {{ border: 1px solid {t['border']}; margin-top: 10px; padding: 10px; }}
      QGroupBox::title {{ subcontrol-origin: margin; left: 8px; }}
    """
