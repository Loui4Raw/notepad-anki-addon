// Notepad addon – reviewer keyboard shortcut
// Injected once via webview_will_set_content; no per-card re-injection needed.
document.addEventListener("keydown", function (e) {
    if (e.ctrlKey && e.shiftKey && (e.key === "N" || e.key === "n")) {
        e.preventDefault();
        e.stopPropagation();
        pycmd("notepad_toggle");
    }
}, true);
