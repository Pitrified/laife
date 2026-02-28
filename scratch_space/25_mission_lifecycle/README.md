# Mission lifecycle (completion and failure)

Wire up mission status transitions: after the world judge confirms a build/craft succeeded, mark the active mission `COMPLETED`. After N consecutive failures or an explicit LLM signal, mark it `FAILED` and trigger re-planning or a new mission. Without this, the player loops forever on a single mission.

explain this: why is FAILED state needed? wouldn't the player just re-plan after a failure and try again until it succeeds?
