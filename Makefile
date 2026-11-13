.PHONY: help sync hooks run headless tui lint format typecheck test plans prose docs-check check nbstrip docs dev-llm-core undev

MAKEFLAGS += --no-print-directory
.DEFAULT_GOAL := help

# Every target that runs project code goes through UV_RUN. The --no-sync matters:
# a plain `uv run` re-syncs the environment from uv.lock first, which silently
# undoes the `uv pip install -e` done by dev-llm-core.
UV_RUN := uv run --no-sync

LLM_CORE_PATH ?= ../llm-core
TURNS ?= 6
SEED ?= 0

help:  ## Show this help (list targets and their descriptions)
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

#########
# SETUP #
#########

sync:  ## Install all dependencies (extras and groups) - the only target that syncs
	uv sync --all-extras --all-groups

hooks:  ## Install the pre-commit git hooks, once per clone
	$(UV_RUN) pre-commit install

#######
# RUN #
#######

run:  ## Run the game
	$(UV_RUN) game/main.py

headless:  ## Run with no window and a scripted LLM; TURNS=6 SEED=0
	$(UV_RUN) game/headless.py --turns $(TURNS) --seed $(SEED)

tui:  ## Run the observability TUI (tails the newest cache/game_*.jsonl)
	$(UV_RUN) python -m laife.observability.tui

#########
# CHECK #
#########

lint:  ## Report lint and formatting problems, changing nothing
	$(UV_RUN) ruff check .
	$(UV_RUN) ruff format --check .

format:  ## Apply what ruff can fix: the safe lint fixes, then the formatting
	$(UV_RUN) ruff check --fix .
	$(UV_RUN) ruff format .

typecheck:  ## Type-check with pyright
	$(UV_RUN) pyright

test:  ## Run the test suite; ARGS="tests/test_x.py -k name" narrows it
	$(UV_RUN) pytest $(ARGS)

plans:  ## Check the plan folders and that nothing outside plans/ cites one
	python3 scripts/plans.py check --citations

prose:  ## Fail on what the writing rules ban outright, em dashes first, in tracked markdown
	@out=$$(git ls-files -z '*.md' | xargs -0 .claude/skills/deslopify/scripts/deslop-scan.sh --only house_rules --quiet); \
		rc=$$?; echo "$$out" | grep -v '^clean\|^skipped'; exit $$rc

docs-check:  ## Build the docs as CI does, failing on any warning
	$(UV_RUN) mkdocs build --strict

check: lint typecheck plans prose test docs-check  ## Everything mechanical: lint, formatting, types, plans, prose, tests, docs

nbstrip:  ## Strip notebook outputs (pre-commit only verifies, this fixes)
	@files=$$(git ls-files '*.ipynb'); \
	if [ -n "$$files" ]; then $(UV_RUN) nbstripout $$files; else echo "no tracked notebooks"; fi

########
# DOCS #
########

docs:  ## Serve the docs locally with MkDocs
	$(UV_RUN) mkdocs serve

########
# DEPS #
########
# Point the venv at a local checkout of llm-core instead of the git tag pinned in
# pyproject.toml. The install lives only in .venv, so any `uv sync`, or any `uv run`
# without --no-sync (the editor's test runner, a terminal), puts the pinned tag back.
# The targets above use --no-sync; `make undev` is the deliberate way back.

dev-llm-core:  ## Install llm-core from a local editable path (see DEPS notes)
	uv pip install -e "$(LLM_CORE_PATH)[openai,chroma]"
	@echo "llm-core installed from $(LLM_CORE_PATH)"
	@echo "WARNING: a bare 'uv run' or 'uv sync' reverts this to the pinned tag."
	@echo "         use make targets (they pass --no-sync), or 'make undev' to revert on purpose."

undev:  ## Revert every local editable override, back to the pinned versions
	uv sync --all-extras --all-groups
