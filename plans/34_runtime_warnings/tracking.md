# runtime warnings cleanup - implementation tracking

Fix or silence the three startup/shutdown warnings collected during the
observability effort (`SystemExit` on quit, pydantic V1 shim on py3.14,
pygame AVX2 build note). Analysis and decisions in [`00_start.md`](00_start.md);
original capture in
[`32_observability/05_random_warnings.md`](../32_observability/05_random_warnings.md).

## Key decisions

- One phase per warning, ordered by value; suppression with a named upstream issue
  is an acceptable outcome for the two dependency warnings.

## Phases

| #  | Phase                        | Plan                                              | Status |
| -- | ---------------------------- | ------------------------------------------------- | ------ |
| 1  | clean shutdown on quit       | [`01_clean_shutdown.md`](01_clean_shutdown.md)    | draft  |
| 2  | pydantic v1 warning          | [`02_pydantic_v1_warning.md`](02_pydantic_v1_warning.md) | draft  |
| 3  | pygame avx2 warning          | [`03_pygame_avx2_warning.md`](03_pygame_avx2_warning.md) | draft  |

Status values: draft / planned / in progress / done / superseded / discarded.

## Log

Append-only. Newest at the bottom.

- 2026-07-11 : bootstrapped the folder from `32_observability/05_random_warnings.md`;
  traced the quit `SystemExit` to `sys.exit()` in `WorldRenderer.quit()` running
  inside the `asyncio.gather` of `game/main.py`; drafted phases 1-3.
