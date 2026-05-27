"""
Notepad — Anki add-on entry point.

Importing hooks.py is sufficient: it registers all gui_hooks and anki.hooks
at module load time and imports main.py which pulls in the full widget tree.
"""
from . import hooks  # noqa: F401