"""The starting world shared by the live game and the headless run."""

from typing import TYPE_CHECKING

from laife.entities.building import Building
from laife.entities.building_types import FACTORY
from laife.entities.building_types import FARM
from laife.entities.building_types import HOUSE
from laife.entities.player import Player
from laife.entities.terrain_types import TERRAINS
from laife.ui.alog import alg

if TYPE_CHECKING:
    from collections.abc import Mapping
    import random

    from llm_core.chat.config.base import ChatConfig

    from laife.entities.sim_control import SimControl
    from laife.entities.world_runner import WorldRunner


PLAYER_NAMES = ("p0", "p1")


class MissingPlayerChatConfigError(Exception):
    """A chat config map was given that has no entry for one of the players."""

    def __init__(self, player: str) -> None:
        """Name the player, so a headless run never falls back to a paid provider."""
        super().__init__(f"No chat config for player {player!r}")


def setup_world(
    runner: WorldRunner,
    sim_control: SimControl | None,
    rng: random.Random,
    chat_configs: Mapping[str, ChatConfig] | None = None,
) -> None:
    """Populate the world with terrain, players, and buildings.

    Player positions are drawn from *rng*: a seeded ``random.Random`` gives the
    same world on every run.

    *chat_configs* maps each name in :data:`PLAYER_NAMES` to that player's chat
    config. ``None`` gives every player ``chat.default``; a map missing a
    player raises rather than fall back to it.
    """

    def _chat_config(name: str) -> ChatConfig | None:
        if chat_configs is None:
            return None
        if name not in chat_configs:
            raise MissingPlayerChatConfigError(name)
        return chat_configs[name]

    # seed terrain regions
    for terrain in TERRAINS:
        runner.add_terrain(terrain)

    for name in PLAYER_NAMES:
        player = Player(
            name,
            position=(rng.randint(0, 800), rng.randint(0, 600)),
            player_type="inu",
            world_input_queue=runner.input_queue,
            sim_control=sim_control,
            chat_config=_chat_config(name),
        )
        runner.add_player(player)

    player_pov = (500, 500)
    # a house
    b = Building(
        name="Alex's House",
        building_type=HOUSE,
        description="This house belongs to Alex.",
        position=(300, 100),
    )
    alg.log(f"W: Adding building >>>\n{b.to_prompt(player_pov)}\n<<<")
    runner.add_building(b)
    # a farm
    b = Building(
        name="Big ol Farm",
        building_type=FARM,
        position=(200, 400),
    )
    alg.log(f"W: Adding building >>>\n{b.to_prompt(player_pov)}\n<<<")
    runner.add_building(b)
    # a factory
    b = Building(
        name="Utensil shop",
        building_type=FACTORY,
        position=(500, 800),
    )
    alg.log(f"W: Adding building >>>\n{b.to_prompt(player_pov)}\n<<<")
    runner.add_building(b)

    # add a building that collides with the house (should be rejected)
    b = Building(
        name="Colliding House",
        building_type=HOUSE,
        position=(300, 100),
    )
    resp = runner.add_building(b)
    alg.log(f"W: Add colliding building response: {resp}")
