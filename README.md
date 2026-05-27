# Notepad — Anki Add-on

A lightweight notepad for Anki review sessions with a clean editor, easy formatting, and flexible docking.

## 🚀 What it does

- Adds a notepad panel or floating editor during review
- Supports bold, italic, and underline formatting
- Applies custom light/dark themes
- Can match the card font automatically
- Saves window position and dock width between sessions

## ✨ Highlights

- **Docked or windowed editor** for your preferred workflow
- **Quick formatting shortcuts**: `Ctrl+B`, `Ctrl+I`, `Ctrl+U`
- **Auto-formatting** for lists and notes
- **Optional transparent window** on Windows
- **Settings panel** for personalization

## 📦 Installation

1. Copy this folder into your Anki add-ons directory:
   - Windows: `%APPDATA%\Anki2\addons21\`
   - Mac: `~/Library/Application Support/Anki2/addons21/`
   - Linux: `~/.local/share/Anki2/addons21/`
2. Restart Anki
3. Open a review session and use the new Notepad menu

## ⚙️ Configuration

The add-on creates `config.json` and `meta.json` on first run.
Use `config.json.example` and `meta.json.example` as templates.

Access settings from: `Notepad > Settings...`

### Main options

- **Clear on new card** — reset notes automatically on each new card
- **Auto-open in reviewer** — show the notepad when review starts
- **Font source** — use a custom font or match card text
- **Theme mode** — system, light, or dark
- **Window transparency** — enable on Windows

## ▶️ Usage

- **Toggle Notepad**: `Ctrl+N`
- **Bold**: `Ctrl+B`
- **Italic**: `Ctrl+I`
- **Underline**: `Ctrl+U`
- **Switch view**: use the view toggle button to change between docked and floating

## 📁 Project structure

```
Notepad/
├── __init__.py          # Add-on entry point
├── main.py              # Core logic and initialization
├── config.py            # Configuration management
├── hooks.py             # Anki hook registration
├── state.py              # Runtime state management
├── themes.py             # Theme definitions
├── ui/                  # UI components
│   ├── dock.py          # Dock widget
│   ├── window.py        # Floating window
│   ├── editor.py        # Text editor
│   ├── toolbar.py       # Toolbar buttons
│   ├── settings.py      # Settings dialog
│   └── theme_editor.py  # Custom theme editor
├── utils/               # Utility helpers
│   ├── formatting.py    # Text formatting helpers
│   └── windows.py       # Windows-specific utilities
└── web/                 # Web assets
    └── notepad.js       # Reviewer JavaScript integration
```

## 🧪 Development

Built for Anki 2.1+ with PyQt5.

### Requirements

- Anki 2.1+
- Python 3.9+
- PyQt5 (included with Anki)

## 📄 License

MIT License — see [LICENSE](LICENSE)
