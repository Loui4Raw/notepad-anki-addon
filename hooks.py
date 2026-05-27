"""hooks.py — Centralised hook registration for the Notepad addon."""
from aqt.gui_hooks import (
    main_window_did_init,
    reviewer_did_show_question,
    reviewer_did_show_answer,
    reviewer_will_end,
    webview_did_receive_js_message,
)
from anki.hooks import addHook

from . import main


# ── Hook registrations ────────────────────────────────────────────────────────

webview_did_receive_js_message.append(main.on_js_message)

main_window_did_init.append(main.on_main_window_init)

reviewer_did_show_question.append(main.on_question_shown)
reviewer_did_show_answer.append(main.on_answer_shown)
reviewer_will_end.append(main.on_reviewer_end)

addHook("deckBrowserDidShow", main.on_deck_browser_shown)
addHook("overviewDidShow",    main.on_overview_shown)
