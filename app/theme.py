"""
Snapdragon AI Studio
SAI Design System

Zentrale Farben, Abstände und Schriftdefinitionen.
Alle neuen Seiten und Widgets sollen diese Datei verwenden.
"""

THEME_NAME = "SAI Dark"
THEME_VERSION = "1.0"

BG = "#101418"
PANEL = "#171d23"
PANEL_2 = "#1f2730"
PANEL_3 = "#26313d"

TEXT = "#e8edf2"
MUTED = "#9aa7b2"
SUBTLE = "#6b7682"

ACCENT = "#3b82f6"
ACCENT_HOVER = "#2563eb"

SUCCESS = "#22c55e"
WARNING = "#f59e0b"
ERROR = "#ef4444"
INFO = "#38bdf8"

SPACE_XS = 8
SPACE_SM = 16
SPACE_MD = 24
SPACE_LG = 32
SPACE_XL = 48

FONT = "Segoe UI"
FONT_MONO = "Consolas"

FONT_SIZE_XS = 8
FONT_SIZE_SM = 9
FONT_SIZE_BASE = 10
FONT_SIZE_MD = 12
FONT_SIZE_LG = 16
FONT_SIZE_XL = 22
FONT_SIZE_TITLE = 28

SIDEBAR_WIDTH = 220
BUTTON_PAD_X = 14
BUTTON_PAD_Y = 8
CARD_PAD = 16

def status_color(status: str) -> str:
    value = (status or "").lower()

    if any(word in value for word in ["installiert", "bereit", "ready", "ok", "erfolgreich"]):
        return SUCCESS

    if any(word in value for word in ["läuft", "working", "loading", "in arbeit"]):
        return INFO

    if any(word in value for word in ["geplant", "fehlt", "missing", "nicht erreichbar", "warning"]):
        return WARNING

    if any(word in value for word in ["fehler", "error", "failed"]):
        return ERROR

    return MUTED
