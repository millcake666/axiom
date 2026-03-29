# Introspection targets
# ---------------------

.PHONY: help
help: header targets

.PHONY: header
header:
	@echo "\033[34mEnvironment\033[0m"
	@echo "\033[34m---------------------------------------------------------------\033[0m"
	@printf "\033[33m%-23s\033[0m" "PROJECT_NAME"
	@printf "\033[35m%s\033[0m" $(PROJECT_NAME)
	@echo ""
	@printf "\033[33m%-23s\033[0m" "PROJECT_VERSION"
	@printf "\033[35m%s\033[0m" $(PROJECT_VERSION)
	@echo ""
	@printf "\033[33m%-23s\033[0m" "GIT_REVISION"
	@printf "\033[35m%s\033[0m" $(GIT_REVISION)
	@echo "\n"

.PHONY: targets
targets:
	@echo "\033[34mDevelopment Targets\033[0m"
	@echo "\033[34m---------------------------------------------------------------\033[0m"
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'


# Development targets
# -------------

.PHONY: sync
sync: ## Install dependencies
	uv sync


# Check, lint and format targets
# ------------------------------

.PHONY: lint
lint: ## Run linter
	uv run ruff check

.PHONY: format
format: ## Run code formatter
	uv run ruff format
	uv run ruff check --fix

.PHONY: check-types
check-types: ## Check types
	uv run mypy axiom-*/src oltp/axiom-*/src olap/axiom-*/src --install-types

.PHONY: check-pylint
check-pylint: ## Run pylint on src and tests
	uv run pylint axiom-*/src oltp/axiom-*/src olap/axiom-*/src
	uv run pylint axiom-*/tests oltp/axiom-*/tests olap/axiom-*/tests --disable=redefined-outer-name,too-many-public-methods

.PHONY: check-vulture
check-vulture: ## Find dead code with vulture
	uv run vulture axiom-*/src axiom-*/tests oltp/axiom-*/src oltp/axiom-*/tests olap/axiom-*/src olap/axiom-*/tests --min-confidence 80

.PHONY: check-jscpd
check-jscpd: ## Check code duplication with jscpd
	npx -y jscpd axiom-*/src axiom-*/tests oltp/axiom-*/src oltp/axiom-*/tests olap/axiom-*/src olap/axiom-*/tests

.PHONE: setup-precommit
setup-precommit: ## Install all hooks
	uv run pre-commit install

.PHONE: check-precommit
check-precommit: ## Check
	uv run pre-commit run --all-files


# Release targets
# ---------------
# Usage:
#   make release PKG=axiom-core VERSION=0.2.0
#   make release PKG=axiom-sqlalchemy VERSION=1.0.0

.PHONY: release
release: ## Tag and push a package release. Requires PKG=axiom-core (version read from pyproject.toml)
	@[ -n "$(PKG)" ] || (echo "ERROR: PKG is required. Usage: make release PKG=axiom-core" && exit 1)
	@PKG_DIR=$$(                                          \
	  if   [ -d "$(PKG)" ];          then echo "$(PKG)"; \
	  elif [ -d "oltp/$(PKG)" ];     then echo "oltp/$(PKG)"; \
	  elif [ -d "olap/$(PKG)" ];     then echo "olap/$(PKG)"; \
	  else echo ""; fi                                    \
	); \
	[ -n "$$PKG_DIR" ] || (echo "ERROR: directory not found for '$(PKG)'" && exit 1); \
	VERSION=$$(grep '^version' "$$PKG_DIR/pyproject.toml" | head -1 | sed 's/.*= *"\(.*\)"/\1/'); \
	[ -n "$$VERSION" ] || (echo "ERROR: could not read version from $$PKG_DIR/pyproject.toml" && exit 1); \
	TAG="$(PKG)-v$$VERSION"; \
	echo "Package : $(PKG)"; \
	echo "Version : $$VERSION  (from $$PKG_DIR/pyproject.toml)"; \
	echo "Tag     : $$TAG"; \
	git tag "$$TAG" && \
	git push origin "$$TAG" && \
	echo "✓ Tag $$TAG pushed — release workflow started."
