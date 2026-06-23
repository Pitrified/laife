.PHONY: help sync run lint format typecheck test docs dev-llm-core

MAKEFLAGS += --no-print-directory
.DEFAULT_GOAL := help

LLM_CORE_PATH ?= ../llm-core

help:  ## Show this help (list targets and their descriptions)
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

#########
# SETUP #
#########

sync:  ## Install all dependencies (extras and groups)
	uv sync --all-extras --all-groups

#######
# RUN #
#######

run:  ## Run the game
	uv run game/main.py

########
# LINT #
########

lint:  ## Lint with ruff
	uv run ruff check .

format:  ## Format with ruff
	uv run ruff format .

typecheck:  ## Type-check with pyright
	uv run pyright

test:  ## Run the test suite
	uv run pytest

########
# DOCS #
########

docs:  ## Serve the docs locally with MkDocs
	uv run mkdocs serve

########
# DEPS #
########

dev-llm-core:  ## Install llm-core from a local editable path
	uv pip install -e "$(LLM_CORE_PATH)[all]"
	@echo "llm-core installed from $(LLM_CORE_PATH) - run 'uv sync' to revert"
