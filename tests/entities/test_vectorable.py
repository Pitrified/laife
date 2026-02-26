"""Unit tests for Vectorable entities - no live vector DB required."""

import inspect

import pytest

from laife.entities.building import BuildingType
from laife.entities.utensil import Utensil

# ---------------------------------------------------------------------------
# Utensil
# ---------------------------------------------------------------------------


@pytest.fixture
def utensil() -> Utensil:
    """Sample plain Utensil, constructed without any vector DB."""
    return Utensil(name="sword", description="A sharp blade.")


def test_utensil_no_vector_db(utensil: Utensil) -> None:
    """Utensil must be constructable without a vector DB."""
    assert utensil.name == "sword"
    assert utensil.description == "A sharp blade."


def test_utensil_to_document_metadata(utensil: Utensil) -> None:
    """to_document must populate all required metadata fields."""
    doc = utensil.to_document()
    assert doc.metadata["entity_type"] == "utensil"
    assert doc.metadata["name"] == "sword"
    assert doc.metadata["description"] == "A sharp blade."


def test_utensil_to_document_page_content(utensil: Utensil) -> None:
    """page_content must equal to_prompt()."""
    doc = utensil.to_document()
    assert doc.page_content == utensil.to_prompt()


def test_utensil_round_trip(utensil: Utensil) -> None:
    """from_document(to_document()) must reconstruct an equivalent object."""
    doc = utensil.to_document()
    restored = Utensil.from_document(doc)
    assert restored.name == utensil.name
    assert restored.description == utensil.description


def test_utensil_from_document_no_vector_db(utensil: Utensil) -> None:
    """from_document must require only a Document (no vector DB arg)."""
    params = inspect.signature(Utensil.from_document).parameters
    assert "vector_db" not in params, "from_document must not accept vector_db"


# ---------------------------------------------------------------------------
# BuildingType
# ---------------------------------------------------------------------------


@pytest.fixture
def building_type() -> BuildingType:
    """Sample plain BuildingType, constructed without any vector DB."""
    return BuildingType(
        building_type="workshop",
        description="A place to craft items.",
        size=(80, 80),
    )


def test_building_type_to_document_metadata(building_type: BuildingType) -> None:
    """to_document must populate all required metadata fields."""
    doc = building_type.to_document()
    assert doc.metadata["entity_type"] == "building_type"
    assert doc.metadata["building_type"] == "workshop"
    assert doc.metadata["description"] == "A place to craft items."
    assert doc.metadata["size_w"] == 80
    assert doc.metadata["size_h"] == 80


def test_building_type_to_document_page_content(building_type: BuildingType) -> None:
    """page_content must equal to_prompt()."""
    doc = building_type.to_document()
    assert doc.page_content == building_type.to_prompt()


def test_building_type_round_trip(building_type: BuildingType) -> None:
    """from_document(to_document()) must reconstruct an equivalent object."""
    doc = building_type.to_document()
    restored = BuildingType.from_document(doc)
    assert restored.building_type == building_type.building_type
    assert restored.description == building_type.description
    assert restored.size == building_type.size


def test_building_type_from_document_no_extra_args(building_type: BuildingType) -> None:
    """from_document must require only a Document."""
    params = inspect.signature(BuildingType.from_document).parameters
    # Only 'cls' and 'doc' are allowed
    non_cls = [p for p in params if p != "cls"]
    assert non_cls == ["doc"], f"Unexpected parameters: {non_cls}"
