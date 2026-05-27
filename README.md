# Notepad - Anki Add-on

A modern notepad add-on for Anki that provides a clean, customizable text editor during card review sessions.

## Features

- **Docked or Windowed Mode**: Use as a sidebar dock or as a floating window
- **Rich Text Editing**: Bold, italic, and underline formatting
- **Custom Themes**: Built-in light and dark themes with custom theme support
- **Auto-formatting**: Optional automatic list creation
- **Card Font Sync**: Option to match the editor font to your card font
- **Keyboard Shortcuts**: Ctrl+N to toggle, Ctrl+B/I/U for formatting
- **Transparent Windows**: Support for transparent/semi-transparent windows on Windows
- **Position Memory**: Remembers window position and dock width

## Installation

1. Copy this add-on folder to your Anki add-ons directory:
   - Windows: `%APPDATA%\Anki2\addons21\`
   - Mac: `~/Library/Application Support/Anki2/addons21/`
   - Linux: `~/.local/share/Anki2/addons21/`
2. Restart Anki
3. The Notepad menu will appear in the menu bar

## Configuration

The add-on creates `config.json` and `meta.json` files on first run. Template files are provided as `config.json.example` and `meta.json.example` for reference.

### Settings

Access settings via: `Notepad > Settings...`

Key options:
- **Clear on new card**: Automatically clear the notepad when showing a new card
- **Auto-open in reviewer**: Automatically show notepad when entering review mode
- **Font source**: Use custom font or match card font
- **Theme mode**: Follow system theme or force light/dark
- **Window transparency**: Enable transparency effects (Windows only)

## Usage

- **Toggle Notepad**: Press `Ctrl+N` during card review
- **Format text**: Use toolbar buttons or `Ctrl+B` (bold), `Ctrl+I` (italic), `Ctrl+U` (underline)
- **Switch views**: Click the view button to toggle between docked and windowed mode

## File Structure

```
Notepad/
├── __init__.py          # Add-on entry point
├── main.py              # Core logic and initialization
├── config.py            # Configuration management
├── hooks.py             # Anki hook registration
├── state.py             # Runtime state management
├── themes.py            # Theme definitions
├── ui/                  # UI components
│   ├── dock.py          # Dock widget
│   ├── window.py        # Floating window
│   ├── editor.py        # Text editor
│   ├── toolbar.py       # Toolbar with formatting buttons
│   ├── settings.py      # Settings dialog
│   └── theme_editor.py  # Custom theme editor
├── utils/               # Utility modules
│   ├── formatting.py    # Text formatting helpers
│   └── windows.py       # Windows-specific utilities
└── web/                 # Web assets
    └── notepad.js       # JavaScript for reviewer integration
```

## Development

This add-on is built for Anki 2.1+ using PyQt5.

### Requirements

- Anki 2.1+
- Python 3.9+
- PyQt5 (included with Anki)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

This is a personal project for Anki customization. Feel free to fork and modify for your own needs.
