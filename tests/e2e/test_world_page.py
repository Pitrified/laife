"""The world page against a real serving run: draws, steps, pauses, quits.

One test walks the whole sequence, since each step needs the state the one
before left, and starting a run costs a few seconds. It ends with a
screenshot in ``cache/e2e/`` for a person or an agent to look at.
"""

import re
from typing import TYPE_CHECKING

from playwright.sync_api import expect

from laife.params.laife_params import get_laife_params

if TYPE_CHECKING:
    from playwright.sync_api import Browser
    from playwright.sync_api import Page
    from playwright.sync_api import ViewportSize

    from tests.e2e.conftest import ServedRun

STOP_SECONDS = 10
VIEWPORT: ViewportSize = {"width": 1400, "height": 850}


def turns(page: Page) -> list[int]:
    """Each card's turn, in card order."""
    found = []
    for meta in page.locator(".player .meta").all_text_contents():
        match = re.search(r"turn (\d+)", meta)
        assert match is not None, meta
        found.append(int(match.group(1)))
    return found


def canvas_has_drawing(page: Page) -> bool:
    """Tell whether the canvas holds more than one colour."""
    return page.evaluate(
        """() => {
            const canvas = document.getElementById("world");
            const ctx = canvas.getContext("2d");
            const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
            for (let i = 4; i < data.length; i += 4 * 97) {
                if (data[i] !== data[0] || data[i + 1] !== data[1] || data[i + 2] !== data[2]) {
                    return true;
                }
            }
            return false;
        }"""
    )


def test_page_draws_steps_pauses_and_quits(browser: Browser, served_run: ServedRun) -> None:
    """The page shows the paused world, steps one turn, runs and holds, then ends the run."""
    page = browser.new_page(viewport=VIEWPORT)
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(served_run.base_url)

    expect(page.locator("#status")).to_have_text("connected")
    expect(page.locator(".player")).to_have_count(2)
    assert turns(page) == [0, 0]
    assert canvas_has_drawing(page)
    expect(page.locator("#pause")).to_have_text("resume")

    # Step: one player plays one turn, and its card lists the action.
    page.click("#step")
    expect(page.locator(".player .meta").filter(has_text="turn 1")).to_have_count(1)
    expect(page.locator(".player .actions li").first).to_be_visible()

    # Resume, let it run, pause: the turns advance, then hold.
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

    shots = get_laife_params().paths.cache_fol / "e2e"
    shots.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=shots / "world_page.png")

    # Quit, after the confirmation: the page says so and the process ends.
    page.once("dialog", lambda dialog: dialog.accept())
    page.click("#quit")
    expect(page.locator("#status")).to_contain_text("run ended")
    served_run.proc.wait(timeout=STOP_SECONDS)
    assert served_run.proc.returncode == 0
    assert errors == []
