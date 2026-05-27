"""ui/toolbar.py — OverlayToolbar widget."""
from aqt.qt import (
    QWidget, QHBoxLayout, Qt, QTimer, QEvent,
)
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

from .buttons import (
    FormatButton, ViewButton, CloseButton,
    _SVG_BOLD, _SVG_ITALIC, _SVG_UNDERLINE,
)

TOOLBAR_H = 34  # fixed height used by EditorPane layout


class OverlayToolbar(QWidget):
    """
    Translucent toolbar rendered on top of the editor area.

    Drag-to-move: active only when the host widget is a NotepadWindow (floating).
    Autohide: when enabled, format buttons fade out until the toolbar is hovered.
    """

    def __init__(self):
        super().__init__()
        self._autohide = False
        self._drag_pos = None
        self._host     = None  # NotepadDock or NotepadWindow set via set_host()

        # Button instances (attribute names referenced externally)
        self._btn_bold      = FormatButton(_SVG_BOLD,      "Bold (Ctrl+B)",      size=22, icon_size=16)
        self._btn_italic    = FormatButton(_SVG_ITALIC,    "Italic (Ctrl+I)",    size=22, icon_size=16)
        self._btn_underline = FormatButton(_SVG_UNDERLINE, "Underline (Ctrl+U)", size=22, icon_size=15, svg_y_offset=1)
        self._btn_view      = ViewButton(size=22, icon_size=16)
        self._btn_close     = CloseButton(size=19, icon_size=18)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        layout.addWidget(self._btn_bold)
        layout.addWidget(self._btn_italic)
        layout.addWidget(self._btn_underline)
        layout.addStretch()
        layout.addWidget(self._btn_view)
        layout.addWidget(self._btn_close)

        # Buttons that participate in autohide (close is always visible)
        self._hideable = [self._btn_bold, self._btn_italic, self._btn_underline]

        # Set up per-button opacity effects for autohide animation
        for btn in self._hideable:
            fx   = QGraphicsOpacityEffect()
            fx.setOpacity(1.0)
            anim = QPropertyAnimation(fx, b"opacity")
            anim.setDuration(220)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            btn.setGraphicsEffect(fx)
            btn._fade_fx   = fx
            btn._fade_anim = anim

    # ── Host ──────────────────────────────────────────────────────────────────

    def set_host(self, host) -> None:
        """Set the widget that receives drag-move events (NotepadWindow only)."""
        self._host = host

    def _is_draggable(self) -> bool:
        from .window import NotepadWindow
        return self._host is not None and isinstance(self._host, NotepadWindow)

    # ── Autohide ──────────────────────────────────────────────────────────────

    def set_autohide(self, enabled: bool) -> None:
        self._autohide = enabled
        self.ensure_autohide_state()

    def _set_opacity(self, value: float, instant: bool = False) -> None:
        for btn in self._hideable:
            if instant:
                btn._fade_fx.setOpacity(value)
            else:
                btn._fade_anim.stop()
                btn._fade_anim.setStartValue(btn._fade_fx.opacity())
                btn._fade_anim.setEndValue(value)
                btn._fade_anim.start()

    def show_buttons(self) -> None:
        if self._autohide:
            self._set_opacity(1.0)

    def hide_buttons(self) -> None:
        if self._autohide:
            self._set_opacity(0.0)

    def set_format_buttons_visible(self, visible: bool) -> None:
        for btn in self._hideable:
            btn.setVisible(visible)
        self._btn_view.setVisible(True)
        self._btn_close.setVisible(True)
        self.ensure_autohide_state()

    def ensure_autohide_state(self) -> None:
        if not any(btn.isVisible() for btn in self._hideable):
            return
        self._set_opacity(0.0 if self._autohide else 1.0, instant=True)

    # ── Drag ──────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._is_draggable():
            child = self.childAt(event.position().toPoint())
            if child is None or not hasattr(child, "clicked"):
                self._drag_pos = (
                    event.globalPosition().toPoint()
                    - self._host.frameGeometry().topLeft()
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (event.buttons() == Qt.MouseButton.LeftButton
                and self._drag_pos is not None
                and self._host is not None):
            self._host.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None
        super().mouseReleaseEvent(event)
