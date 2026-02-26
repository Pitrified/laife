"""Building entity - pure data, no pygame dependency."""

from typing import Self

from langchain_core.documents import Document
from pydantic import BaseModel

from laife.config.types import Position
from laife.config.types import Size
from laife.entities.utils.directions import pospos2cardinal_direction


class BuildingType(BaseModel):
    """Master data for a category of building (never changes per instance)."""

    building_type: str
    description: str
    size: Size

    def to_prompt(self) -> str:
        """Return a short prompt describing the building type."""
        return f"{self.building_type}: {self.description}"

    def to_document(self) -> Document:
        """Serialize the building type to a LangChain Document."""
        meta = {
            "building_type": self.building_type,
            "description": self.description,
            "size_w": self.size[0],
            "size_h": self.size[1],
            "entity_type": "building_type",
        }
        return Document(
            page_content=self.to_prompt(),
            metadata=meta,
        )

    @classmethod
    def from_document(cls, doc: Document) -> Self:
        """Reconstruct a BuildingType from a LangChain Document."""
        meta = doc.metadata
        return cls(
            building_type=meta["building_type"],
            description=meta["description"],
            size=(meta["size_w"], meta["size_h"]),
        )


class Building(BaseModel):
    """Pure data representation of a specific building placed in the world."""

    name: str
    building_type: BuildingType
    position: Position
    description: str | None = None

    @property
    def size(self) -> Size:
        """Convenience accessor - delegates to the building type."""
        return self.building_type.size

    def __str__(self) -> str:
        """Return the string representation of the building."""
        return f"Building {self.name} ({self.building_type.building_type}) at {self.position}"

    def to_prompt(self, pov_pos: Position | None = None) -> str:
        """Return a prompt representation of the building."""
        p = f"{self.name}: {self.building_type.description}"
        if self.description is not None:
            p += (
                f"\nNote about this specific {self.building_type.building_type}: {self.description}"
            )
        if pov_pos is not None:
            self_cardinal = pospos2cardinal_direction(pov_pos, self.position)
            p += f"\nIt is located to the {self_cardinal.value}."
        else:
            p += f"\nIt is located at {self.position}."
        return p
