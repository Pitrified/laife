"""Which sprite file shows a player of each type in each state.

Files are under ``static/sprites/<player type>/``. The pygame loader and the
web server's ``/sprites`` route both read this table, so it imports nothing
from pygame.
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
