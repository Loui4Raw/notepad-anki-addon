"""state.py — Central mutable state for the Notepad addon."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ui.dock   import NotepadDock
    from .ui.window import NotepadWindow
    from .ui.editor import EditorPane, NotepadEditor
    from aqt.qt     import QAction

# Core widgets — reparented between dock and window when switching modes
dock:   "NotepadDock | None"   = None
win:    "NotepadWindow | None" = None
pane:   "EditorPane | None"    = None   # shared EditorPane
editor: "NotepadEditor | None" = None   # shared NotepadEditor (child of pane)

# Menu action displayed in the Notepad top-level menu
toggle_action: "QAction | None" = None

# Reviewer state
in_review:        bool      = False
in_windowed_mode: bool      = False  # True = windowed, False = docked
card_font:        "str | None" = None  # last font family received from card JS

# Per-session geometry (only used when remember_position = False)
session_windowed_geom: "tuple[int, int, int, int] | None" = None
session_docked_width:  "int | None"                       = None
