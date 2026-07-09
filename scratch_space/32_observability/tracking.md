# observability - implementation tracking

Building an observability surface for the laife simulation, decoupled from the
game loop, reading the existing JSON-lines struct log. Analysis and decisions in
[`00-start.md`](00-start.md); original draft in [`README.md`](README.md).

## Key decisions

- Decouple completely: the inspector is a separate process reading the existing
  `.jsonl` sink. Pygame stays out of the observability path. (see `00-start.md`)

## Phases

| #  | Phase                          | Plan                                          | Status  |
| -- | ------------------------------ | --------------------------------------------- | ------- |
| 1  | struct log analysis            | [`01_struct_log_analysis.md`](01_struct_log_analysis.md) | done |
| 2  | textual tui inspector          | [`02_textual_tui.md`](02_textual_tui.md)      | planned |
| 3  | pause / step the game loop     | [`03_loop_pause.md`](03_loop_pause.md)        | planned |

Status values: draft / planned / in progress / done / superseded / discarded.

## Log

Append-only. Newest at the bottom.

- 2026-06-23 : bootstrapped the plan folder from README; drafted phases 1-3.
- 2026-07-09 : phase 1 done - added `(player, turn)` correlation to every
  struct-log event, stamped once in `Player._world_request()` and threaded
  into `PlayerBrain.think()`; fixed `world_request` logging at `DEBUG` (now
  `INFO` like everything else); generalized `world_response` to all six
  request kinds instead of just build/craft; removed the dead `EVT_LLM_RESULT`
  constant and the unused `Player.world_request()` method. Full test/lint/
  typecheck suite green. Landed in commit `f7411a3`. See
  [`01_struct_log_analysis.md`](01_struct_log_analysis.md#outcome).
- 2026-07-09 : phase 2 plan detailed in `02_textual_tui.md` (dependency,
  subpackage layout, `log_reader.tail_jsonl` + `tui.py` split, filter/focus
  design, testing approach). Status stays `planned` - not yet implemented.
