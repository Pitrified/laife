---
status: in progress
priority: 1
description: |
  Bring laife back in line with the sibling repos after four months idle: agent instructions,
  a single fast `make check` behind pre-commit, repo-local skills, a `plans/` layout the
  tracked-development tooling reads, and the errors that drifted in meanwhile.
---

# Reboot

## Origin

laife was last touched on 2026-07-11.
Since then the sibling repos (klide, abyss, house-renderer, and the dotfiles) settled on conventions laife never picked up.
On 2026-11-11 the user asked for a survey of those repos, a list of what laife is missing, and a reboot.

## Survey, 2026-11-11

Read: `abyss`, `klide`, `house-renderer`, `lang-tools`, `fala-language-tutor`, `genealogy-gramps-fn`, `~/dotfiles/claude`, `linux-box-cloudflare/configs/claude`.
The closest precedent is `abyss/plans/00_template_alignment/`, abyss's own reboot.

### Patterns laife lacks

1. **No `CLAUDE.md`.** Every sibling has the one-line `@.github/copilot-instructions.md` import. Claude sessions in laife have never loaded the repo instructions.
2. **Instruction sections.** klide and house-renderer carry "How to write", "Planning" and "How to build". laife carries only the em dash rule.
3. **One `make check`.** abyss and house-renderer have one target for lint, format, types and tests, with the rule that it runs before the commit, not after.
4. **A commit gate.** abyss installs pre-commit with `make hooks`, ruff and pyright pinned alike in `pyproject.toml` and `.pre-commit-config.yaml`. This box has no GitHub credentials, so CI never runs a gate here; the local hook is the only one.
5. **The gate contract** (`klide/meta/gates.md`): one command, actionable failure, fast enough to be run, shown failing before it counts.
6. **`plans/NN_name/` with frontmatter**, read by `plans.py list` and `check`. laife's tracked folders sit in `scratch_space/` among notebooks, and `plans.py` finds nothing.
7. **Unattended cycles** as house-renderer runs them: a whole folder on a feature branch, the agent answering its own question batch as "decided by the agent", a commit per part with `make check` green.
8. **Verification by running the thing.** abyss `make e2e`, klide's frame and session gates. laife verifies by unit tests and a manual live game against OpenAI.
9. **`scripts/spin_worktree`** from the sibling-worktree skill.
10. **A box section** saying which machine runs what.
11. **Repo-local skills** in klide: `principles`, `deslopify`, `grill-me`.

### Errors and drift in laife

- `.github/copilot-instructions.md` says Python 3.13 twice; `pyproject.toml` pins `==3.14.*`.
- `make dev-llm-core` cannot hold: every other target runs plain `uv run`, which re-syncs from `uv.lock` and reverts the editable install. Measured in abyss's reboot log, 2026-08-10, which names laife's target.
- `.claude/settings.local.json` allows `rtk *` commands; the rtk hook was dropped from the dotfiles on 2026-10-14.
- `.github/agents/draft-to-plan.agent.md` is a Copilot agent; abyss dropped `.github/agents/` in its reboot.
- Two plan citations in code: `src/laife/entities/sim_control.py` and `src/laife/meta/logger.py` name `scratch_space/` plan files.
- Lint errors in two scratch files (`I001`), per the 2026-07-06 assessment.

### Churn of moving the old plans

`scratch_space/` holds 27 numbered folders, `10_` to `35_`, plus nine unnumbered code and notebook folders that stay where they are.
Of the 27:

- 26 are markdown only; `12_action_structure` also has a notebook.
- 23 are a single `README.md` with no frontmatter. `plans.py` skips any folder without `00_start.md`, so each would need a rename and three frontmatter fields.
- Three have a `tracking.md` (32, 34, 35). 32 has statuses outside the enum (`draft - analyzed - unplanned`).
- The number 22 is used twice (`22_mission_step_runner`, `22_player_inventory`).
- References to fix: 4 outside `scratch_space/` (instructions, `ruff.toml`, the two code citations above), around 16 links between the folders.

Renaming them into a `check`-clean `plans/` is around 30 renames and 30 frontmatter edits for folders that are all closed except 31 and 33.
Parking them is no edit at all: they stay in `scratch_space/` as history, and `plans/` starts at `00`.

### Box facts

- This is g7: unattended sessions and some interactive use. g4 is where a person is.
- No `DISPLAY` in agent sessions. `libsdl2-dev` and `libfreetype-dev` are installed; Python 3.14.4 is the system Python.
- No `.venv` in the repo yet. `pre-commit` is not on `PATH`; it comes in as a dev dependency.
- `scratch_space/rebirth_/README.md` (2026-02) already listed "Runner with no pygame - text only" as a renderer idea.

## Decisions

From the user's answers on 2026-11-11, by survey item.

