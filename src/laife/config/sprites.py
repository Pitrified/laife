"""Which sprite file shows a player of each type in each state.

Files are under ``static/sprites/<player type>/``; the web server's
``/sprites`` route reads this table and hands it to the page.
"""

INU_STATE_FNS = {
    "idle": "inu_idle_00.png",
    "thinking": "inu_basic_02.png",
    "moving": "inu_idle_back_00.png",
}

STATE_FNS = {
    "inu": INU_STATE_FNS,
}
"""Player type to {state: file name}; a state is a ``PlayerState`` value."""
