"""config.py — Configuration defaults, read/write helpers, and theme colour utilities."""
from aqt import mw

# Layout constants shared across the addon
SHADOW_M      = 80            # transparent margin (px) around NotepadWindow for drop-shadow
RESIZE_EDGE   = SHADOW_M + 5  # px from window edge that activates resize cursors/drag
MIN_CONTENT_W = 160
MIN_CONTENT_H = 120

# Resolve the addon's package name from __name__ so getConfig/writeConfig
# receive the correct folder-based key regardless of which sub-module calls them.
_ADDON_NAME = __name__.split(".")[0]

DEFAULTS: dict = {
    "clear_on_new_card":    True,
    "auto_open_reviewer":   False,
    "show_format_buttons":  True,
    "toolbar_autohide":     False,
    "auto_list":            True,
    "placeholder_text":     "Write anything here\u2026",
    "font_source":          "custom",
    "font_family":          "Arial",
    "font_size":            13,
    # Theme system replaces individual color settings
    "theme_mode":           "follow",  # "light", "dark", or "follow"
    "light_theme":          "blue",
    "dark_theme":           "blue", 
    "custom_light_themes":  {},  # JSON object for custom themes
    "custom_dark_themes":   {},  # JSON object for custom themes
    # Border settings
    "editor_show_border":   True,
    "border_style":         "custom",  # "none", "accent", "custom"
    "custom_border_color":  "",  # Empty string means use sidebar color
    "sidebar_hide_border":  False,  # Hide border in sidebar view
    "border_radius":        6,
    # Window settings
    "windowed":             False,
    "remember_position":    True,
    "windowed_x":           None,
    "windowed_y":           None,
    "windowed_width":       250,
    "windowed_height":      350,
    "docked_min_width":     160,
    "docked_default_width": 240,
    "window_shadow":        True,
    "shadow_style":         "standard",  # "standard", "subtle", or "custom"
    "custom_shadow_blur":   12,
    "custom_shadow_offset": 4,
    "custom_shadow_color": "rgba(0,0,0,0.1)",
    "window_transparent":   False,
    "window_opacity":       90,
    "sidebar_position":     "right",
    "remember_formatting":  True,
    # Legacy color settings (kept for migration, will be removed)
    "editor_bg_dark":       "#1E1E1E",
    "editor_bg_light":      "#FFFFFF",
    "toolbar_bg_dark":      "#3A3A3A",
    "toolbar_bg_light":     "#F8F8F8",
    "text_color_dark":      "#ECECEC",
    "text_color_light":     "#1A1A1A",
    "editor_border_accent": False,
    "accent_dark":          "#5B9BF8",
    "accent_light":         "#5B9BF8",
}


def get_config() -> dict:
    """Return the full config merged with DEFAULTS (stored values take precedence)."""
    raw = mw.addonManager.getConfig(_ADDON_NAME) or {}
    needs_save = False
    
    # Migrate legacy single accent key to dark/light pair
    if "accent" in raw and "accent_dark" not in raw and "accent_light" not in raw:
        raw["accent_dark"] = raw["accent"]
        raw["accent_light"] = raw["accent"]
        needs_save = True
    
    # Migrate to theme system if old color settings exist but no theme settings
    if "theme_mode" not in raw:
        raw["theme_mode"] = "follow"
        raw["light_theme"] = "blue" 
        raw["dark_theme"] = "blue"
        raw["custom_light_themes"] = {}
        raw["custom_dark_themes"] = {}
        needs_save = True
    
    # Migrate old custom_themes to mode-specific structure
    if "custom_themes" in raw:
        old_custom_themes = raw["custom_themes"]
        if "custom_light_themes" not in raw:
            raw["custom_light_themes"] = {}
        if "custom_dark_themes" not in raw:
            raw["custom_dark_themes"] = {}
        
        # Move existing custom themes to appropriate dictionaries
        # We need to determine which mode they were originally created for
        # For now, we'll copy all custom themes to both light and dark to preserve them
        for theme_key, theme_data in old_custom_themes.items():
            # Copy to both dictionaries to preserve custom themes
            raw["custom_light_themes"][theme_key] = theme_data
            raw["custom_dark_themes"][theme_key] = theme_data
        
        # Remove old custom_themes key
        del raw["custom_themes"]
        needs_save = True
    
    # Add new border and shadow settings if they don't exist
    if "border_style" not in raw:
        # Migrate from old border settings
        if raw.get("editor_border_accent", False):
            raw["border_style"] = "accent"
        elif not raw.get("editor_show_border", True):
            raw["border_style"] = "none"
        else:
            raw["border_style"] = "custom"
        needs_save = True
    
    if "sidebar_hide_border" not in raw:
        raw["sidebar_hide_border"] = False
        needs_save = True
    
    if "shadow_style" not in raw:
        raw["shadow_style"] = "standard"
        needs_save = True
    
    # Save immediately if migration happened
    if needs_save:
        save_config(raw)
    
    return {**DEFAULTS, **raw}


def save_config(cfg: dict) -> None:
    try:
        # Get the existing config to preserve custom themes if they're missing
        existing_cfg = mw.addonManager.getConfig(_ADDON_NAME) or {}
        
        # If new config doesn't have custom themes, use existing ones
        if 'custom_light_themes' not in cfg and 'custom_light_themes' in existing_cfg:
            cfg['custom_light_themes'] = existing_cfg['custom_light_themes']
        if 'custom_dark_themes' not in cfg and 'custom_dark_themes' in existing_cfg:
            cfg['custom_dark_themes'] = existing_cfg['custom_dark_themes']
        
        # Write the config
        mw.addonManager.writeConfig(_ADDON_NAME, cfg)
            
    except Exception:
        pass


def is_dark_mode() -> bool:
    try:
        return mw.pm.night_mode()
    except Exception:
        return False


def theme_color(
    cfg: dict,
    dark_key: str,
    light_key: str,
    default_dark: str,
    default_light: str,
    is_dark: bool,
) -> str:
    """Return the appropriate colour string for the current theme."""
    key     = dark_key    if is_dark else light_key
    default = default_dark if is_dark else default_light
    return cfg.get(key, default)


def default_windowed_geometry() -> tuple[int, int, int, int]:
    """
    Compute the default windowed position relative to the main Anki window.

    Position: 100 px from the right edge, vertically centred and shifted 50 px up.
    Returns (x, y, win_w, win_h) where win dimensions include SHADOW_M on each side.
    """
    try:
        content_w, content_h = 250, 350
        win_w  = content_w + 2 * SHADOW_M
        win_h  = content_h + 2 * SHADOW_M
        mw_g   = mw.geometry()
        x      = mw_g.right() - win_w - 100
        y      = mw_g.center().y() - win_h // 2 - 50
        return x, y, win_w, win_h
    except Exception:
        return 60, 60, 250 + 2 * SHADOW_M, 350 + 2 * SHADOW_M
