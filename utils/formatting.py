"""utils/formatting.py — Bold / italic / underline toggle helpers and cursor-sync utilities."""
from aqt.qt import QFont, QTextCharFormat

from ..config import get_config, save_config
from .. import state


# Toggle helpers

def _toggle_format(format_type: str, btn_attr: str, cfg_key: str) -> None:
    """Generic handler for bold / italic / underline toolbar buttons."""
    if not (state.editor and state.pane):
        return

    btn = getattr(state.pane.toolbar(), btn_attr)
    btn.setChecked(not btn.isChecked())

    fmt = QTextCharFormat()
    if format_type == "bold":
        fmt.setFontWeight(QFont.Weight.Bold if btn.isChecked() else QFont.Weight.Normal)
    elif format_type == "italic":
        fmt.setFontItalic(btn.isChecked())
    elif format_type == "underline":
        fmt.setFontUnderline(btn.isChecked())

    state.editor.mergeCurrentCharFormat(fmt)

    cfg = get_config()
    if cfg.get("remember_formatting", True):
        cfg[cfg_key] = btn.isChecked()
        save_config(cfg)


def toggle_bold() -> None:
    _toggle_format("bold", "_btn_bold", "formatting_bold")


def toggle_italic() -> None:
    _toggle_format("italic", "_btn_italic", "formatting_italic")


def toggle_underline() -> None:
    _toggle_format("underline", "_btn_underline", "formatting_underline")


# ── State sync ────────────────────────────────────────────────────────────────

def sync_format_buttons() -> None:
    """Sync toolbar checked states with the cursor's current char format.
    Used when remember_formatting is disabled so buttons track the selection."""
    if not (state.editor and state.pane):
        return
    fmt = state.editor.currentCharFormat()
    tb  = state.pane.toolbar()
    for btn, active in (
        (tb._btn_bold,      fmt.fontWeight() == QFont.Weight.Bold),
        (tb._btn_italic,    fmt.fontItalic()),
        (tb._btn_underline, fmt.fontUnderline()),
    ):
        if btn.isChecked() != active:
            btn.blockSignals(True)
            btn.setChecked(active)
            btn.blockSignals(False)


def restore_formatting_state() -> None:
    """Restore button checked states from saved config on startup."""
    if not state.pane:
        return
    cfg = get_config()
    if not cfg.get("remember_formatting", True):
        return
    tb = state.pane.toolbar()
    tb._btn_bold.setChecked(cfg.get("formatting_bold", False))
    tb._btn_italic.setChecked(cfg.get("formatting_italic", False))
    tb._btn_underline.setChecked(cfg.get("formatting_underline", False))


def apply_saved_formatting() -> None:
    """Apply the saved format state to the current cursor position.
    Called on key-press and focus-in so new typing inherits the saved format."""
    if not state.editor:
        return
    cfg = get_config()
    if not cfg.get("remember_formatting", True):
        return
    fmt = QTextCharFormat()
    if cfg.get("formatting_bold", False):
        fmt.setFontWeight(QFont.Weight.Bold)
    if cfg.get("formatting_italic", False):
        fmt.setFontItalic(True)
    if cfg.get("formatting_underline", False):
        fmt.setFontUnderline(True)
    state.editor.setCurrentCharFormat(fmt)
