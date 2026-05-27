"""
ui/buttons.py — SVG icon factories and all toolbar button classes.

Button classes share a common animated-hover base (_AnimBtn) that smoothly
fades the background opacity on enter/leave events using a QTimer-driven loop.
"""
from aqt.qt import QToolButton, Qt, QTimer
from PyQt6.QtSvgWidgets import QSvgWidget

from ..config import get_config, is_dark_mode


# ── SVG factories ─────────────────────────────────────────────────────────────

def _svg(path_d: str, vb: str = "0 -960 960 960"):
    """Return a factory that produces an SVG bytes object for a given colour/size."""
    def make(color: str, size: int = 18) -> bytes:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="{vb}" fill="{color}"><path d="{path_d}"/></svg>'
        ).encode()
    return make


def _svg_h_flip(path_d: str, vb: str = "0 -960 960 960"):
    """Same as _svg but mirrors horizontally — used for left-side dock icons."""
    def make(color: str, size: int = 18) -> bytes:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="{vb}" fill="{color}">'
            f'<g transform="scale(-1,1) translate(-960,0)">'
            f'<path d="{path_d}"/></g></svg>'
        ).encode()
    return make


# ── Icon definitions ──────────────────────────────────────────────────────────

_SVG_BOLD = _svg(
    "M272-200v-560h221q65 0 120 40t55 111q0 51-23 78.5T602-491q25 11 55.5 41"
    "t30.5 90q0 89-65 124.5T501-200H272Zm121-112h104q48 0 58.5-24.5T566-372"
    "q0-11-10.5-35.5T494-432H393v120Zm0-228h93q33 0 48-17t15-38q0-24-17-39"
    "t-44-15h-95v109Z"
)
_SVG_ITALIC = _svg(
    "M200-200v-100h160l120-360H320v-100h400v100H580L460-300h140v100H200Z"
)
_SVG_UNDERLINE = _svg(
    "M200-120v-80h560v80H200Zm123-223q-56-63-56-167v-330h103v336q0 56 28 91"
    "t82 35q54 0 82-35t28-91v-336h103v330q0 104-56 167t-157 63q-101 0-157-63Z"
)
_SVG_WINDOW = _svg(
    "M160-80q-33 0-56.5-23.5T80-160v-360q0-33 23.5-56.5T160-600h80v-200"
    "q0-33 23.5-56.5T320-880h480q33 0 56.5 23.5T880-800v360q0 33-23.5 56.5"
    "T800-360h-80v200q0 33-23.5 56.5T640-80H160Zm0-80h480v-280H160v280Zm"
    "560-280h80v-280H320v120h320q33 0 56.5 23.5T720-520v80Z"
)
_SVG_SIDEBAR = _svg(
    "M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560"
    "q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm440-80h120"
    "v-560H640v560Zm-80 0v-560H200v560h360Zm80 0h120-120Z"
)
_SVG_SIDEBAR_HOVER = _svg(
    "M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 "
    "56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm360-80v-560H200v560h360Z"
)
# Mirrored variants — used when the dock is on the left side
_SVG_SIDEBAR_LEFT = _svg_h_flip(
    "M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560"
    "q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm440-80h120"
    "v-560H640v560Zm-80 0v-560H200v560h360Zm80 0h120-120Z"
)
_SVG_SIDEBAR_LEFT_HOVER = _svg_h_flip(
    "M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 "
    "56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm360-80v-560H200v560h360Z"
)
_SVG_CLOSE = _svg(
    "m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 "
    "224 224-56 56-224-224-224 224Z"
)


# ── Animated button base ──────────────────────────────────────────────────────

