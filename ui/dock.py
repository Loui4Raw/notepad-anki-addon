"""ui/dock.py — NotepadDock: the sidebar dock widget (always docked, never floating)."""
from aqt import mw
from aqt.qt import QDockWidget, QWidget, QVBoxLayout, Qt, QTimer

from ..config import get_config, save_config, is_dark_mode
from ..themes import get_theme, ThemeConfig
from .. import state
from .theme import apply_common_theme


class NotepadDock(QDockWidget):
    """
    Sidebar dock.  Features:
    - Never allowed to float (DockWidgetMovable only)
    - Invisible title bar (replaced with a zero-height widget)
    - Geometry memory respects the remember_position setting
    - apply_theme() delegates shared styling to apply_common_theme()
    """

    def __init__(self):
        super().__init__("Notepad", mw)
        self.setObjectName("NotepadDock")
        self.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        # Movable only — floating is handled by NotepadWindow, not the dock
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.setTitleBarWidget(QWidget())  # invisible zero-height title bar

        self._container = QWidget()
        self._layout    = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setWidget(self._container)

        cfg = get_config()
        self.setMinimumWidth(cfg.get("docked_min_width", 160))

        self.visibilityChanged.connect(self._on_visibility_changed)

    # ── Pane ownership ────────────────────────────────────────────────────────

    def adopt_pane(self) -> None:
        """Take EditorPane into this dock: reparent and add to layout."""
        state.pane.setParent(self._container)
        self._layout.addWidget(state.pane)
        state.pane.show()
        state.pane.toolbar().set_host(self)
        state.pane.toolbar()._btn_view.set_floating(False)

    def release_pane(self) -> None:
        """Remove EditorPane from layout so it can be reparented to the window."""
        self._layout.removeWidget(state.pane)

    # ── Geometry ──────────────────────────────────────────────────────────────

    def restore_docked_width(self) -> None:
        cfg = get_config()
        if cfg.get("remember_position", True):
            return
        target = (
            state.session_docked_width
            if state.session_docked_width is not None
            else cfg.get("docked_default_width", 240)
        )
        try:
            mw.resizeDocks([self], [target], Qt.Orientation.Horizontal)
        except Exception:
            pass

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.isVisible() and not get_config().get("remember_position", True):
            state.session_docked_width = self.geometry().width()

    # ── Show ──────────────────────────────────────────────────────────────────

    def show_in_dock(self) -> None:
        """Show dock, pre-pinning width to avoid a visible jump on first render."""
        cfg = get_config()
        if not cfg.get("remember_position", True) and state.session_docked_width is None:
            default_w = cfg.get("docked_default_width", 240)
            self.setFixedWidth(default_w)

        self.show()
        state.pane.toolbar().ensure_autohide_state()

        # Release fixed width constraint and apply the target width after Qt settles
        self.setMinimumWidth(cfg.get("docked_min_width", 160))
        self.setMaximumWidth(16777215)
        QTimer.singleShot(0, self.restore_docked_width)

    # ── Close ─────────────────────────────────────────────────────────────────

    def close_notepad(self) -> None:
        if self.isVisible():
            self.hide()
        _set_action_checked(False)

    # ── Signals ───────────────────────────────────────────────────────────────

    def _on_visibility_changed(self, visible: bool) -> None:
        _set_action_checked(visible)

    # ── Theme ─────────────────────────────────────────────────────────────────

    def apply_theme(self) -> None:
        cfg     = get_config()
        dark    = is_dark_mode()
        
        # Get theme-based colors with error handling
        try:
            theme_config = ThemeConfig(
                mode=cfg.get("theme_mode", "follow"),
                light_theme=cfg.get("light_theme", "blue"),
                dark_theme=cfg.get("dark_theme", "blue"),
                custom_light_themes=cfg.get("custom_light_themes", {}),
                custom_dark_themes=cfg.get("custom_dark_themes", {}),
                global_accent=cfg.get("accent_dark", "#5B9BF8")
            )
            
            current_theme = get_theme(theme_config, dark)
            editor_bg = current_theme.main_background
        except Exception:
            editor_bg = "#1E1E1E" if dark else "#FFFFFF"

        self.setStyleSheet("QDockWidget { border: none; outline: none; }")
        self._container.setStyleSheet(
            f"QWidget {{ background-color: {editor_bg}; }}"
        )
        apply_common_theme(cfg, dark, floating=False)

        # Suppress the drag-handle blue edge and rubber band selection box
        existing = mw.styleSheet()
        if "QMainWindow::separator" not in existing:
            mw.setStyleSheet(
                existing
                + "QMainWindow::separator{width:1px;height:1px;background:transparent;}"
                "QMainWindow::separator:hover{background:transparent;}"
                "QRubberBand{border:none;background:transparent;}"
            )


def _set_action_checked(checked: bool) -> None:
    if state.toggle_action is not None:
        state.toggle_action.blockSignals(True)
        state.toggle_action.setChecked(checked)
        state.toggle_action.blockSignals(False)
