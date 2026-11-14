"""The world page against a real serving run: draws, zooms, steps, pauses, shows a player, quits.

One test walks the whole sequence, since each step needs the state the one
before left, and starting a run costs a few seconds. It saves a screenshot
in ``cache/e2e/`` with a player's detail open, for a person or an agent to
look at.
"""

import io
import re
from typing import TYPE_CHECKING

from PIL import Image
from playwright.sync_api import expect

from laife.params.laife_params import get_laife_params

if TYPE_CHECKING:
    from playwright.sync_api import Browser
    from playwright.sync_api import Page
    from playwright.sync_api import ViewportSize

    from tests.e2e.conftest import ServedRun

STOP_SECONDS = 10
VIEWPORT: ViewportSize = {"width": 1400, "height": 850}
MIN_COLOURS = 20
RECONNECT_WAIT_MS = 4000


def turns(page: Page) -> list[int]:
    """Each card's turn, in card order."""
    found = []
    for meta in page.locator(".player .meta").all_text_contents():
        match = re.search(r"turn (\d+)", meta)
        assert match is not None, meta
        found.append(int(match.group(1)))
    return found


def canvas_colours(page: Page) -> int:
    """Count the colours in a screenshot of the world canvas.

    A WebGL canvas cannot be read back with ``getImageData``, so this looks at
    what reached the screen.
    """
    shot = Image.open(io.BytesIO(page.locator("#world").screenshot()))
    colours = shot.convert("RGB").getcolors(maxcolors=1 << 20)
    assert colours is not None
    return len(colours)


def zoom(page: Page) -> float:
    """Return the world view's zoom, which the page keeps on the canvas."""
    value = page.locator("#world").get_attribute("data-zoom")
    assert value is not None
    return float(value)


def check_zoom(page: Page) -> None:
    """Wheel over the world zooms in; fit restores the first view."""
    fitted = zoom(page)
    box = page.locator("#world").bounding_box()
    assert box is not None
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.wheel(0, -600)
    page.wait_for_function(
        f"() => Number(document.getElementById('world').dataset.zoom) > {fitted}"
    )
    page.click("#fit")
    assert zoom(page) == fitted


def check_step_run_and_hold(page: Page) -> None:
    """Step plays one turn; resume runs; pause holds the turns."""
    page.click("#step")
    expect(page.locator(".player .meta").filter(has_text="turn 1")).to_have_count(1)
    expect(page.locator(".player .actions li").first).to_be_visible()
    page.click("#pause")
    expect(page.locator("#pause")).to_have_text("pause")
    page.wait_for_function(
        """() => [...document.querySelectorAll(".player .meta")]
            .every((m) => Number(m.textContent.match(/turn (\\d+)/)[1]) >= 3)"""
    )
    page.click("#pause")
    expect(page.locator("#pause")).to_have_text("resume")
    page.wait_for_timeout(1000)
    held = turns(page)
    page.wait_for_timeout(1000)
    assert turns(page) == held


def check_detail(page: Page) -> None:
    """Open a player from its card, alone; return to the list by Escape and by the back button.

    The screenshot is taken with the detail open.
    """
    name = page.locator(".player").first.get_attribute("data-player")
    page.locator(".player").first.click()
    expect(page.locator(".detail")).to_have_count(1)
    expect(page.locator(".player")).to_have_count(0)
    expect(page.locator(".detail .head .name")).to_have_text(name or "")
    expect(page.locator(".detail .tree .node").first).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator(".player")).to_have_count(2)
    page.locator(".player").first.click()
    shots = get_laife_params().paths.cache_fol / "e2e"
    shots.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=shots / "world_page.png")
    page.click(".detail .back")
    expect(page.locator(".player")).to_have_count(2)


def check_quit(page: Page, served_run: ServedRun) -> None:
    """Quit ends the run, and the page asks nothing more of the server it stopped.

    Every request is recorded from before the click; none to ``/events`` or
    ``/state`` may follow the quit. The wait covers the browser's delay before
    an ``EventSource`` reconnects, about 3 s in Chromium.
    """
    requests: list[str] = []
    page.on("request", lambda request: requests.append(request.url))
    page.once("dialog", lambda dialog: dialog.accept())
    page.click("#quit")
    expect(page.locator("#status")).to_contain_text("run ended")
    served_run.proc.wait(timeout=STOP_SECONDS)
    assert served_run.proc.returncode == 0
    page.wait_for_timeout(RECONNECT_WAIT_MS)
    quit_at = next(i for i, url in enumerate(requests) if url.endswith("/control/quit"))
    asked_after = [url for url in requests[quit_at:] if url.endswith(("/events", "/state"))]
    assert asked_after == []


def test_page_draws_zooms_steps_shows_a_player_and_quits(
    browser: Browser, served_run: ServedRun
) -> None:
    """The whole page against a paused run, from the first draw to the quit."""
    page = browser.new_page(viewport=VIEWPORT)
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(served_run.base_url)

    expect(page.locator("#status")).to_have_text("connected")
    expect(page.locator(".player")).to_have_count(2)
    assert turns(page) == [0, 0]
    expect(page.locator("#pause")).to_have_text("resume")
    # Terrains, buildings, sprites and names: far more than a background and a few shapes.
    assert canvas_colours(page) > MIN_COLOURS

    check_zoom(page)
    check_step_run_and_hold(page)
    check_detail(page)
    check_quit(page, served_run)
    assert errors == []
