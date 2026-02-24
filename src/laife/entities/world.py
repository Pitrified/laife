"""World module — re-exports for backward compatibility.

New code should import directly from:
  laife.entities.world_runner   (WorldRunner)
  laife.entities.world_renderer (WorldRenderer)
"""

from laife.entities.world_renderer import WorldRenderer
from laife.entities.world_runner import WorldRunner

# Alias so that ``from laife.entities.world import World`` keeps working.
World = WorldRunner

__all__ = [
    "World",
    "WorldRenderer",
    "WorldRunner",
]

# ---- original implementation has moved to world_runner.py / world_renderer.py ----

_MOVED = True
