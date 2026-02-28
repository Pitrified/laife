"""Tests for Player inventory management."""

import asyncio
from unittest.mock import MagicMock
from unittest.mock import patch

from laife.entities.action import ActionCraft
from laife.entities.player import Player
from laife.entities.utensil import Utensil
from laife.entities.world_channel import WResCraft
from laife.entities.world_channel import WResStatus
from laife.entities.world_runner import WorldRunner

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_player(runner: WorldRunner) -> Player:
    """Create a Player with all LLM components mocked out."""
    with patch.multiple(
        "laife.entities.player",
        get_laife_params=MagicMock(return_value=MagicMock()),
        PlayerBrainConfig=MagicMock(),
        PlayerPlannerConfig=MagicMock(),
        PromptLoaderConfig=MagicMock(),
        PlayerBrain=MagicMock(return_value=MagicMock()),
        PlayerPlanner=MagicMock(return_value=MagicMock()),
    ):
        player = Player(
            name="tester",
            position=(0, 0),
            player_type="hero",
            world_input_queue=runner.input_queue,
        )
    runner.add_player(player)
    return player


async def _run_craft(runner: WorldRunner, player: Player, action: ActionCraft) -> WResCraft:
    """Drive world simulation + player.craft concurrently; return the craft result."""
    sim = asyncio.create_task(runner.simulate())
    result = await player.craft(action)
    sim.cancel()
    return result


# ---------------------------------------------------------------------------
# inventory_to_prompt
# ---------------------------------------------------------------------------


def test_inventory_empty_on_init() -> None:
    """A freshly created player starts with an empty inventory list."""
    runner = WorldRunner()
    player = _make_player(runner)
    assert player.inventory == []


def test_inventory_to_prompt_empty() -> None:
    """inventory_to_prompt returns the 'empty' string when inventory is empty."""
    runner = WorldRunner()
    player = _make_player(runner)
    assert player.inventory_to_prompt() == "Empty - no utensils carried."


def test_inventory_to_prompt_with_items() -> None:
    """inventory_to_prompt lists each utensil on its own bulleted line."""
    runner = WorldRunner()
    player = _make_player(runner)
    player.inventory.append(Utensil(name="axe", description="Chops wood"))
    player.inventory.append(Utensil(name="bucket", description="Carries water"))

    result = player.inventory_to_prompt()

    assert "- axe: Chops wood" in result
    assert "- bucket: Carries water" in result
    assert result.count("\n") == 1  # exactly one newline between two items


# ---------------------------------------------------------------------------
# craft() - inventory side-effects
# ---------------------------------------------------------------------------


def test_craft_success_adds_utensil_to_inventory() -> None:
    """A successful craft response places the utensil in the player's inventory."""
    runner = WorldRunner()
    player = _make_player(runner)

    action = ActionCraft(
        reason="need it",
        utensil_name="hammer",
        description="Drives nails",
    )

    # Patch the world judge to always approve
    ok_res = WResCraft(status=WResStatus.SUCCESS, feedback="ok")
    with patch.object(runner, "judge_craft", return_value=ok_res):
        result = asyncio.run(_run_craft(runner, player, action))

    assert result.status == WResStatus.SUCCESS
    assert len(player.inventory) == 1
    assert player.inventory[0].name == "hammer"
    assert player.inventory[0].description == "Drives nails"


def test_craft_failure_does_not_add_utensil_to_inventory() -> None:
    """A failed craft response leaves the inventory unchanged."""
    runner = WorldRunner()
    player = _make_player(runner)

    action = ActionCraft(
        reason="try it",
        utensil_name="magic_wand",
        description="Does magic",
    )

    err_res = WResCraft(status=WResStatus.ERROR, feedback="not possible")
    with patch.object(runner, "judge_craft", return_value=err_res):
        result = asyncio.run(_run_craft(runner, player, action))

    assert result.status == WResStatus.ERROR
    assert player.inventory == []


def test_craft_multiple_successes_accumulate_in_inventory() -> None:
    """Each successful craft appends a new utensil; inventory grows with each call."""
    runner = WorldRunner()
    player = _make_player(runner)

    async def _run_all() -> None:
        for name in ("axe", "bucket", "hoe"):
            action = ActionCraft(reason="need it", utensil_name=name, description=f"A {name}")
            ok_res = WResCraft(status=WResStatus.SUCCESS, feedback="ok")
            with patch.object(runner, "judge_craft", return_value=ok_res):
                await _run_craft(runner, player, action)

    asyncio.run(_run_all())

    assert [u.name for u in player.inventory] == ["axe", "bucket", "hoe"]
