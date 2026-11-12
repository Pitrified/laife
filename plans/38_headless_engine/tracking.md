# headless engine - implementation tracking

Run the engine with no window and a scripted LLM, writing the structured log as a live run does.
Analysis, proposals and open questions in [`00_start.md`](00_start.md).

## Key decisions

- Rule-based scripted LLM, a fixed cycling script per player, the fake model in laife (Q1-Q3).
- `max_turns` on `Player.play()`; renderer skipped, renderer checks moved to the `plan.md` backlog (Q4, Q5).
- The gate checks a minimal run; headless mode is a development tool first (Q6).
- `setup_world()` moves into the package and takes a seeded `random.Random`.
- `Player` and `WorldRunner` take their own chat config, defaulting to `chat.default` (phase 3).

## Phases

| #  | Phase                        | Plan                                                 | Status |
| -- | ---------------------------- | ---------------------------------------------------- | ------ |
| 1  | shared world setup with seed | [`01_world_setup_seed.md`](01_world_setup_seed.md)   | done    |
| 2  | turn limit                   | [`02_max_turns.md`](02_max_turns.md)                 | done    |
| 3  | scripted chat model          | [`03_scripted_chat.md`](03_scripted_chat.md)         | done    |
| 4  | headless entry and gate      | [`04_headless_entry.md`](04_headless_entry.md)       | done    |

Status values: draft / planned / in progress / done / superseded / discarded.

## Log

Append-only. Newest at the bottom.

- 2026-11-12 : picked from `plan.md`; read the chain wiring, llm-core's `FakeChatModel`, the turn loop and the renderer; wrote the proposals and Q1-Q6.
- 2026-11-12 : Q1-Q6 answered with the user; renderer checks added to `plan.md`; drafted phases 1-4.
- 2026-11-12 : per-player and per-world chat config chosen for phase 3; phases 1-4 planned.
- 2026-11-12 : phase 1 done: `setup_world()` in the package with a `random.Random`; it needs a running loop because of `alg.log`.
- 2026-11-12 : phase 2 done: `play(max_turns=...)`; cancelling the runner moved to phase 4.
- 2026-11-12 : phase 3 done: `scripted_chat.py`, and a `chat_config` argument on `Player` and `WorldRunner`.
- 2026-11-12 : phase 4 done: `make headless`, the gate in `make check`; dropped the pygame re-exports from `laife.entities`; `run_headless` re-raises a dead world task instead of hanging. Folder done.
