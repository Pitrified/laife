"""Building entity - pure data, no pygame dependency."""

from pydantic import BaseModel

from laife.config.types import Position
from laife.config.types import Size
from laife.entities.utils.directions import pospos2cardinal_direction


class BuildingType(BaseModel):
    """Master data for a category of building (never changes per instance)."""

    building_type: str
    description: str
    size: Size


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
