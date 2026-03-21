"""Unit tests for the Terrain entity - no live vector DB required."""

import inspect

from llm_core.vectorstores.vectorable import Vectorable
import pytest

from laife.entities.terrain import Terrain
from laife.entities.terrain import TerrainType

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def forest() -> Terrain:
    """Sample forest terrain."""
    return Terrain(
        name="Dark Woods",
        terrain_type=TerrainType.FOREST,
        position=(10, 20),
        size=(200, 150),
        description="Tall ancient oaks.",
    )


# ---------------------------------------------------------------------------
# to_document / from_document
# ---------------------------------------------------------------------------


def test_terrain_to_document_metadata(forest: Terrain) -> None:
    """to_document must populate all required metadata fields."""
    doc = forest.to_document()
    assert doc.metadata["entity_type"] == "terrain"
    assert doc.metadata["name"] == "Dark Woods"
    assert doc.metadata["terrain_type"] == "forest"
    assert doc.metadata["position_x"] == 10
    assert doc.metadata["position_y"] == 20
    assert doc.metadata["size_w"] == 200
    assert doc.metadata["size_h"] == 150
    assert doc.metadata["description"] == "Tall ancient oaks."


def test_terrain_to_document_page_content(forest: Terrain) -> None:
    """page_content must equal to_prompt() with no pov_pos."""
    doc = forest.to_document()
    assert doc.page_content == forest.to_prompt()


def test_terrain_round_trip(forest: Terrain) -> None:
    """from_document(to_document()) must reconstruct an equivalent object."""
    doc = forest.to_document()
    restored = Terrain.from_document(doc)
    assert restored.name == forest.name
    assert restored.terrain_type == forest.terrain_type
    assert restored.position == forest.position
    assert restored.size == forest.size
    assert restored.description == forest.description


def test_terrain_round_trip_no_description() -> None:
    """Round-trip must work when description is None."""
    t = Terrain(
        name="Lake",
        terrain_type=TerrainType.LAKE,
        position=(0, 0),
        size=(50, 50),
    )
    restored = Terrain.from_document(t.to_document())
    assert restored.description is None


def test_terrain_from_document_no_vector_db(forest: Terrain) -> None:
    """from_document must require only a Document (no vector_db argument)."""
    params = inspect.signature(Terrain.from_document).parameters
    assert "vector_db" not in params


# ---------------------------------------------------------------------------
# to_prompt
# ---------------------------------------------------------------------------


def test_terrain_to_prompt_no_pov(forest: Terrain) -> None:
    """to_prompt() without pov must include terrain type and position."""
    text = forest.to_prompt()
    assert "forest" in text
    assert "Dark Woods" in text
    assert str(forest.position) in text


def test_terrain_to_prompt_with_pov(forest: Terrain) -> None:
    """to_prompt(pov_pos=...) must include a cardinal direction."""
    directions = {
        "north",
        "south",
        "east",
        "west",
        "northeast",
        "northwest",
        "southeast",
        "southwest",
    }
    text = forest.to_prompt(pov_pos=(500, 500))
    assert any(d in text for d in directions)


def test_terrain_to_prompt_contains_description(forest: Terrain) -> None:
    """to_prompt() must include the description when set."""
    text = forest.to_prompt()
    assert "Tall ancient oaks." in text


# ---------------------------------------------------------------------------
# Vectorable protocol
# ---------------------------------------------------------------------------


def test_terrain_implements_vectorable(forest: Terrain) -> None:
    """Terrain must satisfy the Vectorable structural protocol."""
    assert isinstance(forest, Vectorable)
