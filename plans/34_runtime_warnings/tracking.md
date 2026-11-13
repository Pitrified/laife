# runtime warnings cleanup - implementation tracking

Fix or silence the three startup/shutdown warnings collected during the
observability effort (`SystemExit` on quit, pydantic V1 shim on py3.14,
pygame AVX2 build note). Analysis and decisions in [`00_start.md`](00_start.md);
original capture in
[`32_observability/05.1_random_warnings.md`](../32_observability/05.1_random_warnings.md).

## Key decisions

- One phase per warning, ordered by value; suppression with a named upstream issue
  is an acceptable outcome for the two dependency warnings.

## Phases

| #  | Phase                        | Plan                                              | Status |
| -- | ---------------------------- | ------------------------------------------------- | ------ |
| 4  | judge after collision check  | [`04_judge_after_collision.md`](04_judge_after_collision.md) | done |
| 2  | dependency upgrade, llm-core then laife | [`02_pydantic_v1_warning.md`](02_pydantic_v1_warning.md) | done |
| 1  | clean shutdown on quit, parked | [`01_clean_shutdown.md`](01_clean_shutdown.md)    | draft  |
| 3  | pygame avx2 warning, parked  | [`03_pygame_avx2_warning.md`](03_pygame_avx2_warning.md) | draft  |

Status values: draft / planned / in progress / done / superseded / discarded.

## Log

Append-only. Newest at the bottom.

- 2026-07-11 : bootstrapped the folder from `32_observability/05.1_random_warnings.md`;
  traced the quit `SystemExit` to `sys.exit()` in `WorldRenderer.quit()` running
  inside the `asyncio.gather` of `game/main.py`; drafted phases 1-3.
- 2026-11-13 : picked with the user on branch `fix/warnings_judge_order`.
  Phases 1 and 3 parked with the renderer question; the judge order added as phase 4, run first;
  phase 2 rewritten as a full dependency upgrade through llm-core, after langchain-core 1.8.0 was checked not to warn.
  Decisions and open questions in `00_start.md`.
- 2026-11-13 : phase 4 done: collision check before the build judge; test shown failing on the old order; `make check` and `make headless` pass.
- 2026-11-13 : phase 2: llm-core v0.3.0 made locally; laife relocked on the same stack with no code change, pydantic warning gone, test warnings 27 to 15.
- 2026-11-13 : phase 2 done: laife pinned to llm-core v0.3.0, `make check` and `make headless` pass. Left in the folder: phases 1 and 3, parked with the renderer. `make run` on g4 is the user's.
