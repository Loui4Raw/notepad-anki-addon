"""
ui/settings.py — SettingsDialog and open_settings().

Reachable from the Notepad top-menu.  All theme changes are saved immediately
and applied to the live notepad on every meaningful interaction.
"""
from __future__ import annotations

from aqt import mw
from aqt.qt import (
    QButtonGroup, QCheckBox, QColor, QColorDialog, QComboBox, QDialog,
    QDialogButtonBox, QFont, QFontComboBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QTabWidget,
    QToolButton, QVBoxLayout, QWidget, Qt, QPushButton, QIcon, QPixmap,
    QTimer,
)
from PyQt6.QtWidgets import QSlider, QMessageBox

from ..config import get_config, save_config
from ..themes import ThemeColors, get_available_themes
from .. import state
from .theme import apply_current_theme




class ThemeWidget(QWidget):
    """Simple wrapper around ThemeCircleButton."""

    def __init__(self, key: str, theme: ThemeColors, mode: str,
                 dialog: "SettingsDialog") -> None:
        super().__init__()
        self.setFixedSize(45, 45)  # Match ThemeCircleButton size
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._btn = ThemeCircleButton(key, theme, mode, dialog)
        layout.addWidget(self._btn)

    def get_button(self) -> "ThemeCircleButton":
        return self._btn


class ThemeCircleButton(QToolButton):
    """
    Circular theme-picker button.

    Single-click selects this theme via the parent QButtonGroup.
    Double-click opens the theme editor for customisation.
    """

    def __init__(self, key: str, theme: ThemeColors, mode: str,
                 dialog: "SettingsDialog") -> None:
        super().__init__()
        self._key    = key
        self._theme  = theme
        self._mode   = mode
        self._dialog = dialog

        self.setCheckable(True)
        self.setFixedSize(45, 45)
        self.setToolTip(f"{theme.name}\nDouble-click to edit")
        self._apply_style(selected=False)

    def _apply_style(self, selected: bool) -> None:
        border = "3px solid #0282FA" if selected else "2px solid #888"
        self.setStyleSheet(f"""
            QToolButton {{
                background-color: {self._theme.toolbar};
                border: {border};
                border-radius: 22px;
            }}
            QToolButton:hover:!checked {{
                border: 2px solid #0282FA;
            }}
        """)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dialog._edit_theme(self._key, self._mode)
        super().mouseDoubleClickEvent(event)


