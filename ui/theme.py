"""ui/theme.py — Shared theming helpers applied to both docked and windowed modes."""
from aqt.qt import QFont, Qt

from ..config import get_config, is_dark_mode
from ..themes import get_theme, ThemeConfig
from .. import state
from .toolbar import OverlayToolbar, TOOLBAR_H


def apply_common_theme(cfg: dict, dark: bool, floating: bool) -> None:
    """
    Apply styling common to both modes.
    floating=True  → windowed mode
    floating=False → docked/sidebar
    """
    if not (state.editor and state.pane):
        return

    tb = state.pane.toolbar()
    pad = 5

    # Get theme-based colors
    try:
        theme_config = ThemeConfig(
            mode=cfg.get("theme_mode", "follow"),
            light_theme=cfg.get("light_theme", "blue"),
            dark_theme=cfg.get("dark_theme", "blue"),
            custom_light_themes=cfg.get("custom_light_themes", {}),
            custom_dark_themes=cfg.get("custom_dark_themes", {}),
        )
        
        current_theme = get_theme(theme_config, dark)
        
        # Use theme-specific accent color, fallback to global if not set
        accent = current_theme.accent if current_theme.accent else cfg.get("accent_dark" if dark else "accent_light", "#5B9BF8")
        
        # Theme-based colors
        fg = current_theme.text
        editor_bg = current_theme.main_background
        toolbar_bg = current_theme.toolbar
        buttons_color = current_theme.buttons
        
        icon_color = "#AAAAAA" if dark else "#666666"
        
    except Exception:
        accent = cfg.get("accent_dark" if dark else "accent_light", "#5B9BF8")
        fg = "#ECECEC" if dark else "#1A1A1A"
        editor_bg = "#1E1E1E" if dark else "#FFFFFF"
        toolbar_bg = "#3A3A3A" if dark else "#F8F8F8"
        buttons_color = "#424242"
        icon_color = "#AAAAAA" if dark else "#666666"

    border_radius = cfg.get("border_radius", 6)
    show_border   = cfg.get("editor_show_border", True)
    border_accent = cfg.get("editor_border_accent", False)
    border_style  = cfg.get("border_style", "custom")  # "none", "accent", "custom"
    custom_border_color = cfg.get("custom_border_color", "")
    sidebar_hide_border = cfg.get("sidebar_hide_border", False)
    show_toolbar  = cfg.get("show_format_buttons", True)
    autohide      = cfg.get("toolbar_autohide", False) and show_toolbar
    placeholder   = cfg.get("placeholder_text", "Write anything here\u2026")
    font_source   = cfg.get("font_source", "custom")

    # ── Font ──────────────────────────────────────────────────────────────────
    ff   = cfg.get("font_family", "Arial")
    size = cfg.get("font_size", 13)
    if font_source == "card" and state.card_font:
        state.editor.setFont(QFont(state.card_font, size))
    else:
        state.editor.setFont(QFont(ff, size))

    state.editor.setPlaceholderText(placeholder)
    state.editor.set_auto_list(cfg.get("auto_list", True))

    # ── Toolbar ───────────────────────────────────────────────────────────────
    tb.setVisible(True)
    tb.set_format_buttons_visible(show_toolbar)
    tb.set_autohide(autohide)

    for btn in (tb._btn_bold, tb._btn_italic, tb._btn_underline):
        btn.update_colors(buttons_color, accent, dark)
    tb._btn_view.update_colors(buttons_color, accent, dark)
    tb._btn_close.update_colors(buttons_color, accent, dark)

    # ── Editor border ─────────────────────────────────────────────────────────
    if floating:
        # Border is on the NotepadWindow inner frame; editor has no border
        editor_border = "none"
        editor_radius = 0
    else:
        # Sidebar: square corners; border based on settings
        editor_radius = 0
        if sidebar_hide_border or not show_border:
            editor_border = "none"
        elif border_style == "none":
            editor_border = "none"
        elif border_style == "accent":
            editor_border = f"1px solid {accent}"
        elif border_style == "custom":
            if custom_border_color:
                editor_border = f"1px solid {custom_border_color}"
            else:
                # Default to sidebar background color
                editor_border = f"1px solid {editor_bg}"
        else:
            # Fallback to old logic
            if border_accent:
                editor_border = f"1px solid {accent}"
            else:
                editor_border = f"1px solid {'#404040' if dark else '#CCCCCC'}"

    # ── Editor stylesheet ─────────────────────────────────────────────────────
    state.editor.setStyleSheet(f"""
        QTextEdit {{
            background-color: {'transparent' if floating else editor_bg};
            color: {fg};
            border: {editor_border};
            border-radius: {editor_radius}px;
            padding: 7px;
            selection-background-color: {accent};
        }}
        QScrollBar:vertical {{
            border: none; background: transparent; width: 6px;
            margin: {TOOLBAR_H + pad}px 0px 0px 0px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        QScrollBar::handle:vertical {{
            background: rgba(128,128,128,0.6); border-radius: 3px;
            min-height: 20px; border: none; width: 3px; outline: none;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(128,128,128,0.8); border-radius: 3px;
            border: none; width: 3px; outline: none;
        }}
    """)

    # ── Viewport transparency ─────────────────────────────────────────────────
    if floating:
        state.editor.viewport().setAutoFillBackground(False)
        state.editor.viewport().setStyleSheet("background: transparent;")
    else:
        state.editor.viewport().setAutoFillBackground(True)
        state.editor.viewport().setStyleSheet("")

    # ── Toolbar stylesheet ─────────────────────────────────────────────────────
    if floating:
        toolbar_radius = max(2, border_radius - 5)
    else:
        # Sidebar: fixed 5px radius for toolbar
        toolbar_radius = 5
        
    tb.setObjectName("NotepadToolbar")
    tb.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    tb.setStyleSheet(f"""
        QWidget#NotepadToolbar {{
            background-color: {toolbar_bg};
            border-radius: {toolbar_radius}px;
        }}
    """)


def apply_current_theme() -> None:
    """Re-apply theme to whichever mode is currently active."""
    if state.in_windowed_mode and state.win:
        state.win.apply_theme()
    elif state.dock:
        state.dock.apply_theme()
