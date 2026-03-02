"""Terrain entity - pure data, no pygame dependency."""

from enum import StrEnum
from typing import Self

from langchain_core.documents import Document
from pydantic import BaseModel

from laife.config.types import Position
from laife.config.types import Size
from laife.entities.utils.directions import pospos2cardinal_direction


class TerrainType(StrEnum):
    """Enumeration of terrain types in the world."""

    FOREST = "forest"
    LAKE = "lake"
    FERTILE_LAND = "fertile_land"
    PLAIN = "plain"


class Terrain(BaseModel):
    """Pure data representation of a terrain region in the world."""

    name: str
    terrain_type: TerrainType
    position: Position
    size: Size
    description: str | None = None

    def to_prompt(self, pov_pos: Position | None = None) -> str:
        """Return a prompt representation of the terrain."""
        label = self.terrain_type.value.replace("_", " ")
        p = f"{self.name}: a {label}"
        if self.description is not None:
            p += f" - {self.description}"
        if pov_pos is not None:
            cardinal = pospos2cardinal_direction(pov_pos, self.position)
            p += f"\nIt lies to the {cardinal.value}."
        else:
            p += f"\nIt is located at {self.position}."
        return p

    def to_document(self) -> Document:
        """Serialize the terrain to a LangChain Document."""
        meta = {
            "entity_type": "terrain",
            "name": self.name,
            "terrain_type": self.terrain_type.value,
            "position_x": self.position[0],
            "position_y": self.position[1],
            "size_w": self.size[0],
            "size_h": self.size[1],
            "description": self.description or "",
        }
        return Document(
            page_content=self.to_prompt(),
            metadata=meta,
        )

    @classmethod
    def from_document(cls, doc: Document) -> Self:
        """Reconstruct a Terrain from a LangChain Document."""
        meta = doc.metadata
        return cls(
            name=meta["name"],
            terrain_type=TerrainType(meta["terrain_type"]),
            position=(meta["position_x"], meta["position_y"]),
            size=(meta["size_w"], meta["size_h"]),
            description=meta["description"] or None,
        )
