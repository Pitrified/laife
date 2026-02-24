"""Building entity - pure data, no pygame dependency."""

from dataclasses import dataclass
from dataclasses import field

from laife.config.types import Position
from laife.config.types import Size
from laife.entities.utils.directions import pospos2cardinal_direction

BUILDING_TYPES = ["house", "farm", "factory"]
BUILDING_DESCRIPTIONS = {
    "house": "A place to rest safely.",
    "farm": "A place to grow food.",
    "factory": "A place to make things.",
}


@dataclass
class Building:
    """Pure data representation of a building (no pygame)."""

    name: str
    building_type: str
    position: Position
    size: Size
    description: str | None = field(default=None)

    def __str__(self) -> str:
        """Return the string representation of the building."""
        return f"Building {self.name} at {self.position}"

    def to_prompt(self, pov_pos: Position | None = None) -> str:
        """Return a prompt representation of the building."""
        gen_desc = BUILDING_DESCRIPTIONS[self.building_type]
        p = f"{self.name}: {gen_desc}"
        if self.description is not None:
            p += f"\nNote about this specific {self.building_type}: {self.description}"
        if pov_pos is not None:
            self_cardinal = pospos2cardinal_direction(pov_pos, self.position)
            p += f"\nIt is located to the {self_cardinal.value}."
        else:
            p += f"\nIt is located at {self.position}."
        return p