class _AddThemeButton(QToolButton):
    """Circular '+' button appended to the theme grid to create a new custom theme."""

    def __init__(self, mode: str, dialog: "SettingsDialog") -> None:
        super().__init__()
        self._mode   = mode
        self._dialog = dialog

        self.setFixedSize(45, 45)
        self.setText("+")
        self.setToolTip("Add new theme")
        self.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                color: #666;
                border: 2px dashed #666;
                border-radius: 22px;
                font-size: 32px;
                font-weight: normal;
                qproperty-alignment: AlignCenter;
                padding-top: -7px;
            }
            QToolButton:hover {
                border-color: #5B9BF8;
                color: #5B9BF8;
            }
        """)
        self.clicked.connect(lambda: self._dialog._add_new_theme(self._mode))


# ── Settings dialog ───────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    """Full settings dialog: General / Appearance / Themes tabs."""

    _MODE_TO_TEXT = {"follow": "Follow Anki", "light": "Light", "dark": "Dark"}
    _TEXT_TO_MODE = {v: k for k, v in _MODE_TO_TEXT.items()}

    def __init__(self) -> None:
        super().__init__(mw)
        self.setWindowTitle("Notepad Settings")
        self.setMinimumWidth(500)
        self.resize(550, 620)
        self._cfg = get_config()

        self._light_btn_group: QButtonGroup | None = None
        self._dark_btn_group:  QButtonGroup | None = None
        self._light_delete_btn: QPushButton | None = None
        self._dark_delete_btn:  QPushButton | None = None

        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 12)

        tabs = QTabWidget()
        tabs.addTab(self._build_general_tab(),    "General")
        tabs.addTab(self._build_appearance_tab(), "Appearance")
        tabs.addTab(self._build_themes_tab(),     "Themes")
        root.addWidget(tabs)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    # ── Tab builders ──────────────────────────────────────────────────────────

    def _build_general_tab(self) -> QWidget:
        w      = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        grp = QGroupBox("Behaviour")
        frm  = QFormLayout(grp)
        frm.setSpacing(6)
        frm.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        frm.setContentsMargins(12, 12, 12, 12)

        self.cb_clear = QCheckBox()
        self.cb_clear.setChecked(self._cfg.get("clear_on_new_card", True))
        frm.addRow("Clear text on new card:", self.cb_clear)

        self.cb_auto_open = QCheckBox()
        self.cb_auto_open.setChecked(self._cfg.get("auto_open_reviewer", False))
        frm.addRow("Auto open in reviewer:", self.cb_auto_open)

        self.cb_auto_list = QCheckBox()
        self.cb_auto_list.setChecked(self._cfg.get("auto_list", True))
        frm.addRow("Auto bulleted/numbered lists:", self.cb_auto_list)

        self.cb_remember_fmt = QCheckBox()
        self.cb_remember_fmt.setChecked(self._cfg.get("remember_formatting", True))
        frm.addRow("Remember last formatting choices:", self.cb_remember_fmt)
        layout.addWidget(grp)

        grp2 = QGroupBox("Toolbar")
        frm2  = QFormLayout(grp2)
        frm2.setSpacing(6)
        frm2.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        frm2.setContentsMargins(12, 12, 12, 12)

        self.cb_fmt = QCheckBox()
        self.cb_fmt.setChecked(self._cfg.get("show_format_buttons", True))
        self.cb_fmt.toggled.connect(self._on_fmt_toggle)
        frm2.addRow("Show toolbar buttons:", self.cb_fmt)

        self._cb_autohide_lbl = QLabel("Auto hide toolbar buttons:")
        self.cb_autohide = QCheckBox()
        self.cb_autohide.setChecked(self._cfg.get("toolbar_autohide", False))
        frm2.addRow(self._cb_autohide_lbl, self.cb_autohide)
        layout.addWidget(grp2)

        grp3 = QGroupBox("Window")
        frm3  = QFormLayout(grp3)
        frm3.setSpacing(6)
        frm3.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        frm3.setContentsMargins(12, 12, 12, 12)

        self.cb_remember_pos = QCheckBox()
        self.cb_remember_pos.setChecked(self._cfg.get("remember_position", True))
        frm3.addRow("Remember last position and size:", self.cb_remember_pos)

        self.cb_shadow = QCheckBox()
        self.cb_shadow.setChecked(self._cfg.get("window_shadow", True))
        frm3.addRow("Window shadow:", self.cb_shadow)

        self.cb_transparent = QCheckBox()
        self.cb_transparent.setChecked(self._cfg.get("window_transparent", False))
        self.cb_transparent.toggled.connect(self._on_transparent_toggle)
        frm3.addRow("Transparency:", self.cb_transparent)

        opacity_row = QHBoxLayout()
        opacity_row.setContentsMargins(0, 0, 0, 0)
        opacity_row.setSpacing(8)
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(10, 100)
        self._opacity_slider.setValue(self._cfg.get("window_opacity", 90))
        self._opacity_slider.setFixedWidth(120)
        self._opacity_label = QLabel(f"{self._opacity_slider.value()}%")
        self._opacity_label.setFixedWidth(40)
        self._opacity_slider.valueChanged.connect(
            lambda v: self._opacity_label.setText(f"{v}%")
        )
        opacity_row.addWidget(self._opacity_slider)
        opacity_row.addWidget(self._opacity_label)
        opacity_row.addStretch()
        opacity_w = QWidget()
        opacity_w.setLayout(opacity_row)
        self._opacity_row_lbl = QLabel("Opacity:")
        frm3.addRow(self._opacity_row_lbl, opacity_w)

        self.sidebar_pos = QComboBox()
        self.sidebar_pos.addItems(["Right", "Left"])
        self.sidebar_pos.setCurrentText(self._cfg.get("sidebar_position", "right").title())
        frm3.addRow("Sidebar position:", self.sidebar_pos)
        layout.addWidget(grp3)
        layout.addStretch()

        self._on_fmt_toggle(self.cb_fmt.isChecked())
        self._on_transparent_toggle(self.cb_transparent.isChecked())
        return w

    def _build_appearance_tab(self) -> QWidget:
        w      = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 8, 8, 8)

        grp = QGroupBox("Text")
        frm  = QFormLayout(grp)
        frm.setSpacing(8)
        frm.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        frm.setContentsMargins(12, 12, 12, 12)

        self.font_source = QComboBox()
        self.font_source.addItems(["Custom", "Match card font"])
        self.font_source.setCurrentText(
            "Match card font" if self._cfg.get("font_source") == "card" else "Custom"
        )
        self.font_source.currentTextChanged.connect(self._on_font_src_changed)
        frm.addRow("Font source:", self.font_source)

        self._font_combo_lbl = QLabel("Font family:")
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self._cfg.get("font_family", "Arial")))
        frm.addRow(self._font_combo_lbl, self.font_combo)

        self.font_size = QSpinBox()
        self.font_size.setRange(8, 36)
        self.font_size.setValue(self._cfg.get("font_size", 13))
        frm.addRow("Font size:", self.font_size)

        self.le_placeholder = QLineEdit(
            self._cfg.get("placeholder_text", "Write anything here\u2026")
        )
        self.le_placeholder.setPlaceholderText("(leave blank for none)")
        frm.addRow("Placeholder text:", self.le_placeholder)
        layout.addWidget(grp)

        grp2 = QGroupBox("Border")
        frm2  = QFormLayout(grp2)
        frm2.setSpacing(8)
        frm2.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        frm2.setContentsMargins(12, 12, 12, 12)

        self.border_style = QComboBox()
        self.border_style.addItems(["None", "Accent", "Custom"])
        current_style = self._cfg.get("border_style", "custom")
        self.border_style.setCurrentText(current_style.title())
        self.border_style.currentTextChanged.connect(self._on_border_style_changed)
        frm2.addRow("Border style:", self.border_style)

        # Custom border color picker (shown when "Custom" is selected)
        self.custom_border_color_row = QHBoxLayout()
        self.custom_border_color_row.setContentsMargins(16, 0, 0, 0)
        # Default to empty string (will use sidebar background color)
        current_custom_color = self._cfg.get("custom_border_color", "")
        if not current_custom_color:
            current_custom_color = "#CCCCCC"  # Fallback for display
        self.btn_custom_border = self._colour_btn(current_custom_color)
        self.btn_custom_border.clicked.connect(lambda: self._pick_colour(self.btn_custom_border))
        self.custom_border_color_row.addWidget(QLabel("Custom color:"))
        self.custom_border_color_row.addWidget(self.btn_custom_border)
        self.custom_border_color_row.addStretch()
        custom_border_w = QWidget()
        custom_border_w.setLayout(self.custom_border_color_row)
        frm2.addRow("", custom_border_w)

        self.cb_sidebar_hide_border = QCheckBox("Hide border in sidebar view")
        self.cb_sidebar_hide_border.setChecked(self._cfg.get("sidebar_hide_border", False))
        frm2.addRow("", self.cb_sidebar_hide_border)

        self.border_radius = QSpinBox()
        self.border_radius.setRange(0, 20)
        self.border_radius.setValue(self._cfg.get("border_radius", 6))
        self.border_radius.setSuffix(" px")
        frm2.addRow("Border radius:", self.border_radius)
        layout.addWidget(grp2)

        # Window shadow options
        shadow_grp = QGroupBox("Window Shadow")
        shadow_row = QHBoxLayout(shadow_grp)
        shadow_row.setContentsMargins(12, 12, 12, 12)
        shadow_row.setSpacing(10)
        shadow_row.addWidget(QLabel("Shadow style:"))
        self.shadow_style = QComboBox()
        self.shadow_style.addItems(["Standard", "Subtle", "Custom"])
        current_shadow = self._cfg.get("shadow_style", "standard")
        self.shadow_style.setCurrentText(current_shadow.title())
        self.shadow_style.currentTextChanged.connect(self._on_shadow_style_changed)
        shadow_row.addWidget(self.shadow_style)
        shadow_row.addStretch()
        layout.addWidget(shadow_grp)

        # Custom shadow controls (shown when "Custom" is selected)
        custom_shadow_grp = QGroupBox("Custom Shadow Settings")
        custom_shadow_layout = QVBoxLayout(custom_shadow_grp)
        custom_shadow_layout.setContentsMargins(12, 12, 12, 12)
        custom_shadow_layout.setSpacing(8)

        # Blur radius
        blur_row = QHBoxLayout()
        blur_row.addWidget(QLabel("Blur radius:"))
        self.shadow_blur = QSpinBox()
        self.shadow_blur.setRange(0, 50)
        self.shadow_blur.setValue(self._cfg.get("custom_shadow_blur", 12))
        self.shadow_blur.setSuffix(" px")
        blur_row.addWidget(self.shadow_blur)
        blur_row.addStretch()
        custom_shadow_layout.addLayout(blur_row)

        # Y offset
        offset_row = QHBoxLayout()
        offset_row.addWidget(QLabel("Y offset:"))
        self.shadow_offset = QSpinBox()
        self.shadow_offset.setRange(0, 50)
        self.shadow_offset.setValue(self._cfg.get("custom_shadow_offset", 4))
        self.shadow_offset.setSuffix(" px")
        offset_row.addWidget(self.shadow_offset)
        offset_row.addStretch()
        custom_shadow_layout.addLayout(offset_row)

        # Color
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color:"))
        self.shadow_color = QLineEdit()
        self.shadow_color.setText(self._cfg.get("custom_shadow_color", "rgba(0,0,0,0.1)"))
        self.shadow_color.setPlaceholderText("e.g., rgba(0,0,0,0.1) or #000000")
        color_row.addWidget(self.shadow_color)
        color_row.addStretch()
        custom_shadow_layout.addLayout(color_row)

        layout.addWidget(custom_shadow_grp)
        layout.addStretch()

        self._on_font_src_changed(self.font_source.currentText())
        self._on_border_style_changed(self.border_style.currentText())
        self._on_shadow_style_changed(self.shadow_style.currentText())
        return w

    def _build_themes_tab(self) -> QWidget:
        w      = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 8, 8, 8)

        # Mode selector
        mode_grp = QGroupBox("Theme Mode")
        mode_row = QHBoxLayout(mode_grp)
        mode_row.setContentsMargins(12, 12, 12, 12)
        mode_row.setSpacing(10)
        mode_row.addWidget(QLabel("Colour mode:"))
        self.theme_mode = QComboBox()
        self.theme_mode.addItems(list(self._MODE_TO_TEXT.values()))
        current_mode = self._cfg.get("theme_mode", "follow")
        self.theme_mode.setCurrentText(
            self._MODE_TO_TEXT.get(current_mode, "Follow Anki")
        )
        mode_row.addWidget(self.theme_mode)
        mode_row.addStretch()
        layout.addWidget(mode_grp)

        # Colour grids
        colour_grp    = QGroupBox("Colour selection")
        colour_layout = QVBoxLayout(colour_grp)
        colour_layout.setSpacing(8)
        colour_layout.setContentsMargins(12, 12, 12, 12)

        # Light section
        self._light_section = QWidget()
        light_inner = QVBoxLayout(self._light_section)
        light_inner.setContentsMargins(0, 0, 0, 0)
        light_inner.setSpacing(6)
        light_inner.addWidget(QLabel("Light Mode Theme:"))
        self.light_theme_grid, self._light_btn_group = self._build_theme_grid("light")
        light_inner.addWidget(self.light_theme_grid)
        
        # Delete button in its own horizontal layout for right alignment
        light_btn_layout = QHBoxLayout()
        light_btn_layout.setContentsMargins(0, 20, 5, 20)  # Much more top/bottom margin
        light_btn_layout.addStretch()
        self._light_delete_btn = self._build_delete_btn("light")
        light_btn_layout.addWidget(self._light_delete_btn)
        light_inner.addLayout(light_btn_layout)
        
        colour_layout.addWidget(self._light_section)

        # Dark section
        self._dark_section = QWidget()
        dark_inner = QVBoxLayout(self._dark_section)
        dark_inner.setContentsMargins(0, 0, 0, 0)
        dark_inner.setSpacing(6)
        dark_inner.addWidget(QLabel("Dark Mode Theme:"))
        self.dark_theme_grid, self._dark_btn_group = self._build_theme_grid("dark")
        dark_inner.addWidget(self.dark_theme_grid)
        
        # Delete button in its own horizontal layout for right alignment
        dark_btn_layout = QHBoxLayout()
        dark_btn_layout.setContentsMargins(0, 20, 5, 20)  # Much more top/bottom margin
        dark_btn_layout.addStretch()
        self._dark_delete_btn = self._build_delete_btn("dark")
        dark_btn_layout.addWidget(self._dark_delete_btn)
        dark_inner.addLayout(dark_btn_layout)
        
        colour_layout.addWidget(self._dark_section)

        layout.addWidget(colour_grp)
        layout.addStretch()

        # Apply initial visibility THEN connect signal so it doesn't fire prematurely
        self._apply_mode_visibility(current_mode)
        self.theme_mode.currentTextChanged.connect(self._on_theme_mode_changed)
        
        return w

    # ── Theme data helpers ────────────────────────────────────────────────────

    def _effective_themes(self, mode: str) -> dict[str, ThemeColors]:
        """
        Return the ordered dict of themes for this mode, with any saved custom
        overrides merged in.  Purely new custom themes are appended at the end.
        """
        cfg      = get_config()
        is_dark  = mode == "dark"
        raw_key  = f"custom_{'dark' if is_dark else 'light'}_themes"
        predefined = get_available_themes(is_dark)
        custom_raw = cfg.get(raw_key, {})

        result: dict[str, ThemeColors] = {}

        # Predefined themes — replaced by custom override if one exists for that key
        for key, theme in predefined.items():
            if key in custom_raw:
                d = custom_raw[key]
                result[key] = ThemeColors(
                    name=d["name"],
                    buttons=d["buttons"],
                    main_background=d["main_background"],
                    toolbar=d["toolbar"],
                    accent=d.get("accent", ""),
                    text=d.get("text", ""),
                )
            else:
                result[key] = theme

        # Purely custom themes (keys not present in predefined)
        for key, d in custom_raw.items():
            if key not in predefined:
                result[key] = ThemeColors(
                    name=d["name"],
                    buttons=d["buttons"],
                    main_background=d["main_background"],
                    toolbar=d["toolbar"],
                    accent=d.get("accent", ""),
                    text=d.get("text", ""),
                )

        return result

    # ── Theme grid construction ───────────────────────────────────────────────

    def _build_theme_grid(self, mode: str) -> tuple[QWidget, QButtonGroup]:
        """
        Build a 4-column grid of ThemeWidgets plus an _AddThemeButton.

        Returns (container, QButtonGroup).  The group is exclusive so exactly
        one theme is always selected — deselection is not possible.
        """
        themes      = self._effective_themes(mode)
        current_key = get_config().get(f"{mode}_theme", "blue")
        
        # Get predefined themes to identify custom ones
        predefined_themes = get_available_themes(mode == "dark")

        container = QWidget()
        grid      = QGridLayout(container)
        grid.setSpacing(16)
        grid.setContentsMargins(0, 0, 0, 0)

        btn_group = QButtonGroup(container)
        btn_group.setExclusive(True)

        cols = 4
        for idx, (key, theme) in enumerate(themes.items()):
            widget = ThemeWidget(key, theme, mode, self)
            btn = widget.get_button()
            btn.setChecked(key == current_key)
            btn._apply_style(selected=(key == current_key))
            grid.addWidget(widget, idx // cols, idx % cols)
            btn_group.addButton(btn)

        # + button sits at next grid position; not part of the exclusive group
        plus_idx = len(themes)
        grid.addWidget(_AddThemeButton(mode, self), plus_idx // cols, plus_idx % cols)

        btn_group.buttonToggled.connect(self._on_group_toggled)
        return container, btn_group

    def _rebuild_grid(self, mode: str) -> None:
        """
        Replace existing grid widget in section layout with a fresh one.
        Called after a theme is edited or a new theme is created.
        """
        section      = self._light_section if mode == "light" else self._dark_section
        inner_layout = section.layout()

        # Remove only the grid widget (index 1), keep the button layout (index 2)
        grid_item = inner_layout.itemAt(1)
        if grid_item and grid_item.widget():
            grid_item.widget().deleteLater()

        new_grid, new_group = self._build_theme_grid(mode)
        inner_layout.insertWidget(1, new_grid)

        # Refresh delete button state
        self._refresh_delete_btn(mode)

        if mode == "light":
            self.light_theme_grid = new_grid
            self._light_btn_group = new_group
        else:
            self.dark_theme_grid = new_grid
            self._dark_btn_group = new_group

    def _build_delete_btn(self, mode: str) -> QPushButton:
        """Create delete button for theme section."""
        btn = QPushButton("Delete")
        btn.setEnabled(False)  # Start disabled for default themes
        btn.setToolTip("Delete selected custom theme")
        btn.clicked.connect(lambda: self._delete_selected_theme(mode))
        return btn

    def _refresh_delete_btn(self, mode: str) -> None:
        """Enable delete button only when a custom theme is selected."""
        btn = self._light_delete_btn if mode == "light" else self._dark_delete_btn
        if not btn:
            return

        group = self._light_btn_group if mode == "light" else self._dark_btn_group
        if not group or not group.checkedButton():
            btn.setEnabled(False)
            return

        selected_key = group.checkedButton()._key
        predefined_themes = get_available_themes(mode == "dark")
        is_custom = selected_key not in predefined_themes
        btn.setEnabled(is_custom)

    def _delete_selected_theme(self, mode: str) -> None:
        """Delete the currently selected custom theme."""
        group = self._light_btn_group if mode == "light" else self._dark_btn_group
        if not group or not group.checkedButton():
            return

        selected_key = group.checkedButton()._key
        predefined_themes = get_available_themes(mode == "dark")
        
        # Never allow deletion of predefined themes
        if selected_key in predefined_themes:
            return  # Don't delete predefined themes

        # Get theme name for confirmation dialog
        themes = self._effective_themes(mode)
        theme = themes.get(selected_key)
        theme_name = theme.name if theme else "Unknown Theme"

        reply = QMessageBox.question(
            self,
            "Delete Theme",
            f"Are you sure you want to delete the theme '{theme_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._delete_theme(selected_key, mode)

    # ── Theme editing ─────────────────────────────────────────────────────────

    def _edit_theme(self, key: str, mode: str) -> None:
        """
        Open the theme editor for the given key.  Loads the effective theme
        (custom override if it exists, otherwise predefined) so the editor
        always starts from the current saved state.
        """
        from .theme_editor import open_theme_editor

        themes = self._effective_themes(mode)
        theme  = themes.get(key)
        if theme is None:
            return

        edited = open_theme_editor(key, theme, mode == "dark", self)
        if edited is None:
            return

        self._persist_custom_theme(key, mode, edited)
        self._rebuild_grid(mode)
        apply_current_theme()

    def _add_new_theme(self, mode: str) -> None:
        """Create a brand new custom theme and add it to the grid."""
        from .theme_editor import open_theme_editor

        default = ThemeColors(
            name="Custom",
            buttons="#424242" if mode == "light" else "#000000",
            main_background="#FFFFFF" if mode == "light" else "#2A2A2A",
            toolbar="#F8F8F8" if mode == "light" else "#3A3A3A",
            accent="#5B9BF8",
        )

        # Generate a key that doesn't clash with existing custom themes
        cfg         = get_config()
        raw_key     = f"custom_{'dark' if mode == 'dark' else 'light'}_themes"
        existing    = cfg.get(raw_key, {})
        n           = 1
        while f"custom_{n}" in existing:
            n += 1
        new_key = f"custom_{n}"

        edited = open_theme_editor(new_key, default, mode == "dark", self)
        if edited is None:
            return

        self._persist_custom_theme(new_key, mode, edited)

        # Select the newly created theme
        cfg = get_config()
        cfg[f"{mode}_theme"] = new_key
        save_config(cfg)

        self._rebuild_grid(mode)
        apply_current_theme()

    def _delete_theme(self, key: str, mode: str) -> None:
        """Delete a custom theme from the configuration."""
        cfg = get_config()
        raw_key = f"custom_{'dark' if mode == 'dark' else 'light'}_themes"
        custom = cfg.get(raw_key, {})
        
        if key in custom:
            del custom[key]
            cfg[raw_key] = custom
            
            # If the deleted theme was currently selected, fallback to blue
            if cfg.get(f"{mode}_theme") == key:
                cfg[f"{mode}_theme"] = "blue"
            
            save_config(cfg)
            self._rebuild_grid(mode)
            apply_current_theme()

    @staticmethod
    def _persist_custom_theme(key: str, mode: str, theme: ThemeColors) -> None:
        """Write a custom theme override to config."""
        cfg     = get_config()
        raw_key = f"custom_{'dark' if mode == 'dark' else 'light'}_themes"
        custom  = cfg.get(raw_key, {})
        custom[key] = {
            "name":            theme.name,
            "buttons":         theme.buttons,
            "main_background": theme.main_background,
            "toolbar":         theme.toolbar,
            "accent":          theme.accent,
            "text":            theme.text,
        }
        cfg[raw_key] = custom
        save_config(cfg)

    # ── Visibility control ────────────────────────────────────────────────────

    def _apply_mode_visibility(self, mode: str) -> None:
        # Show/hide labels based on mode
        light_label = self._light_section.layout().itemAt(0).widget()
        dark_label = self._dark_section.layout().itemAt(0).widget()
        
        light_label.setVisible(mode == "follow")
        dark_label.setVisible(mode == "follow")
        
        # Show only the appropriate theme grid
        self._light_section.setVisible(mode in ("follow", "light"))
        self._dark_section.setVisible(mode in ("follow", "dark"))

    # ── Slot handlers ─────────────────────────────────────────────────────────

    def _on_group_toggled(self, btn: QToolButton, checked: bool) -> None:
        if not checked or not isinstance(btn, ThemeCircleButton):
            return
        group = self._light_btn_group if btn._mode == "light" else self._dark_btn_group
        for b in group.buttons():
            if isinstance(b, ThemeCircleButton):
                b._apply_style(selected=(b is btn))
        cfg = get_config()
        cfg[f"{btn._mode}_theme"] = btn._key
        save_config(cfg)
        apply_current_theme()
        
        # Refresh delete button state
        self._refresh_delete_btn(btn._mode)

    def _on_theme_mode_changed(self, text: str) -> None:
        mode = self._TEXT_TO_MODE.get(text, "follow")
        self._apply_mode_visibility(mode)
        cfg              = get_config()
        cfg["theme_mode"] = mode
        save_config(cfg)
        apply_current_theme()

    def _on_fmt_toggle(self, checked: bool) -> None:
        self.cb_autohide.setEnabled(checked)
        self._cb_autohide_lbl.setEnabled(checked)

    def _on_font_src_changed(self, text: str) -> None:
        custom = text == "Custom"
        self.font_combo.setEnabled(custom)
        self._font_combo_lbl.setEnabled(custom)

    def _on_transparent_toggle(self, checked: bool) -> None:
        self._opacity_slider.setEnabled(checked)
        self._opacity_label.setEnabled(checked)
        self._opacity_row_lbl.setEnabled(checked)

    def _on_border_toggle(self, checked: bool) -> None:
        self.cb_border_accent.setEnabled(checked)

    def _on_border_style_changed(self, text: str) -> None:
        # Show/hide custom color picker based on selection
        show_custom = text.lower() == "custom"
        custom_border_w = self.custom_border_color_row.parent()
        custom_border_w.setVisible(show_custom)

    def _on_shadow_style_changed(self, text: str) -> None:
        # Show/hide custom shadow settings based on selection
        show_custom = text.lower() == "custom"
        # Find the custom shadow group widget
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if widget and isinstance(widget, QGroupBox) and widget.title() == "Custom Shadow Settings":
                widget.setVisible(show_custom)
                break

    # ── Colour picker helpers ─────────────────────────────────────────────────

    @staticmethod
    def _colour_btn(hex_color: str) -> QToolButton:
        btn = QToolButton()
        btn.setText(hex_color)
        btn.setFixedHeight(28)
        SettingsDialog._apply_colour(btn, hex_color)
        return btn

    @staticmethod
    def _apply_colour(btn: QToolButton, hex_color: str) -> None:
        c   = QColor(hex_color)
        lum = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
        btn.setStyleSheet(
            f"background-color:{hex_color};"
            f"color:{'#000' if lum > 128 else '#FFF'};"
            "border:1px solid #888;border-radius:4px;padding:4px 8px;"
        )

    def _pick_colour(self, btn: QToolButton) -> None:
        colour = QColorDialog.getColor(QColor(btn.text()), self)
        if colour.isValid():
            btn.setText(colour.name())
            self._apply_colour(btn, colour.name())

    # ── Read current selection ────────────────────────────────────────────────

    def _selected_theme_key(self, mode: str) -> str:
        group   = self._light_btn_group if mode == "light" else self._dark_btn_group
        checked = group.checkedButton() if group else None
        return checked._key if isinstance(checked, ThemeCircleButton) else "blue"

    # ── Save (OK button) ──────────────────────────────────────────────────────

    def _save(self) -> None:
        remember   = self.cb_remember_pos.isChecked()
        existing   = get_config()
        theme_mode = self._TEXT_TO_MODE.get(self.theme_mode.currentText(), "follow")

        cfg = {
            # Behaviour
            "clear_on_new_card":    self.cb_clear.isChecked(),
            "auto_open_reviewer":   self.cb_auto_open.isChecked(),
            "auto_list":            self.cb_auto_list.isChecked(),
            "remember_formatting":  self.cb_remember_fmt.isChecked(),
            # Toolbar
            "show_format_buttons":  self.cb_fmt.isChecked(),
            "toolbar_autohide":     self.cb_autohide.isChecked(),
            # Text / font
            "font_source":   "card" if self.font_source.currentText() == "Match card font" else "custom",
            "font_family":   self.font_combo.currentFont().family(),
            "font_size":     self.font_size.value(),
            "placeholder_text": self.le_placeholder.text(),
            # Border
            "border_style":         self.border_style.currentText().lower(),
            "custom_border_color":  self.btn_custom_border.text(),
            "sidebar_hide_border":  self.cb_sidebar_hide_border.isChecked(),
            "border_radius":        self.border_radius.value(),
            # Window
            "remember_position":    remember,
            "window_shadow":        self.cb_shadow.isChecked(),
            "shadow_style":         self.shadow_style.currentText().lower(),
            "custom_shadow_blur":    self.shadow_blur.value(),
            "custom_shadow_offset":  self.shadow_offset.value(),
            "custom_shadow_color":  self.shadow_color.text(),
            "window_transparent":   self.cb_transparent.isChecked(),
            "window_opacity":       self._opacity_slider.value(),
            "sidebar_position":     self.sidebar_pos.currentText().lower(),
            # Themes
            "theme_mode":    theme_mode,
            "light_theme":   self._selected_theme_key("light"),
            "dark_theme":    self._selected_theme_key("dark"),
            # Preserved values
            "windowed":      existing.get("windowed", False),
            "windowed_x":    existing.get("windowed_x")           if remember else None,
            "windowed_y":    existing.get("windowed_y")           if remember else None,
            "windowed_width":  existing.get("windowed_width",  250) if remember else 250,
            "windowed_height": existing.get("windowed_height", 350) if remember else 350,
        }
        save_config(cfg)
        apply_current_theme()
        self.accept()


# ── Entry point ───────────────────────────────────────────────────────────────

def open_settings() -> None:
    """Open the settings dialog; reposition dock if sidebar side changed."""
    dialog = SettingsDialog()
    # Refresh delete button states after dialog is fully created
    dialog._refresh_delete_btn("light")
    dialog._refresh_delete_btn("dark")
    if dialog.exec() != QDialog.DialogCode.Accepted:
        dialog.deleteLater()
        return

    if state.dock is None:
        return

    cfg         = get_config()
    sidebar_pos = cfg.get("sidebar_position", "right")
    target_area = (
        Qt.DockWidgetArea.RightDockWidgetArea
        if sidebar_pos == "right"
        else Qt.DockWidgetArea.LeftDockWidgetArea
    )
    if mw.dockWidgetArea(state.dock) != target_area:
        mw.removeDockWidget(state.dock)
        mw.addDockWidget(target_area, state.dock)
        if state.dock.isVisible():
            state.dock.show_in_dock()
