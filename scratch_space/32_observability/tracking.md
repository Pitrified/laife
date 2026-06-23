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
| 1  | struct log analysis            | [`01_struct_log_analysis.md`](01_struct_log_analysis.md) | planned |
| 2  | textual tui inspector          | [`02_textual_tui.md`](02_textual_tui.md)      | planned |
| 3  | pause / step the game loop     | [`03_loop_pause.md`](03_loop_pause.md)        | planned |

Status values: draft / planned / in progress / done / superseded / discarded.

## Log

Append-only. Newest at the bottom.

- 2026-06-23 : bootstrapped the plan folder from README; drafted phases 1-3.
