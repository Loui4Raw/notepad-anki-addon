"""main.py — Core Notepad logic."""
from aqt import mw
from aqt.qt import QAction, QMenu, QShortcut, QKeySequence, QFont, QTimer, Qt

from .config import get_config, save_config, is_dark_mode, SHADOW_M
from . import state
from .ui.dock    import NotepadDock, _set_action_checked
from .ui.window  import NotepadWindow
from .ui.editor  import EditorPane
from .ui.theme   import apply_current_theme
from .ui.settings import open_settings
from .utils.formatting import (
    toggle_bold, toggle_italic, toggle_underline,
    restore_formatting_state, sync_format_buttons,
)


# JS injected into reviewer

_SHORTCUT_JS = """
(function() {
    if (window.__notepadBound) return;
    window.__notepadBound = true;
    window.addEventListener('keyup', function(e) {
        if (e.ctrlKey && !e.shiftKey && !e.altKey && (e.key === 'N' || e.key === 'n')) {
            e.preventDefault(); e.stopPropagation();
            pycmd('notepad_toggle');
        }
    }, true);
})();
"""

_CARD_FONT_JS = """
setTimeout(function() {
    var card = document.querySelector('.card');
    if (!card) return;
    var font = getComputedStyle(card).fontFamily;
    if (font) pycmd('notepad_font:' + font);
}, 200);
"""


def _inject_shortcut() -> None:
    try:
        mw.reviewer.web.eval(_SHORTCUT_JS)
    except Exception:
        pass


def _inject_card_font() -> None:
    try:
        mw.reviewer.web.eval(_CARD_FONT_JS)
    except Exception:
        pass


# JS message bridge

def on_js_message(handled, message: str, context):
    """Handler for webview_did_receive_js_message — registered in hooks.py."""
    if message == "notepad_toggle":
        toggle_notepad()
        return (True, None)

    if message.startswith("notepad_font:"):
        raw    = message[len("notepad_font:"):]
        family = raw.split(",")[0].strip().strip("'\"")
        state.card_font = family
        cfg = get_config()
        if state.editor and cfg.get("font_source") == "card":
            state.editor.setFont(QFont(family, cfg.get("font_size", 13)))
        return (True, None)

    return handled


# Initialisation

def _init_notepad() -> None:
    """
    Create the shared widget tree (EditorPane + NotepadDock) on first use.
    Called at most once per Anki session, on the first toggle_notepad() call.
    """
    cfg = get_config()

    state.pane = EditorPane()   # also sets state.editor inside __init__
    state.dock = NotepadDock()

    dock_area = (
        Qt.DockWidgetArea.RightDockWidgetArea
        if cfg.get("sidebar_position", "right") == "right"
        else Qt.DockWidgetArea.LeftDockWidgetArea
    )
    mw.addDockWidget(dock_area, state.dock)

    # Wire toolbar buttons
    tb = state.pane.toolbar()
    tb._btn_bold.clicked.connect(toggle_bold)
    tb._btn_italic.clicked.connect(toggle_italic)
    tb._btn_underline.clicked.connect(toggle_underline)
    tb._btn_view.clicked.connect(_switch_mode)
    tb._btn_close.clicked.connect(_close_current)

    # Format button sync (only when remember_formatting is off)
    if not cfg.get("remember_formatting", True):
        state.editor.cursorPositionChanged.connect(sync_format_buttons)
        state.editor.currentCharFormatChanged.connect(lambda _: sync_format_buttons())

    # In-editor keyboard shortcuts
    QShortcut(QKeySequence("Ctrl+B"), state.editor, activated=toggle_bold)
    QShortcut(QKeySequence("Ctrl+I"), state.editor, activated=toggle_italic)
    QShortcut(QKeySequence("Ctrl+U"), state.editor, activated=toggle_underline)

    if cfg.get("windowed", False):
        # Start in windowed mode — adopt pane into dock first so Qt layout is
        # initialised, then immediately switch to windowed.
        state.dock.adopt_pane()
        state.dock.show()
        QTimer.singleShot(0, lambda: _do_switch_to_windowed(initial=True))
    else:
        state.dock.adopt_pane()
        state.dock.apply_theme()
        QTimer.singleShot(50, state.pane.toolbar().ensure_autohide_state)

    restore_formatting_state()


# Mode switching

def _switch_mode() -> None:
    """Called when the view button (sidebar ↔ window) is clicked."""
    if state.in_windowed_mode:
        _do_switch_to_docked()
    else:
        _do_switch_to_windowed()


