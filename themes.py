"""themes.py — Color theme definitions and management for the notepad addon."""

from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class ThemeColors:
    """Color definitions for a single theme."""
    name: str
    buttons: str
    main_background: str
    toolbar: str
    accent: str = ""  # Theme-specific accent color
    text: str = ""  # Will be set based on theme background
    
    def __post_init__(self):
        # Auto-calculate appropriate text color based on background brightness
        if not self.text:
            self.text = self._calculate_text_color(self.main_background)
    
    @staticmethod
    def _calculate_text_color(background: str) -> str:
        """Calculate appropriate text color (black or white) based on background."""
        # Remove # if present
        hex_color = background.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Calculate luminance using standard formula
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        
        # Return black for light backgrounds, white for dark
        return "#1A1A1A" if luminance > 128 else "#ECECEC"


# Light mode themes
LIGHT_THEMES: Dict[str, ThemeColors] = {
    "yellow": ThemeColors(
        name="Yellow",
        buttons="#424242",
        main_background="#FFF6CB",
        toolbar="#F2DD65",
        accent="#FFA500"
    ),
    "green": ThemeColors(
        name="Green", 
        buttons="#424242",
        main_background="#E7F6E4",
        toolbar="#C0DEB9",
        accent="#32CD32"
    ),
    "pink": ThemeColors(
        name="Pink",
        buttons="#424242", 
        main_background="#FFE3F1",
        toolbar="#F1B4D2",
        accent="#FF69B4"
    ),
    "purple": ThemeColors(
        name="Purple",
        buttons="#424242",
        main_background="#F2E5FF", 
        toolbar="#D4C0EA",
        accent="#9370DB"
    ),
    "blue": ThemeColors(
        name="Blue",
        buttons="#424242",
        main_background="#E7F3FF",
        toolbar="#BFD9F4",
        accent="#0282FA"
    ),
    "gray": ThemeColors(
        name="Gray",
        buttons="#424242",
        main_background="#EDEBE9",
        toolbar="#CCCCCC",
        accent="#708090"
    ),
    "charcoal": ThemeColors(
        name="Charcoal",
        buttons="#424242",
        main_background="#5E5E5E",
        toolbar="#7E7E7E",
        accent="#696969"
    ),
}

# Dark mode themes
DARK_THEMES: Dict[str, ThemeColors] = {
    "yellow": ThemeColors(
        name="Yellow",
        buttons="#000000",
        main_background="#816C01",
        toolbar="#EBC91E",
        accent="#FFA500"
    ),
    "green": ThemeColors(
        name="Green", 
        buttons="#000000",
        main_background="#355C2F",
        toolbar="#7EC974",
        accent="#32CD32"
    ),
    "pink": ThemeColors(
        name="Pink",
        buttons="#000000",
        main_background="#855171",
        toolbar="#EF9DD0",
        accent="#FF69B4"
    ),
    "purple": ThemeColors(
        name="Purple",
        buttons="#000000",
        main_background="#5D4772",
        toolbar="#D4A5FF",
        accent="#9370DB"
    ),
    "blue": ThemeColors(
        name="Blue",
        buttons="#000000",
        main_background="#346475",
        toolbar="#67BEDD",
        accent="#0282FA"
    ),
    "gray": ThemeColors(
        name="Gray",
        buttons="#000000",
        main_background="#646464",
        toolbar="#BCBCBC",
        accent="#708090"
    ),
    "charcoal": ThemeColors(
        name="Charcoal",
        buttons="#000000",
        main_background="#464646",
        toolbar="#9C9C9C",
        accent="#696969"
    ),
}

@dataclass 
class ThemeConfig:
    """Theme configuration and user preferences."""
    mode: str = "follow"  # "light", "dark", or "follow"
    light_theme: str = "blue"  # Theme key for light mode
    dark_theme: str = "blue"   # Theme key for dark mode  
    custom_light_themes: Dict[str, ThemeColors] = field(default_factory=dict)
    custom_dark_themes: Dict[str, ThemeColors] = field(default_factory=dict)
    global_accent: str = "#5B9BF8"


def get_theme(config: ThemeConfig, is_dark_mode: bool) -> ThemeColors:
    """Get the appropriate theme based on mode and dark mode state."""
    if config.mode == "follow":
        theme_key = config.dark_theme if is_dark_mode else config.light_theme
        use_dark_themes = is_dark_mode
    elif config.mode == "dark":
        theme_key = config.dark_theme
        use_dark_themes = True
    else:  # light
        theme_key = config.light_theme
        use_dark_themes = False  # Always use light themes in light mode
    
    themes = DARK_THEMES if use_dark_themes else LIGHT_THEMES
    
    # Check mode-specific custom themes first, then fallback to predefined
    custom_themes = config.custom_dark_themes if use_dark_themes else config.custom_light_themes
    if theme_key in custom_themes:
        custom_theme_data = custom_themes[theme_key]
        custom_theme = ThemeColors(
            name=custom_theme_data["name"],
            buttons=custom_theme_data["buttons"],
            main_background=custom_theme_data["main_background"],
            toolbar=custom_theme_data["toolbar"],
            accent=custom_theme_data.get("accent", ""),
            text=custom_theme_data.get("text", "")
        )
        return custom_theme
    elif theme_key in themes:
        theme = themes[theme_key]
        return theme
    else:
        if themes:
            blue_theme = themes.get("blue", list(themes.values())[0])
            return blue_theme
        else:
            return ThemeColors(
                name="Default",
                buttons="#424242",
                main_background="#FFFFFF" if not use_dark_themes else "#1E1E1E",
                toolbar="#F8F8F8" if not use_dark_themes else "#3A3A3A",
                accent="#5B9BF8"
            )


def get_available_themes(is_dark_mode: bool) -> Dict[str, ThemeColors]:
    """Get all available themes for the specified mode."""
    return DARK_THEMES if is_dark_mode else LIGHT_THEMES


def get_theme_display_name(theme_key: str, is_dark_mode: bool) -> str:
    """Get display name for a theme key."""
    themes = get_available_themes(is_dark_mode)
    if theme_key in themes:
        return themes[theme_key].name
    return theme_key.title()
