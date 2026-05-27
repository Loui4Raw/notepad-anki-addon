"""ui/window.py — NotepadWindow: standalone frameless window for windowed mode."""
from aqt import mw
from aqt.qt import (
    QWidget, QVBoxLayout, Qt, QRect, QPoint, QColor, QEvent, QTimer,
)
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

from ..config import (
    get_config, save_config, is_dark_mode,
    SHADOW_M, RESIZE_EDGE, MIN_CONTENT_W, MIN_CONTENT_H,
    default_windowed_geometry,
)
from ..themes import get_theme, ThemeConfig
from .. import state
from .theme import apply_common_theme
from .dock import _set_action_checked


def _parse_shadow_color(text: str) -> QColor:
    """Parse an rgba(...), rgb(...) or #hex string into a QColor.

    Falls back to a semi-transparent black if parsing fails.
    """
    text = text.strip()
    try:
        if text.startswith("rgba("):
            inner = text[5:].rstrip(")")
            parts = [p.strip() for p in inner.split(",")]
            if len(parts) == 4:
                r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                a = float(parts[3])
                alpha = int(min(max(a, 0.0), 1.0) * 255) if a <= 1.0 else int(min(a, 255))
                return QColor(r, g, b, alpha)
        elif text.startswith("rgb("):
            inner = text[4:].rstrip(")")
            parts = [p.strip() for p in inner.split(",")]
            if len(parts) == 3:
                return QColor(int(parts[0]), int(parts[1]), int(parts[2]), 255)
        else:
            color = QColor(text)   # handles #rrggbb / #aarrggbb / named colors
            if color.isValid():
                return color
    except Exception:
        pass
    return QColor(0, 0, 0, 77)   # safe fallback: ~30% black


