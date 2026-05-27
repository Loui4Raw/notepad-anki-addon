"""
ui/theme_editor.py — Dialog for editing individual theme colours.

Allows customising all colours within a specific theme, with live preview
and automatic text-colour calculation based on background luminance.
"""
from __future__ import annotations

from aqt import mw
from aqt.qt import (
    QColor, QColorDialog, QDialog, QDialogButtonBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, Qt, QToolButton,
    QVBoxLayout, QWidget,
)

from ..themes import ThemeColors


class ThemeEditorDialog(QDialog):
    """
    Edits one ThemeColors in-place.

    The caller is responsible for persisting the result; this dialog only
    returns the edited ThemeColors object on accept.
    """

    def __init__(
        self,
        theme_key: str,
        theme: ThemeColors,
        is_dark_mode: bool,
        parent=None,
    ):
        super().__init__(parent)
        self._theme_key  = theme_key
        self._is_dark    = is_dark_mode

        # Working copy — mutated by colour pickers; original untouched until accept
        self._theme = ThemeColors(
            name=theme.name,
            buttons=theme.buttons,
            main_background=theme.main_background,
            toolbar=theme.toolbar,
            accent=theme.accent,
            text=theme.text,
        )

        # Keep the predefined original for Reset
        from ..themes import get_available_themes
        predefined = get_available_themes(is_dark_mode)
        self._predefined = predefined.get(theme_key, theme)

        # If no accent color, set a default based on theme type
        if not self._theme.accent:
            self._theme.accent = "#5B9BF8"

        self.setWindowTitle(f"Edit Theme: {theme.name}")
        self.setMinimumWidth(420)
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        # Name
        name_grp = QGroupBox("Theme Name")
        name_frm = QFormLayout(name_grp)
        name_frm.setSpacing(8)
        name_frm.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        name_frm.setContentsMargins(12, 12, 12, 12)
        self._name_edit = QLineEdit(self._theme.name)
        name_frm.addRow("Name:", self._name_edit)
        root.addWidget(name_grp)

        # Colours
        col_grp = QGroupBox("Colours")
        col_frm = QFormLayout(col_grp)
        col_frm.setSpacing(8)
        col_frm.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        col_frm.setContentsMargins(12, 12, 12, 12)

        self._btn_bg      = self._colour_btn(self._theme.main_background)
        self._btn_toolbar = self._colour_btn(self._theme.toolbar)
        self._btn_buttons = self._colour_btn(self._theme.buttons)
        self._btn_accent  = self._colour_btn(self._theme.accent or "#5B9BF8")
        self._btn_text    = self._colour_btn(self._theme.text)

        col_frm.addRow("Main background:", self._btn_bg)
        col_frm.addRow("Toolbar:",         self._btn_toolbar)
        col_frm.addRow("Buttons:",         self._btn_buttons)
        col_frm.addRow("Accent:",          self._btn_accent)
        col_frm.addRow("Text:",            self._btn_text)

        self._btn_bg.clicked.connect(
            lambda: self._pick("main_background", self._btn_bg)
        )
        self._btn_toolbar.clicked.connect(
            lambda: self._pick("toolbar", self._btn_toolbar)
        )
        self._btn_buttons.clicked.connect(
            lambda: self._pick("buttons", self._btn_buttons)
        )
        self._btn_accent.clicked.connect(
            lambda: self._pick("accent", self._btn_accent)
        )
        self._btn_text.clicked.connect(
            lambda: self._pick("text", self._btn_text)
        )
        root.addWidget(col_grp)

        # Preview
        prev_grp = QGroupBox("Preview")
        prev_lay = QVBoxLayout(prev_grp)
        prev_lay.setContentsMargins(12, 12, 12, 12)
        self._preview = self._build_preview()
        prev_lay.addWidget(self._preview)
        self._refresh_preview()
        root.addWidget(prev_grp)

        # Dialog buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Reset
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(
            self._on_reset
        )
        root.addWidget(btns)

    # ── Preview ───────────────────────────────────────────────────────────────

    def _build_preview(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(70)
        layout = QHBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Store references so _refresh_preview can update them directly
        self._prev_toolbar_lbl = QLabel("Toolbar")
        self._prev_button_lbl  = QLabel("Button")
        self._prev_text_lbl    = QLabel("Sample text")

        layout.addWidget(self._prev_toolbar_lbl)
        layout.addWidget(self._prev_button_lbl)
        layout.addWidget(self._prev_text_lbl)
        layout.addStretch()

        return w

    def _refresh_preview(self) -> None:
        t = self._theme
        self._preview.setStyleSheet(
            f"QWidget {{ background-color: {t.main_background};"
            "border: 1px solid #888; border-radius: 4px; }}"
        )
        self._prev_toolbar_lbl.setStyleSheet(
            f"QLabel {{ background-color: {t.toolbar}; color: {t.text};"
            "padding: 4px 8px; border-radius: 2px; }}"
        )
        self._prev_button_lbl.setStyleSheet(
            f"QLabel {{ background-color: {t.buttons}; color: {t.text};"
            "padding: 4px 8px; border-radius: 2px; }}"
        )
        self._prev_text_lbl.setStyleSheet(f"QLabel {{ color: {t.text}; }}")

    # ── Colour helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _colour_btn(hex_color: str) -> QToolButton:
        btn = QToolButton()
        btn.setText(hex_color)
        btn.setFixedHeight(28)
        ThemeEditorDialog._style_btn(btn, hex_color)
        return btn

    @staticmethod
    def _style_btn(btn: QToolButton, hex_color: str) -> None:
        c   = QColor(hex_color)
        lum = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
        btn.setStyleSheet(
            f"background-color:{hex_color};"
            f"color:{'#000' if lum > 128 else '#FFF'};"
            "border:1px solid #888;border-radius:4px;padding:4px 8px;"
        )

    def _pick(self, attr: str, btn: QToolButton) -> None:
        colour = QColorDialog.getColor(QColor(btn.text()), self)
        if not colour.isValid():
            return
        hex_color = colour.name()
        setattr(self._theme, attr, hex_color)
        btn.setText(hex_color)
        self._style_btn(btn, hex_color)
        # Auto-update text colour when background changes
        if attr == "main_background":
            self._theme.text = ThemeColors._calculate_text_color(hex_color)
            self._btn_text.setText(self._theme.text)
            self._style_btn(self._btn_text, self._theme.text)
        self._refresh_preview()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_accept(self) -> None:
        self._theme.name = self._name_edit.text().strip() or self._theme.name
        self.accept()

    def _on_reset(self) -> None:
        """Reset all fields to the original predefined values."""
        p = self._predefined
        self._theme = ThemeColors(
            name=p.name, buttons=p.buttons,
            main_background=p.main_background, toolbar=p.toolbar, text=p.text,
        )
        self._name_edit.setText(self._theme.name)
        for btn, val in (
            (self._btn_bg,      self._theme.main_background),
            (self._btn_toolbar, self._theme.toolbar),
            (self._btn_buttons, self._theme.buttons),
            (self._btn_text,    self._theme.text),
        ):
            btn.setText(val)
            self._style_btn(btn, val)
        self._refresh_preview()

    # ── Result ────────────────────────────────────────────────────────────────

    def result_theme(self) -> ThemeColors:
        return self._theme


# ── Public helper ─────────────────────────────────────────────────────────────

def open_theme_editor(
    theme_key: str,
    theme: ThemeColors,
    is_dark_mode: bool,
    parent=None,
) -> ThemeColors | None:
    """
    Open the theme editor.  Returns the edited ThemeColors on accept, else None.
    The caller is responsible for persisting the result.
    """
    dlg = ThemeEditorDialog(theme_key, theme, is_dark_mode, parent)
    if dlg.exec() == QDialog.DialogCode.Accepted:
        return dlg.result_theme()
    return None
