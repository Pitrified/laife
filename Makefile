LLM_CORE_PATH ?= ../llm-core

.PHONY: dev-llm-core

dev-llm-core: ## Install llm-core from a local editable path
	uv pip install -e "$(LLM_CORE_PATH)[all]"
	@echo "llm-core installed from $(LLM_CORE_PATH) - run 'uv sync' to revert"