class NotepadWindow(QWidget):
    """
    Standalone frameless window providing true rounded corners, a two-layer
    drop shadow, custom edge resize, and toolbar drag-to-move.
    """

    # Shadow parameters (ambient_blur, ambient_y, ambient_alpha_resting, ambient_alpha_active,
    #   direct_blur,  direct_y,  direct_alpha_resting,  direct_alpha_active)
    _SHADOW_PARAMS = (65, 2, 0.12, 0.22, 70, 12, 0.14, 0.26)

    def __init__(self):
        super().__init__(mw, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        # WA_TranslucentBackground is set ONCE at construction and never toggled
        # to avoid Qt compositing-state caching issues (black corners on re-show).
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(
            MIN_CONTENT_W + 2 * SHADOW_M,
            MIN_CONTENT_H + 2 * SHADOW_M,
        )

        # Shadow layers
        # Both are childless so their effects cannot interfere with child layout.
        self._shadow_ambient = QWidget(self)
        self._shadow_ambient.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._fx_ambient = QGraphicsDropShadowEffect()
        self._fx_ambient.setXOffset(0)
        self._shadow_ambient.setGraphicsEffect(self._fx_ambient)

        self._shadow_direct = QWidget(self)
        self._shadow_direct.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._fx_direct = QGraphicsDropShadowEffect()
        self._fx_direct.setXOffset(0)
        self._shadow_direct.setGraphicsEffect(self._fx_direct)

        # Background layer
        # Paints background colour + border + border-radius; no shadow effect
        # (effects on parent are sufficient; adding one here would double-shadow).
        self._bg = QWidget(self)
        self._bg.setObjectName("NotepadInner")
        self._bg.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Content layer
        # No graphics effect — EditorPane's OverlayToolbar uses absolute positioning
        # which breaks when a QGraphicsEffect is applied to an ancestor.
        self._content        = QWidget(self)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

        # Shadow animation state
        a_bl, a_y, a_r, a_a, d_bl, d_y, d_r, d_a = self._SHADOW_PARAMS
        self._alpha_resting = [a_r, d_r]
        self._alpha_active  = [a_a, d_a]
        self._alpha_current = list(self._alpha_resting)
        self._alpha_target  = list(self._alpha_resting)
        self._shadow_enabled = True
        # When set, _apply_shadow_values() uses these exact QColors rather than
        # deriving black-with-varying-alpha from _alpha_current.
        # Used by custom and subtle modes to preserve the user's chosen RGBA.
        self._custom_ambient_color: QColor | None = None
        self._custom_direct_color:  QColor | None = None

        self._shadow_timer = QTimer()
        self._shadow_timer.setInterval(16)
        self._shadow_timer.timeout.connect(self._step_shadow)

        self._apply_shadow_values()

        # Resize tracking
        self._resizing           = False
        self._resize_dir         = (False, False, False, False)  # L, R, T, B
        self._resize_start_geom  = QRect()
        self._resize_start_pos   = QPoint()

        self.setMouseTracking(True)

    # Pane ownership

    def adopt_pane(self) -> None:
        state.pane.setParent(self._content)
        self._content_layout.addWidget(state.pane)
        state.pane.show()
        state.pane.toolbar().set_host(self)
        state.pane.toolbar()._btn_view.set_floating(True)

    def release_pane(self) -> None:
        self._content_layout.removeWidget(state.pane)

    # Geometry

    def restore_geometry(self) -> None:
        cfg = get_config()
        if cfg.get("remember_position", True):
            x = cfg.get("windowed_x")
            y = cfg.get("windowed_y")
            w = cfg.get("windowed_width",  250) + 2 * SHADOW_M
            h = cfg.get("windowed_height", 350) + 2 * SHADOW_M
            if x is not None and y is not None:
                self.setGeometry(x, y, w, h)
                return
        elif state.session_windowed_geom is not None:
            self.setGeometry(*state.session_windowed_geom)
            return
        self.setGeometry(*default_windowed_geometry())

    def _save_geometry(self) -> None:
        cfg = get_config()
        g   = self.geometry()
        if cfg.get("remember_position", True):
            cfg["windowed_x"]      = g.x()
            cfg["windowed_y"]      = g.y()
            cfg["windowed_width"]  = g.width()  - 2 * SHADOW_M
            cfg["windowed_height"] = g.height() - 2 * SHADOW_M
            save_config(cfg)
        else:
            state.session_windowed_geom = (g.x(), g.y(), g.width(), g.height())

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        if self.isVisible():
            self._save_geometry()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        inner = self.rect().adjusted(SHADOW_M, SHADOW_M, -SHADOW_M, -SHADOW_M)
        self._shadow_ambient.setGeometry(inner)
        self._shadow_direct.setGeometry(inner)
        self._bg.setGeometry(inner)
        self._content.setGeometry(inner)
        self._content.raise_()
        if self.isVisible():
            self._save_geometry()

    # Shadow animation

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.ActivationChange and self._shadow_enabled:
            self._alpha_target = list(
                self._alpha_active if self.isActiveWindow() else self._alpha_resting
            )
            if not self._shadow_timer.isActive():
                self._shadow_timer.start()

    def _step_shadow(self) -> None:
        done = True
        for i in range(len(self._alpha_current)):
            diff = self._alpha_target[i] - self._alpha_current[i]
            if abs(diff) < 0.002:
                self._alpha_current[i] = self._alpha_target[i]
            else:
                self._alpha_current[i] += diff * 0.08
                done = False
        self._apply_shadow_values()
        if done:
            self._shadow_timer.stop()

    def _apply_shadow_values(self) -> None:
        if not self._shadow_enabled:
            self._fx_ambient.setColor(QColor(0, 0, 0, 0))
            self._fx_direct.setColor(QColor(0, 0, 0, 0))
            return
        # Custom/subtle modes store exact QColors; standard mode animates black alpha.
        if self._custom_ambient_color is not None:
            self._fx_ambient.setColor(self._custom_ambient_color)
        else:
            self._fx_ambient.setColor(QColor(0, 0, 0, int(self._alpha_current[0] * 255)))
        if self._custom_direct_color is not None:
            self._fx_direct.setColor(self._custom_direct_color)
        else:
            self._fx_direct.setColor(QColor(0, 0, 0, int(self._alpha_current[1] * 255)))

    # Resize handling

    def _edge_flags(self, pos) -> tuple[bool, bool, bool, bool]:
        x, y, w, h = pos.x(), pos.y(), self.width(), self.height()
        m = RESIZE_EDGE
        return x < m, x > w - m, y < m, y > h - m

    @staticmethod
    def _cursor_for_edges(left, right, top, bottom) -> Qt.CursorShape:
        if   (left and top)  or (right and bottom): return Qt.CursorShape.SizeFDiagCursor
        elif (right and top) or (left and bottom):  return Qt.CursorShape.SizeBDiagCursor
        elif left or right:                          return Qt.CursorShape.SizeHorCursor
        elif top  or bottom:                         return Qt.CursorShape.SizeVerCursor
        return Qt.CursorShape.ArrowCursor

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            l, r, t, b = self._edge_flags(event.position().toPoint())
            if any((l, r, t, b)):
                self._resizing           = True
                self._resize_dir         = (l, r, t, b)
                self._resize_start_geom  = self.geometry()
                self._resize_start_pos   = event.globalPosition().toPoint()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._resizing:
            self._do_resize(event.globalPosition().toPoint())
            event.accept()
        else:
            l, r, t, b = self._edge_flags(event.position().toPoint())
            self.setCursor(self._cursor_for_edges(l, r, t, b))
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._resizing:
            self._resizing = False
            self.unsetCursor()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _do_resize(self, global_pos) -> None:
        delta = global_pos - self._resize_start_pos
        geom  = QRect(self._resize_start_geom)
        min_w = MIN_CONTENT_W + 2 * SHADOW_M
        min_h = MIN_CONTENT_H + 2 * SHADOW_M
        l, r, t, b = self._resize_dir

        if l:
            new_left = geom.left() + delta.x()
            if geom.right() - new_left + 1 >= min_w:
                geom.setLeft(new_left)
        if r:
            geom.setRight(max(geom.left() + min_w - 1,
                              geom.left() + geom.width() + delta.x() - 1))
        if t:
            new_top = geom.top() + delta.y()
            if geom.bottom() - new_top + 1 >= min_h:
                geom.setTop(new_top)
        if b:
            geom.setBottom(max(geom.top() + min_h - 1,
                               geom.top() + geom.height() + delta.y() - 1))
        self.setGeometry(geom)

    # Close

    def close_window(self) -> None:
        if self.isVisible():
            self.hide()
        _set_action_checked(False)

    # Theme

    def apply_theme(self) -> None:
        cfg           = get_config()
        dark          = is_dark_mode()
        
        # Get theme-based colors with error handling
        try:
            theme_config = ThemeConfig(
                mode=cfg.get("theme_mode", "follow"),
                light_theme=cfg.get("light_theme", "blue"),
                dark_theme=cfg.get("dark_theme", "blue"),
                custom_light_themes=cfg.get("custom_light_themes", {}),
                custom_dark_themes=cfg.get("custom_dark_themes", {}),
            )
            
            current_theme = get_theme(theme_config, dark)
            editor_bg = current_theme.main_background
            accent = current_theme.accent if current_theme.accent else cfg.get("accent_dark" if dark else "accent_light", "#5B9BF8")
        except Exception:
            editor_bg = "#1E1E1E" if dark else "#FFFFFF"
            accent = cfg.get("accent_dark" if dark else "accent_light", "#5B9BF8")
        
        border_radius = cfg.get("border_radius", 6)
        border_style = cfg.get("border_style", "custom")
        custom_border_color = cfg.get("custom_border_color", "")

        # Calculate border CSS
        if border_style == "none":
            border_css = "none"
        elif border_style == "accent":
            border_css = f"1px solid {accent}"
        elif border_style == "custom":
            if custom_border_color:
                border_css = f"1px solid {custom_border_color}"
            else:
                border_css = f"1px solid {editor_bg}"  # Use background as default
        else:
            # Fallback to old logic
            border_accent = cfg.get("editor_border_accent", False)
            if border_accent:
                border_css = f"1px solid {accent}"
            else:
                border_css = f"1px solid {'#404040' if dark else '#CCCCCC'}"

        # Background widget: scoped to #NotepadInner so styles don't cascade
        bg_radius = max(0, border_radius - 2)
        self._bg.setStyleSheet(f"""
            QWidget#NotepadInner {{
                background-color: {editor_bg};
                border: {border_css};
                border-radius: {bg_radius}px;
            }}
        """)
        
        # Main window styling with overflow hidden
        actual_radius = max(0, border_radius - 1)
        self.setStyleSheet(f"""
            NotepadWindow {{
                overflow: hidden;
                border: {border_css};
                border-radius: {actual_radius}px;
            }}
        """)

        # Shadow
        self._shadow_enabled = cfg.get("window_shadow", True)
        shadow_style = cfg.get("shadow_style", "standard")
        
        if shadow_style == "subtle":
            # Subtle: fixed light drop shadow, no hover animation.
            alpha = int(0.3 * 255) if dark else int(0.1 * 255)
            self._custom_ambient_color = QColor(0, 0, 0, 0)
            self._custom_direct_color  = QColor(0, 0, 0, alpha)
            self._fx_ambient.setBlurRadius(0)
            self._fx_ambient.setYOffset(0)
            self._fx_direct.setBlurRadius(45)
            self._fx_direct.setYOffset(5)
        elif shadow_style == "custom":
            # Custom: user-defined blur, offset, and RGBA color.
            custom_blur   = cfg.get("custom_shadow_blur",   12)
            custom_offset = cfg.get("custom_shadow_offset",  4)
            custom_color  = cfg.get("custom_shadow_color",  "rgba(0,0,0,0.3)")

            self._custom_ambient_color = QColor(0, 0, 0, 0)
            self._custom_direct_color  = _parse_shadow_color(custom_color)

            self._fx_ambient.setBlurRadius(0)
            self._fx_ambient.setYOffset(0)
            self._fx_direct.setBlurRadius(custom_blur)
            self._fx_direct.setYOffset(custom_offset)
        else:
            # Standard shadow — animated black with varying alpha.
            self._custom_ambient_color = None
            self._custom_direct_color  = None
            scale = 1.3 if dark else 1.0
            a_bl, a_y, a_r, a_a, d_bl, d_y, d_r, d_a = self._SHADOW_PARAMS
            
            self._alpha_resting = [a_r * scale, d_r * scale]
            self._alpha_active  = [a_a * scale, d_a * scale]
            
            # Blur/offset are fixed — only alpha animates
            self._fx_ambient.setBlurRadius(a_bl)
            self._fx_ambient.setYOffset(a_y)
            self._fx_direct.setBlurRadius(d_bl)
            self._fx_direct.setYOffset(d_y)

        # Snap to current activation state without animating
        target = list(
            self._alpha_active if self.isActiveWindow() else self._alpha_resting
        )
        self._alpha_current = target[:]
        self._alpha_target  = target[:]
        self._apply_shadow_values()

        # Shadow widgets: border-radius 1 px smaller than _bg so their square
        # corners sit fully underneath _bg and do not bleed out.
        shadow_r     = max(0, border_radius - 1)
        shadow_style = f"background-color: {editor_bg}; border-radius: {shadow_r}px; border: none;"
        self._shadow_ambient.setStyleSheet(shadow_style)
        self._shadow_direct.setStyleSheet(shadow_style)

        # Window opacity
        if cfg.get("window_transparent", False):
            self.setWindowOpacity(cfg.get("window_opacity", 90) / 100.0)
        else:
            self.setWindowOpacity(1.0)

        apply_common_theme(cfg, dark, floating=True)
