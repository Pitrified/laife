import asyncio
from enum import Enum

from loguru import logger as lg
from pygame.sprite import Sprite

from laife.llm.brain import Brain
from laife.ui.sprites import SpriteSheet


class PlayerState(Enum):
    IDLE = "idle"
    THINKING = "thinking"


class Player(Sprite):
    def __init__(
        self,
        name: str,
        position: tuple[int, int],
        player_type: str,
        state: PlayerState = PlayerState.IDLE,
    ) -> None:
        super().__init__()

        self.name: str = name

        self.player_type = player_type
        self.sprite_sheet = SpriteSheet(player_type)

        self.set_state(state)
        self.set_position(position)

        self.score: int = 0

        self.brain = Brain()

        self.dying = False
        self.input_data: str | None = None

    def move(self, dx: int, dy: int) -> None:
        new_position = (self.position[0] + dx, self.position[1] + dy)
        self.set_position(new_position)

    def increase_score(self, points: int) -> None:
        self.score += points

    async def think(self) -> None:
        self.state = PlayerState.THINKING
        lg.info(f"{self.name} is thinking")
        res = await self.brain.achat("english", "german", self.input_data)
        lg.info(f"{self.name} thought: {res}")
        self.increase_score(10)
        self.state = PlayerState.IDLE

    def set_position(self, position: tuple[int, int]) -> None:
        self.position = position
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position

    def set_state(self, state: PlayerState) -> None:
        self.state = state
        self.image = self.sprite_sheet.get_sprite_state(self.state.value)

    def __str__(self) -> str:
        return f"Player {self.name} at {self.position} with score {self.score} and state {self.state.value}"