- D1 (p1): add `CLAUDE.md` importing `.github/copilot-instructions.md`.
- D2 (p2): rewrite the instructions with the sibling sections, adapted to laife.
- D3 (p3): add `make check`.
- D4 (p4, Q2): pre-commit, as abyss.
- D5 (p5): adopt the gate contract. "Fast enough to run" is the rule that matters most: a slow gate gets skipped.
- D6 (p6, Q1, Q5): plans go in `plans/`, and all 27 old folders are renamed in and brought to `plans.py check`. Their numbers stay, so this folder is `36_reboot`.
- D7 (p7): less autonomy than house-renderer. Planning is cooperative and fleshes out the functional and technical details with the user. Only small implementation changes run unsupervised.
- D8 (p8): the engine running is mandatory evidence, while planning and while implementing. Whether pygame stays as the renderer, or laife moves to a web app, is an open assessment, written into `plan.md` as backlog items until it is picked.
- D9 (p9): adopt `scripts/spin_worktree`.
- D10 (p10): g7 is the dev and unattended box, sometimes used with a UI; g4 is the human one.
- D11 (p11): migrate klide's `principles`, `deslopify` and `grill-me` skills into `.claude/skills/`.
- D12: fix every error listed above.
- D13: folder 33, the 2026-07-06 assessment, is brought up to date against the code and stays open (phase 5).
- D16 (Q6, Q7): `make check` is the full set, `mkdocs build --strict` included if measurement says it is fast; pytest is not in the pre-commit hook.
- D17: nothing under `src/` points at a plan or at `scratch_space/`. `plans.py check --citations` enforces it.
- D18 (Q8): delete `.github/agents/draft-to-plan.agent.md`.
- D19 (Q9): unsupervised work is bounded as proposed, except that prompt versions and data models may change when the phase plan names that change as its aim.
- D20 (Q10): `plan.md` is the one backlog: future work, unnumbered. The README todo list folds into it. A numbered folder is created only when a feature is picked from `plan.md` to implement; there is no roadmap folder.
- D14 (Q3): keep mkdocs. Its point is the Pages CI already set up; the reboot must not break `docs.yml`.
- D15 (Q4): work on the `reboot/agent-alignment` branch.

## Open questions

- Q1: where plans live.
  - ANS: `plans/`, folder number decided after the churn assessment.
- Q2: commit gate, pre-commit or `.githooks`.
  - ANS: pre-commit.
- Q3: keep mkdocs and the Pages workflow.
  - ANS: keep.
- Q4: branch before writing.
  - ANS: yes, `reboot/agent-alignment`.
- Q5: the old numbered folders, given the churn above.
  - a. park: leave `scratch_space/10_` to `35_` untouched as history; `plans/` starts with `00_reboot` and `01_assessment`, which indexes them.
  - b. rename all 27 into `plans/`, fix links, add frontmatter until `plans.py check` passes; this folder becomes `36_reboot`.
  - c. rename only the open ones (31, 33) into `plans/`, park the rest.
  - Recommended: a, because every folder but 31 and 33 is closed, and 01_assessment absorbs both of those.
  - ANS: b, rename all. The `src/` citations are removed regardless: code does not point at plans or scratch.
- Q6: what `make check` runs. The test suite took about 9 s in July. `mkdocs build --strict` is what CI runs and would catch a docs break locally.
  - a. ruff check, ruff format --check, pyright, pytest, `plans.py check`, the house-style scan; `mkdocs build --strict` as its own `make docs-check`.
  - b. the same plus `mkdocs build --strict` inside `check`.
  - Recommended: b if the strict build is fast when measured in phase 1, else a. The ceiling is the speed rule in D5.
  - ANS: measure it, then decide.
- Q7: what the pre-commit hook runs. abyss runs ruff, format, pyright, nbstripout, detect-secrets and file hygiene, and leaves tests to `make check`.
  - a. as abyss, plus `plans.py check` and the house-style scan.
  - b. as a, plus pytest.
  - Recommended: a, so a commit stays quick; pytest stays in `make check`, which the instructions say to run before every commit.
  - ANS: a, pytest not in the hook.
- Q8: `.github/agents/draft-to-plan.agent.md`.
  - a. delete; tracked-development and `grill-me` cover the same step for Claude.
  - b. keep, for Copilot in VS Code.
  - Recommended: a, unless Copilot agents are still in use on g4.
  - ANS: a, delete.
- Q9: what counts as a small implementation change that may run unsupervised (D7).
  - Proposed: a phase whose file is `planned` with no open `NEW_ANS`, on a feature branch, no new dependencies, no change to an LLM prompt version or a public data model, `make check` green per commit, no merge to `main`. Anything outside that stops and asks.
  - ANS: all fair, except that a prompt version or data model change may be exactly what a folder is for; allowed when the phase plan names it.
- Q10: `plan.md` and the README todo list once `01_assessment` has a roadmap.
  - a. the roadmap replaces both; `plan.md` is deleted and the README links to `plans/`.
  - b. keep `plan.md` as the roadmap.
  - Recommended: a, so the backlog lives in one place that `plans.py list` reads.
  - ANS: a, one source of truth.
  - Corrected 2026-11-12: "one source of truth" is `plan.md`, not a new folder. A folder with a number is a feature being implemented; the backlog has no numbers until something is picked from it. Neither option above said this, so D20 holds the answer.
