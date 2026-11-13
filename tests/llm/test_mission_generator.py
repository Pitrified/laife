"""Tests for the mission generator chain models."""

from laife.llm.mission_generator import MissionGeneratorInput


def test_generator_input_fields() -> None:
    """MissionGeneratorInput should expose the three required template fields."""
    inp = MissionGeneratorInput(
        observation="A forest to the north.",
        player_state="idle at (0, 0)",
        inventory="Empty - no utensils carried.",
    )
    assert inp.observation == "A forest to the north."
    assert inp.player_state == "idle at (0, 0)"
    assert inp.inventory == "Empty - no utensils carried."
