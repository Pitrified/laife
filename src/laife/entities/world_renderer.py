"""WorldRenderer — pygame display layer that observes a WorldRunner."""

import asyncio
import sys
import time

import pygame

from laife.entities.building_sprite import BuildingSprite
from laife.entities.player_sprite import PlayerSprite
from laife.entities.world_runner import WorldRunner
from laife.ui.alog import alg


class WorldRenderer:
    """Drives the pygame display for a WorldRunner.

    The renderer is intentionally decoupled from the runner: it holds a
    read-only reference to the runner's entity lists and creates its own
    sprite objects.  The runner never imports pygame.

    Usage::

        runner = WorldRunner()
        renderer = WorldRenderer(runner)
        await asyncio.gather(runner.simulate(), renderer.render(), ...)
    """

    WIDTH = 1200
    HEIGHT = 900

    def __init__(self, runner: WorldRunner) -> None:
        """Initialise pygame and build initial sprite collections."""
        self.runner = runner

        pygame.init()
        pygame.display.set_caption("lAIfe simulation")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))

        self.redraw_period_sec = 1
        self.redraw_deadline = time.time()  # draw immediately on first tick

        # sprite groups owned entirely by the renderer
        self.player_sprites: pygame.sprite.Group = pygame.sprite.Group()
        self.building_sprites: pygame.sprite.Group = pygame.sprite.Group()

        # maps used to avoid recreating sprites for the same entity
        self._agent_sprite_map: dict[int, PlayerSprite] = {}
        self._building_sprite_map: dict[int, BuildingSprite] = {}

    # ------------------------------------------------------------------
    # Render loop
    # ------------------------------------------------------------------

    async def render(self) -> None:
        """Async render loop — call from asyncio.gather alongside the runner."""
        alg.log("W: Starting rendering loop")
        while True:
            self._sync_sprites()
            self.check_events()
            self.redraw()
            await asyncio.sleep(0.1)

    # ------------------------------------------------------------------
    # Sprite synchronisation
    # ------------------------------------------------------------------

    def _sync_sprites(self) -> None:
        """Reconcile renderer sprite collections with runner entity lists."""
        # add sprites for new agents
        for agent in self.runner.agents:
            if id(agent) not in self._agent_sprite_map:
                sprite = PlayerSprite(agent, self.player_sprites)
                self._agent_sprite_map[id(agent)] = sprite

        # add sprites for new buildings
        for building in self.runner.buildings:
            if id(building) not in self._building_sprite_map:
                sprite = BuildingSprite(building, self.building_sprites)
                self._building_sprite_map[id(building)] = sprite

        # pull latest state from all agent sprites
        self.player_sprites.update()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def check_events(self) -> None:
        """Poll pygame events and react to quit gestures."""
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    self.quit()
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_q:
                            self.quit()

    def quit(self) -> None:
        """Tear down pygame and exit the process."""
        alg.log_nowait("W: Quitting the game\n")
        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def should_redraw(self) -> bool:
        """Return True when the throttle period has elapsed."""
        return time.time() > self.redraw_deadline

    def reset_deadline(self) -> None:
        """Advance the redraw deadline by one period."""
        self.redraw_deadline = time.time() + self.redraw_period_sec

    def redraw(self) -> None:
        """Clear the screen, draw all sprites, and flip the display."""
        if not self.should_redraw():
            return
        self.screen.fill((0, 0, 0))
        self.player_sprites.draw(self.screen)
        self.building_sprites.draw(self.screen)
        pygame.display.flip()
        self.reset_deadline()
