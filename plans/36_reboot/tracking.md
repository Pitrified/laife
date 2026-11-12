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
| 1  | Tooling and gates          | [`01_tooling_and_gates.md`](01_tooling_and_gates.md)   | planned |
| 2  | Skills and worktrees       | [`02_skills_and_worktrees.md`](02_skills_and_worktrees.md) | planned |
| 3  | Plans layout and errors    | [`03_plans_and_errors.md`](03_plans_and_errors.md)     | planned |
| 4  | Agent instructions         | [`04_instructions.md`](04_instructions.md)             | planned |
| 5  | Assessment and backlog     | [`05_assessment_and_backlog.md`](05_assessment_and_backlog.md) | planned |

Status values: draft / planned / in progress / done / superseded / discarded.

Instructions come last because they describe the targets, gates and layout the first three phases create.

## Log

Append-only. Newest at the bottom.

- 2026-11-11 : surveyed the sibling repos and dotfiles; user answered p1 to p11 and Q1 to Q4. Branched `reboot/agent-alignment`. Measured the churn of moving the old plans (27 folders, 23 single-README). Bootstrapped this folder and a draft assessment folder; Q5 to Q10 open.
- 2026-11-12 : Q5 to Q10 folded in (Q5 b, rename all; Q6 measure; Q7 a; Q8 a; Q9 as proposed with prompt and model changes allowed when a phase names them; Q10 a). Renumbered this folder to 36 and the assessment to 37 to follow the old 10-35. Phase 3 rewritten for the full rename. Every phase `planned`.
- 2026-11-12 : Q10 corrected by the user: no roadmap folder. `37_assessment` deleted; folder 33 is updated in place and stays open (new phase 5); `plan.md` is the unnumbered backlog, and a folder is numbered only when a feature is picked from it.
