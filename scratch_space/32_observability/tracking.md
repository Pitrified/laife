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
| 2  | textual tui inspector          | [`02_textual_tui.md`](02_textual_tui.md)      | done |
| 3  | pause / step the game loop     | [`03_loop_pause.md`](03_loop_pause.md)        | done |
| 4  | inspector fine-tuning          | [`04_fine_tunes.md`](04_fine_tunes.md)        | done |
| 5  | inspector fine-tuning, round 2 | [`04.1_fine_tunes.md`](04.1_fine_tunes.md)    | planned |

Status values: draft / planned / in progress / done / superseded / discarded.

Not a phase: [`05_random_warnings.md`](05_random_warnings.md) - unrelated
startup/shutdown warnings (SystemExit on quit, pydantic V1 on py3.14, pygame
AVX2). Spun out as a separate future cleanup, not part of the inspector.

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
- 2026-07-09 : phase 2 done - built the Textual inspector as planned. New
  `tui` dependency group (`textual>=0.60`) and `make tui` target; new
  subpackage `src/laife/observability/` with `log_reader.py` (pure
  `tail_jsonl` async generator, no Textual dependency, unit-tested against
  fixture `.jsonl` files) and `tui.py` (`ObservabilityApp`: a `DataTable`
  fed by a reader worker -> `asyncio.Queue` -> UI worker pair, with player
  filter, event-type filter, the `(player, turn)` focus-turn feature phase 1
  unlocked, and a follow-tail toggle). Tested with Textual's headless
  `App.run_test()` pilot, plus a manual smoke run against a real
  `cache/game_*.jsonl` confirming a build turn's
  `llm_call -> action -> world_request -> world_response ->
  mission_transition` chain groups correctly under focus-turn. Full
  test/lint/typecheck suite green (195 tests).
- 2026-07-09 : phase 3 plan detailed in `03_loop_pause.md`. Key decisions:
  pause unit is one player turn (gate at the top of `Player.play()`, world
  runner never gated to avoid deadlocking in-flight turns); trigger from
  pygame `KEYDOWN` (space toggle, `n` step) rather than TUI-driven IPC -
  resolves the open question in `00-start.md`. New `SimControl`
  (asyncio.Condition over running/step_permits) in
  `src/laife/entities/sim_control.py`, one `EVT_SIM_CONTROL` marker event
  with a `state` field. Status stays `planned` - not yet implemented.
- 2026-07-09 : phase 3 done - `SimControl` landed in
  `src/laife/entities/sim_control.py` and wired through `Player.play()`
  (optional gate, default `None`), the renderer (`K_SPACE` toggle with a
  `[PAUSED]` caption, `K_n` step), `game/main.py`, and the TUI (red
  `sim_control` rows). Deviations from the plan, found while implementing:
  an `asyncio.Event` pulse replaced the planned `asyncio.Condition` so the
  triggers stay synchronous for the pygame pump; the step marker is emitted
  at consumption carrying the released `(player, turn)`; `resume()` drops
  unconsumed step permits (a banked permit would otherwise leak a spurious
  step into a later pause - caught by the smoke run). 9 new unit tests;
  manual smoke ran headless (real jsonl round trip + `SDL_VIDEODRIVER=dummy`
  synthetic keys) since `make run` needs a live LLM backend. Full suite
  green: 204 tests, ruff and pyright clean. See
  [`03_loop_pause.md`](03_loop_pause.md#outcome).
- 2026-07-10 : recorded what phase 3 did not cover (see
  [`03_loop_pause.md`](03_loop_pause.md#missing)): the interactive
  `make run` smoke - space/`n` against a live game with a real LLM backend
  - was not performed; the headless smoke covered the code paths but not
  the real-run feel. To be done once on a box with the game running.
- 2026-07-10 : unblocked the interactive smoke. `make run` was crashing at
  `Player` construction with `MissingPromptVariablesError: ['sender_name']`
  - a pre-existing bug (not from phases 1-3; `player_replier.py` last
  touched in `c6ee7af "migrate to llm_core"`): `PlayerReplyInput` requires
  `sender_name` and it is plumbed through `world_runner`/`WRecInteract`/
  `receive_message`, but `prompts/player_reply/v1.jinja` never referenced
  it, and `StructuredLLMChain` validates every input field against the
  prompt. Fixed by naming the sender in the template header
  (`## The player addressing you ({{ sender_name }})`). Game now runs past
  construction; suite still 204 passed.
- 2026-07-10 : phase 3 interactive smoke performed - `make run` + `make tui`
  against a live LLM backend, space/`n` on the focused pygame window, all
  green. This closes the last outstanding item across phases 1-3; the
  observability effort is complete. See
  [`03_loop_pause.md`](03_loop_pause.md#missing).
- 2026-07-10 : phase 4 planned from the post-smoke fine-tune notes
  ([`04_fine_tunes.md`](04_fine_tunes.md)). Three grounded findings: the
  `action` event logs `str(action)` which omits the action type (pydantic
  v2 `__str__` drops the class name); `world_request`/`world_response` pairs
  are two rows where one would do (the request carries only `kind`); and
  only the brain's action-picker emits `llm_call` - the planner, replier,
  and mission generator each make an unlogged LLM call. Goals: add
  `action_type`, collapse the request/response pair render-side, close the
  three `llm_call` gaps (with a `stage` field), and refresh the phase-1/2
  docs. Status `planned` - not yet implemented. The startup/shutdown
  warnings ([`05_random_warnings.md`](05_random_warnings.md)) are spun out as
  a separate future cleanup, not a phase of this feature.
- 2026-07-11 : phase 4 done - all four goals landed and verified end-to-end
  against a real game log. New `logger.timed_llm_call` context manager
  unifies LLM-call timing; the brain plus the previously-unlogged planner,
  replier, and mission generator now all emit `llm_call` with a `stage`
  field (real-log check surfaced `stage=mission` events that were invisible
  before). `action` events carry `action_type`; the TUI leads the action
  detail with it. `world_request`/`world_response` pairs collapse to one row
  render-side via `_pending_round_trips` (upgraded in place, bypassed under
  turn focus, both events kept in the `.jsonl`) - real-log check collapsed
  exactly 304 pairs (715 -> 411 rows). 9 new tests; full suite 213 passed,
  ruff and pyright clean. One test-only fix (planner fixture now sets
  `turn`). Interactive `make run` visual pass not done (needs a focused
  window); headless pilot covered the render path. See
  [`04_fine_tunes.md`](04_fine_tunes.md#outcome). Observability phases 1-4
  all done; only the spun-out warnings (05) remain as a separate future item.
- 2026-07-11 : phase 5 planned from a second fine-tune note
  ([`04.1_fine_tunes.md`](04.1_fine_tunes.md)). Two grounded findings: the
  `stage=mission` llm_call is an orphan - `_start_new_mission` builds the new
  mission but only `alg.log`s it, emitting no struct-log event, so the
  objective never reaches the TUI; and after phase 4's pair-collapse a
  distance-N move still emits N identical `WRecMove -> WResMove` rows in a
  row. Goals: emit a new `mission_start` event (player, turn, objective) and
  render it; and collapse consecutive identical rows with an `xN` suffix,
  mirroring `alog`'s run-collapse, disabled under turn focus. Main risk noted
  in the plan: the run-collapse must cooperate with phase 4's in-place pair
  upgrade and the `_pending_round_trips` indices - factor one
  `_merge_if_repeat` helper, with a pure-recompute fallback if the index
  bookkeeping gets tangled. Status `planned` - not yet implemented.
