# reboot tracking

Aligning laife with the sibling repos: agent instructions, `make check` behind pre-commit, skills, the `plans/` layout, and the drifted errors.
Analysis and decisions in [`00_start.md`](00_start.md).
Future work is the unnumbered backlog in [`../../plan.md`](../../plan.md).

## Key decisions

- The siblings are evidence, abyss's `00_template_alignment` the closest precedent (D2).
- Planning is cooperative; only small implementation changes run unsupervised (D7, Q9).
- The engine running is required evidence; the renderer choice is a backlog item (D8).
- mkdocs and its Pages workflow stay working throughout (D14).

## Phases

| #  | Phase                      | Plan                                                   | Status |
| -- | -------------------------- | ------------------------------------------------------ | ------ |
| 1  | Tooling and gates          | [`01_tooling_and_gates.md`](01_tooling_and_gates.md)   | done |
| 2  | Skills and worktrees       | [`02_skills_and_worktrees.md`](02_skills_and_worktrees.md) | done |
| 3  | Plans layout and errors    | [`03_plans_and_errors.md`](03_plans_and_errors.md)     | done |
| 4  | Agent instructions         | [`04_instructions.md`](04_instructions.md)             | done |
| 5  | Assessment and backlog     | [`05_assessment_and_backlog.md`](05_assessment_and_backlog.md) | done |

Status values: draft / planned / in progress / done / superseded / discarded.

Instructions come last because they describe the targets, gates and layout the first three phases create.

## Log

Append-only. Newest at the bottom.

- 2026-11-11 : surveyed the sibling repos and dotfiles; user answered p1 to p11 and Q1 to Q4. Branched `reboot/agent-alignment`. Measured the churn of moving the old plans (27 folders, 23 single-README). Bootstrapped this folder and a draft assessment folder; Q5 to Q10 open.
- 2026-11-12 : Q5 to Q10 folded in (Q5 b, rename all; Q6 measure; Q7 a; Q8 a; Q9 as proposed with prompt and model changes allowed when a phase names them; Q10 a). Renumbered this folder to 36 and the assessment to 37 to follow the old 10-35. Phase 3 rewritten for the full rename. Every phase `planned`.
- 2026-11-12 : Q10 corrected by the user: no roadmap folder. `37_assessment` deleted; folder 33 is updated in place and stays open (new phase 5); `plan.md` is the unnumbered backlog, and a folder is numbered only when a feature is picked from it.
- 2026-11-12 : executed phases 1 to 5, committed in the order the hooks allow: pre-commit stashes unstaged changes, so the plan content (phase 3) had to land before any commit that runs the plans hook, and its code files after the ruff config (phase 1). Commits: phase 3 markdown, phase 2, phase 1 tooling, a repo-wide pass of the new checks, phase 4, phase 5. `make check` green on the final tree: 229 passed, about 19 s in all, so the strict docs build stays inside `check` (Q6). A full hook run is about 10 s.
- 2026-11-12 : what the implementation found. The system Python 3.14 has no headers and pygame 2.6 has no 3.14 wheel: g7 now uses uv's managed 3.14.8 (box note `~/repos/plans/2026-11-12_00_uv_python_314.md`). `make sync` pulls torch with the full CUDA 12 stack and failed twice on a connection reset mid-cuDNN; it passed with `UV_CONCURRENT_DOWNLOADS=1 UV_HTTP_TIMEOUT=900`, and the weight is a `plan.md` item. ruff 0.17 brought CPY001 (ignored, as in the siblings), TC rules under a py314 target (target kept at py313, as in the siblings, because pydantic needs runtime annotations), ICN001 on `datetime` (fixed), and formatting of markdown code blocks (excluded). The pyright hook type-checked scratch scripts because passed file names override pyproject's include; scoped to `src` and `tests`. Every new gate was shown failing on a throwaway probe: plans, citations, prose, the strict docs build. `make prose` first passed with findings because a trailing grep masked the scanner's exit code; fixed. The citations gate found a real one, a klide plan path in the grill-me README. `make dev-llm-core` holds through `make test` and `make undev` restores the tag.
- 2026-11-12 : left open. Phase 2: the skills registering in a fresh session, and a real `scripts/spin_worktree` run, which creates a folder, a branch and a zellij session and is the user's to approve. Phase 4: the instructions loading in a fresh session.
- 2026-11-12 : reopened the ruff target on the user's request. Assessed on a scratch copy, then applied: `target-version = "py314"`, with `runtime-evaluated-base-classes` exempting pydantic models and the two `BaseModelKwargs` bases, and ruff moving the other annotation-only imports under `TYPE_CHECKING` (39 files). ruff only recognises a pydantic base in the same file, so `tests/test_models_build.py` rebuilds every laife pydantic model; shown failing by hand on `WResObserve`, whose import already carried a `noqa: TC001` for this reason. `make check` green, `game/main.py` imports. The earlier "py313 as in the siblings" entry stands as the record of why it was first kept. Also: the markdown code blocks are formatted after all, one commit of churn, and the version-drift check across the siblings went to `python-project-template`.
- 2026-11-12 : the user approved the real worktree test. `scripts/spin_worktree test/spin_worktree spin` (the test branch made at the reboot head first, since a new branch starts from `main`, which has none of the reboot) created `../laife-spin`, ran `make sync` from uv's cache, and started `wt-laife-spin` with Remote Control. Asked over cross-session message, that session listed `principles`, `deslopify` and `grill-me` among its skills and named sections of the instructions without opening them. Its `make check` found a real fault: `test_root_is_laife` asserted the folder name, which is `laife-spin` in a worktree; the test now checks the root's `pyproject.toml`, and `make check` passes inside the worktree. Phases 2 and 4 done, and the folder with them. python-project-template carries the same folder-name assertion in `tests/params/test_project_name_paths.py`, reported to the user rather than changed.
