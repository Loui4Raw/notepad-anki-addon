"""ui/editor.py — NotepadEditor (QTextEdit) and EditorPane (container + toolbar overlay)."""
import re

from aqt.qt import (
    QWidget, QTextEdit, QFont, Qt, QTimer, QEvent, QAction,
    QTextCursor, QTextBlockFormat,
)

from ..config import get_config
from .. import state
from ..utils.formatting import apply_saved_formatting
from .toolbar import OverlayToolbar, TOOLBAR_H


class NotepadEditor(QTextEdit):
    """
    Custom QTextEdit with:
    - Plain-text paste (strips all incoming formatting)
    - Auto bullet / numbered list continuation on Enter
    - '-' → '•' conversion at line start on Space
    - Context menu with "Reset (clear all text)"
    - Saved-formatting application on key press and focus
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auto_list = True

    def set_auto_list(self, enabled: bool) -> None:
        self._auto_list = enabled

    # ── Paste as plain text ───────────────────────────────────────────────────

    def insertFromMimeData(self, source) -> None:
        self.insertPlainText(source.text())

    # ── Context menu ──────────────────────────────────────────────────────────

    def createStandardContextMenu(self):
        menu = super().createStandardContextMenu()
        menu.addSeparator()
        reset_act = QAction("Reset (clear all text)", menu)
        reset_act.triggered.connect(self.clear)
        menu.addAction(reset_act)
        return menu

    # ── Key handling ──────────────────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:
        if event.text():
            apply_saved_formatting()

        key = event.key()

        if self._auto_list and key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            line   = self.textCursor().block().text()
            bullet = re.match(r"^(\s*)[•]\s(.*)$", line)
            number = re.match(r"^(\s*)(\d+)\.\s(.*)$", line)

            if bullet:
                content, indent = bullet.group(2), bullet.group(1)
                if not content:
                    # Empty bullet — break out of list
                    self.textCursor().select(QTextCursor.SelectionType.LineUnderCursor)
                    self.textCursor().removeSelectedText()
                    super().keyPressEvent(event)
                    return
                super().keyPressEvent(event)
                self.textCursor().insertText(f"{indent}• ")
                self._add_list_spacing()
                return

            if number:
                content, indent = number.group(3), number.group(1)
                if not content:
                    self.textCursor().select(QTextCursor.SelectionType.LineUnderCursor)
                    self.textCursor().removeSelectedText()
                    super().keyPressEvent(event)
                    return
                super().keyPressEvent(event)
                self.textCursor().insertText(f"{indent}{int(number.group(2)) + 1}. ")
                self._add_list_spacing()
                return

        if self._auto_list and key == Qt.Key.Key_Space:
            if self.textCursor().block().text() == "-":
                self.textCursor().select(QTextCursor.SelectionType.LineUnderCursor)
                self.textCursor().removeSelectedText()
                self.textCursor().insertText("• ")
                self._add_list_spacing()
                return

        super().keyPressEvent(event)

    def _add_list_spacing(self) -> None:
        fmt = QTextBlockFormat()
        fmt.setBottomMargin(3)
        self.textCursor().mergeBlockFormat(fmt)

    # ── Focus ─────────────────────────────────────────────────────────────────

    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        apply_saved_formatting()


class EditorPane(QWidget):
    """
    Container widget that holds NotepadEditor filling the full area with
    OverlayToolbar positioned absolutely on top via viewport margins.

    Created once at startup; reparented between NotepadDock and NotepadWindow
    when the user switches modes — text and cursor state are fully preserved.
    """

    def __init__(self):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        # Create the shared editor and register it in module state
        state.editor = NotepadEditor(self)
        self._apply_initial_font()

        # Toolbar is overlaid — not managed by a layout
        self._toolbar = OverlayToolbar()
        self._toolbar.setParent(self)
        self._toolbar.installEventFilter(self)

    def _apply_initial_font(self) -> None:
        """Apply the configured font immediately after editor creation."""
        cfg = get_config()
        family = cfg.get("font_family", "Arial")
        size   = cfg.get("font_size", 13)
        if cfg.get("font_source") == "card" and state.card_font:
            state.editor.setFont(QFont(state.card_font, size))
        else:
            state.editor.setFont(QFont(family, size))

    def toolbar(self) -> OverlayToolbar:
        return self._toolbar

    # ── Layout ────────────────────────────────────────────────────────────────

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._layout_children()

    def _layout_children(self) -> None:
        w, h  = self.width(), self.height()
        pad   = 5
        state.editor.setGeometry(0, 0, w, h)
        self._toolbar.setGeometry(pad, pad, w - 2 * pad, TOOLBAR_H)
        self._toolbar.raise_()
        state.editor.setViewportMargins(0, TOOLBAR_H + pad, 0, 0)

    # ── Autohide event filter ─────────────────────────────────────────────────

    def eventFilter(self, obj, event) -> bool:
        if obj is self._toolbar:
            if event.type() == QEvent.Type.Enter:
                self._toolbar.show_buttons()
            elif event.type() == QEvent.Type.Leave:
                QTimer.singleShot(80, self._check_toolbar_leave)
        return super().eventFilter(obj, event)

    def _check_toolbar_leave(self) -> None:
        if (not self._toolbar.underMouse()
                and any(b.isVisible() for b in self._toolbar._hideable)):
            self._toolbar.hide_buttons()
