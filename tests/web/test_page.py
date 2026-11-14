"""The page, the sprite table and the sprite files, served in process."""

import asyncio

import httpx

from laife.entities.player import PlayerState
from laife.headless import build_world
from laife.params.laife_params import get_laife_params
from laife.web.events import EventHub
from laife.web.server import create_app


def get(path: str) -> httpx.Response:
    """GET *path* from an app over a scripted world."""

    async def scenario() -> httpx.Response:
        app = create_app(build_world(0, None), None, EventHub())
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(path)

    return asyncio.run(scenario())


def test_page_is_served_without_caching() -> None:
    """/ is the page, and a browser is told to ask again on every load."""
    response = get("/")
    assert response.status_code == httpx.codes.OK
    assert "<canvas" in response.text
    assert response.headers["cache-control"] == "no-cache"


def test_page_scripts_are_served() -> None:
    """The page's module is served as JavaScript."""
    response = get("/js/app.js")
    assert response.status_code == httpx.codes.OK
    assert "javascript" in response.headers["content-type"]


def test_sprites_cover_every_state_of_every_player_type() -> None:
    """Each player type in the world has a served sprite for each state."""
    table = get("/sprites").json()
    sprites_fol = get_laife_params().paths.sprites_fol
    player_types = {p.player_type for p in build_world(0, None).players}
    for player_type in player_types:
        assert set(table[player_type]) == {s.value for s in PlayerState}
        for url in table[player_type].values():
            assert (sprites_fol / url.removeprefix("/sprites/")).is_file()
            response = get(url)
            assert response.status_code == httpx.codes.OK
            assert response.headers["content-type"] == "image/png"


def test_api_routes_win_over_the_page_mount() -> None:
    """The mount at / does not swallow /state."""
    assert "players" in get("/state").json()