class _AnimBtn(QToolButton):
    """
    Base class for all Notepad toolbar buttons.

    Provides smooth hover background fade via a 16 ms QTimer-driven loop and
    hosts an SVG icon widget centred inside the button.
    """

    def __init__(self, size: int = 19, icon_size: int = 16, svg_y_offset: int = 0):
        super().__init__()
        self._normal:  str   = "#666666"
        self._accent:  str   = "#5B9BF8"
        self._is_dark: bool  = False
        self._opacity: float = 0.0
        self._target:  float = 0.0

        self.setFixedSize(size, size)

        self._svg = QSvgWidget(self)
        self._svg.setFixedSize(icon_size, icon_size)
        self._svg.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._svg.setStyleSheet("background: transparent;")
        margin = (size - icon_size) // 2
        self._svg.move(margin, margin + svg_y_offset)

        self._timer = QTimer()
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._step)
        self._apply_style()

    def update_colors(self, normal: str, accent: str, is_dark: bool = False) -> None:
        self._normal  = normal
        self._accent  = accent
        self._is_dark = is_dark
        self._load_icon()
        self._apply_style()

    # ── Animation ─────────────────────────────────────────────────────────────

    def _step(self) -> None:
        diff = self._target - self._opacity
        if abs(diff) < 0.02:
            self._opacity = self._target
            self._timer.stop()
        else:
            self._opacity += diff * 0.12
        self._apply_style()

    def _bg_rgba(self) -> str:
        if self._is_dark:
            return f"rgba(255,255,255,{self._opacity * 0.15:.3f})"
        return f"rgba(0,0,0,{self._opacity * 0.12:.3f})"

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"QToolButton {{ background-color: {self._bg_rgba()};"
            "border: none; border-radius: 4px; padding: 0; }}"
        )

    def _load_icon(self) -> None:
        pass

    # ── Hover ─────────────────────────────────────────────────────────────────

    def enterEvent(self, event) -> None:
        self._target = 1.0
        if not self._timer.isActive():
            self._timer.start()
        self._on_hover(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._target = 0.0
        if not self._timer.isActive():
            self._timer.start()
        self._on_hover(False)
        super().leaveEvent(event)

    def _on_hover(self, hovered: bool) -> None:
        pass


# ── Concrete button classes ───────────────────────────────────────────────────

class FormatButton(_AnimBtn):
    """Bold / italic / underline toggle button."""

    def __init__(self, svg_fn, tooltip: str,
                 size: int = 19, icon_size: int = 16, svg_y_offset: int = 0):
        self._svg_fn = svg_fn
        super().__init__(size, icon_size, svg_y_offset)
        self.setToolTip(tooltip)
        self.setCheckable(True)
        # Re-draw icon when clicked (base class clicked signal fires first)
        self.clicked.connect(lambda: self.setChecked(not self.isChecked()))
        self._load_icon()

    def _load_icon(self) -> None:
        self._svg.load(self._svg_fn(self._accent if self.isChecked() else self._normal))

    def setChecked(self, val: bool) -> None:
        super().setChecked(val)
        self._load_icon()
        self._apply_style()

    def _bg_rgba(self) -> str:
        # Checked state: keep the hover background permanently visible
        if self.isChecked():
            return "rgba(255,255,255,0.15)" if self._is_dark else "rgba(0,0,0,0.12)"
        return super()._bg_rgba()


class ViewButton(_AnimBtn):
    """Sidebar ↔ window toggle button.  Icon reflects current mode and dock side."""

    def __init__(self, size: int = 19, icon_size: int = 16):
        self._floating:  bool = False
        self._hovering:  bool = False
        self._dock_left: bool = False
        super().__init__(size, icon_size)
        self._load_icon()
        self.setToolTip("Pop out to window")

    def set_floating(self, floating: bool) -> None:
        self._floating = floating
        self._opacity  = 0.0
        self._target   = 0.0
        self._timer.stop()
        self._update_dock_side()
        self._load_icon()
        self._apply_style()
        self.setToolTip("Return to sidebar" if floating else "Pop out to window")

    def _update_dock_side(self) -> None:
        from aqt import mw
        from .. import state
        try:
            area = mw.dockWidgetArea(state.dock)
            self._dock_left = (area == Qt.DockWidgetArea.LeftDockWidgetArea)
        except Exception:
            self._dock_left = False

    def _icon_factory(self):
        if self._floating:
            if self._dock_left:
                return _SVG_SIDEBAR_LEFT_HOVER if self._hovering else _SVG_SIDEBAR_LEFT
            return _SVG_SIDEBAR_HOVER if self._hovering else _SVG_SIDEBAR
        return _SVG_WINDOW

    def _load_icon(self) -> None:
        self._svg.load(self._icon_factory()(self._normal))

    def _on_hover(self, hovered: bool) -> None:
        self._hovering = hovered
        self._load_icon()


class CloseButton(_AnimBtn):
    """Close button — fades to red on hover."""

    def __init__(self, size: int = 19, icon_size: int = 16):
        super().__init__(size, icon_size)
        self._load_icon()

    def _bg_rgba(self) -> str:
        return f"rgba(250,82,82,{self._opacity * 0.75:.3f})"

    def _load_icon(self) -> None:
        color = "#FFFFFF" if self._opacity > 0.45 else self._normal
        self._svg.load(_SVG_CLOSE(color))

    def _step(self) -> None:
        diff = self._target - self._opacity
        if abs(diff) < 0.02:
            self._opacity = self._target
            self._timer.stop()
        else:
            self._opacity += diff * 0.12
        self._apply_style()
        self._load_icon()
