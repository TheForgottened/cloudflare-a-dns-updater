.PHONY: help lint install-all-dependencies cicd-check

help: ## This help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

lint: ## Run linting scripts.
	uv run ruff check --force-exclude . -v
	uv run ruff format --force-exclude --check . -v

install-all-dependencies: ## Prepare dev environment.
	uv sync --all-groups

cicd-check: install-all-dependencies lint ## CI/CD checks (lint and tests).
	uv run pre-commit run --all-files --show-diff-on-failure
