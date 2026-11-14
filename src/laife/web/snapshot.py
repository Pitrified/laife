"""The world as JSON: what ``GET /state`` returns."""

from typing import TYPE_CHECKING
from typing import Any

from pydantic import BaseModel

from laife.entities.building import Building
from laife.entities.player import PlayerState
from laife.entities.terrain import Terrain
from laife.llm.mission import Mission

if TYPE_CHECKING:
    from laife.entities.player import Player
    from laife.entities.sim_control import SimControl
    from laife.entities.world_runner import WorldRunner

HISTORY_SHOWN = 8
"""How many of a player's latest history entries a snapshot carries."""


class UtensilView(BaseModel):
    """One utensil in a player's inventory."""

    name: str
    description: str


class HistoryView(BaseModel):
    """One action a player took on its mission, and what came of it.

    ``action`` is the action's own fields; ``action_type`` is its class name,
    as the ``action`` log event writes it.
    """

    action_type: str
    action: dict[str, Any]
    result: str


class PlayerView(BaseModel):
    """What a client sees of a player."""

    name: str
    player_type: str
    position: tuple[int, int]
    size: tuple[int, int]
    state: PlayerState
    turn: int
    mission: Mission
    inventory: list[UtensilView]
    history: list[HistoryView]

    @classmethod
    def from_player(cls, player: Player) -> PlayerView:
        """Build the view of *player*, with its latest ``HISTORY_SHOWN`` history entries."""
        return cls(
            name=player.name,
            player_type=player.player_type,
            position=player.position,
            size=player.size,
            state=player.state,
            turn=player.turn,
            mission=player.mission,
            inventory=[
                UtensilView(name=u.name, description=u.description) for u in player.inventory
            ],
            history=[
                HistoryView(
                    action_type=type(entry.action).__name__,
                    action=entry.action.model_dump(mode="json"),
                    result=entry.result,
                )
                for entry in player.history.history[-HISTORY_SHOWN:]
            ],
        )


class WorldSnapshot(BaseModel):
    """The whole world at one moment.

    ``seq`` is the number of the last event published before the snapshot was
    taken; a client drops streamed events at or below it. ``paused`` is
    ``None`` when the run has no pause control.
    """

    seq: int
    paused: bool | None
    terrains: list[Terrain]
    buildings: list[Building]
    players: list[PlayerView]


def take_snapshot(runner: WorldRunner, sim_control: SimControl | None, seq: int) -> WorldSnapshot:
    """Return the world held by *runner*, stamped with event number *seq*."""
    return WorldSnapshot(
        seq=seq,
        paused=None if sim_control is None else sim_control.paused,
        terrains=list(runner.terrains),
        buildings=list(runner.buildings),
        players=[PlayerView.from_player(p) for p in runner.players],
    )