def _do_switch_to_windowed(initial: bool = False) -> None:
    """Transition: docked → windowed."""
    if state.win is None:
        state.win = NotepadWindow()

    state.dock.release_pane()
    state.win.adopt_pane()
    state.in_windowed_mode = True

    cfg = get_config()
    cfg["windowed"] = True
    save_config(cfg)

    state.dock.hide()
    state.win.restore_geometry()
    state.win.show()
    state.win.apply_theme()
    _set_action_checked(True)
    QTimer.singleShot(50, state.pane.toolbar().ensure_autohide_state)


def _do_switch_to_docked() -> None:
    """Transition: windowed → docked."""
    if state.win:
        state.win.release_pane()
        state.win.hide()

    state.dock.adopt_pane()
    state.in_windowed_mode = False

    cfg = get_config()
    cfg["windowed"] = False
    save_config(cfg)

    state.dock.show_in_dock()
    state.dock.apply_theme()
    _set_action_checked(True)
    QTimer.singleShot(50, state.pane.toolbar().ensure_autohide_state)


# Toggle (Ctrl+N / menu)

def toggle_notepad() -> None:
    """Show or hide the Notepad.  Only operates when inside a review session."""
    if not state.in_review:
        return

    if state.dock is None:
        _init_notepad()
        _set_action_checked(True)
        return

    if state.in_windowed_mode:
        if state.win and state.win.isVisible():
            state.win.close_window()
        elif state.win:
            state.win.restore_geometry()
            state.win.show()
            state.pane.toolbar().ensure_autohide_state()
            _set_action_checked(True)
    else:
        if state.dock.isVisible():
            state.dock.close_notepad()
        else:
            state.dock.show_in_dock()
            _set_action_checked(True)


def _close_current() -> None:
    """Close whichever view (window or dock) is currently active."""
    if state.in_windowed_mode and state.win:
        state.win.close_window()
    elif state.dock:
        state.dock.close_notepad()


# Session geometry helpers

def _clear_session_geometry() -> None:
    state.session_windowed_geom = None
    state.session_docked_width  = None


def _is_notepad_visible() -> bool:
    if state.in_windowed_mode:
        return state.win is not None and state.win.isVisible()
    return state.dock is not None and state.dock.isVisible()


# Reviewer event handlers

def on_question_shown(card) -> None:
    state.in_review = True
    _inject_shortcut()
    _update_action_state()

    cfg = get_config()
    if not cfg.get("remember_position", True):
        _clear_session_geometry()
    if cfg.get("font_source") == "card":
        _inject_card_font()
    if cfg.get("auto_open_reviewer", False) and not _is_notepad_visible():
        toggle_notepad()
    if cfg.get("clear_on_new_card", True) and state.editor is not None:
        state.editor.clear()


def on_answer_shown(card) -> None:
    _inject_shortcut()


def on_reviewer_end() -> None:
    _ensure_notepad_closed()


def _ensure_notepad_closed() -> None:
    if state.in_review:
        state.in_review = False
        _update_action_state()
        cfg = get_config()
        if not cfg.get("remember_position", True):
            _clear_session_geometry()
        if _is_notepad_visible():
            _close_current()
    elif _is_notepad_visible():
        _close_current()


def on_deck_browser_shown() -> None:
    _ensure_notepad_closed()


def on_overview_shown() -> None:
    _ensure_notepad_closed()


def _update_action_state() -> None:
    if state.toggle_action:
        state.toggle_action.setEnabled(state.in_review)


# Menu setup

def on_main_window_init() -> None:
    notepad_menu = QMenu("Notepad", mw)
    mw.menuBar().addMenu(notepad_menu)

    state.toggle_action = QAction("Show Notepad  (Ctrl+N)", mw)
    state.toggle_action.setCheckable(True)
    state.toggle_action.setChecked(False)
    state.toggle_action.setEnabled(False)
    state.toggle_action.triggered.connect(_on_action_triggered)
    notepad_menu.addAction(state.toggle_action)

    notepad_menu.addSeparator()

    settings_action = QAction("Settings...", mw)
    settings_action.triggered.connect(open_settings)
    notepad_menu.addAction(settings_action)


def _on_action_triggered(checked: bool) -> None:
    if checked:
        if state.in_review and not _is_notepad_visible():
            toggle_notepad()
    else:
        if _is_notepad_visible():
            _close_current()
