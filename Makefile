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
	uv run python scripts/check_types.py

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


# Test targets
# ------------

.PHONY: test
test: ## Run all tests with summary (per-package to avoid cross-package import conflicts)
	@total_passed=0; \
	total_failed=0; \
	total_skipped=0; \
	total_warnings=0; \
	total_errors=0; \
	total_packages=0; \
	packages_with_tests=0; \
	failed_packages=""; \
	skipped_tests_list=""; \
	for pkg in axiom-* oltp/axiom-* olap/axiom-*; do \
		[ -d "$$pkg/tests" ] || continue; \
		total_packages=$$((total_packages + 1)); \
		echo "\033[34m--- $$pkg ---\033[0m"; \
		output=$$(cd "$$pkg" && uv run pytest tests -v 2>&1); \
		rc=$$?; \
		echo "$$output" | tail -1; \
		if echo "$$output" | grep -q "collected 0 items"; then \
			echo "\033[33m  ⚠ No tests found\033[0m"; \
			total_warnings=$$((total_warnings + 1)); \
			continue; \
		fi; \
		packages_with_tests=$$((packages_with_tests + 1)); \
		passed=$$(echo "$$output" | grep -o '[0-9]* passed' | grep -o '[0-9]*' | head -1); \
		failed=$$(echo "$$output" | grep -o '[0-9]* failed' | grep -o '[0-9]*' | head -1); \
		skipped=$$(echo "$$output" | grep -o '[0-9]* skipped' | grep -o '[0-9]*' | head -1); \
		errors=$$(echo "$$output" | grep -o '[0-9]* error' | grep -o '[0-9]*' | head -1); \
		warnings=$$(echo "$$output" | grep -o '[0-9]* warning' | grep -o '[0-9]*' | head -1); \
		[ -z "$$passed" ] && passed=0; \
		[ -z "$$failed" ] && failed=0; \
		[ -z "$$skipped" ] && skipped=0; \
		[ -z "$$errors" ] && errors=0; \
		[ -z "$$warnings" ] && warnings=0; \
		total_passed=$$((total_passed + passed)); \
		total_failed=$$((total_failed + failed)); \
		total_skipped=$$((total_skipped + skipped)); \
		total_errors=$$((total_errors + errors)); \
		total_warnings=$$((total_warnings + warnings)); \
		if [ $$failed -ne 0 ] || [ $$errors -ne 0 ]; then \
			failed_packages="$$failed_packages $$pkg"; \
		fi; \
		if [ $$skipped -gt 0 ]; then \
			skipped_details=$$(echo "$$output" | grep "SKIPPED" | sed 's/^[[:space:]]*/    /'); \
			skipped_tests_list="$${skipped_tests_list}\\n  $$pkg:\\n$$skipped_details"; \
		fi; \
		[ $$rc -eq 5 ] && continue; \
		[ $$rc -ne 0 ] && total_failed=$$((total_failed + 1)); \
	done; \
	total_tests=$$((total_passed + total_failed + total_skipped)); \
	echo ""; \
	echo "\033[34m================================================================\033[0m"; \
	echo "\033[34m                        TEST SUMMARY                          \033[0m"; \
	echo "\033[34m================================================================\033[0m"; \
	echo "\033[36mPackages scanned:     $$total_packages\033[0m"; \
	echo "\033[36mPackages with tests:  $$packages_with_tests\033[0m"; \
	if [ $$total_warnings -gt 0 ]; then \
		echo "\033[33mPackages w/o tests:   $$total_warnings ⚠\033[0m"; \
	fi; \
	echo "\033[34m----------------------------------------------------------------\033[0m"; \
	echo "\033[37mTotal tests:          $$total_tests\033[0m"; \
	echo "\033[32m  ✓ Passed:           $$total_passed\033[0m"; \
	if [ $$total_failed -gt 0 ]; then \
		echo "\033[31m  ✗ Failed:           $$total_failed\033[0m"; \
	else \
		echo "\033[32m  ✗ Failed:           $$total_failed\033[0m"; \
	fi; \
	if [ $$total_skipped -gt 0 ]; then \
		echo "\033[33m  ⊘ Skipped:          $$total_skipped\033[0m"; \
	else \
		echo "\033[36m  ⊘ Skipped:          $$total_skipped\033[0m"; \
	fi; \
	if [ $$total_errors -gt 0 ]; then \
		echo "\033[31m  ⚠ Errors:           $$total_errors\033[0m"; \
	else \
		echo "\033[32m  ⚠ Errors:           $$total_errors\033[0m"; \
	fi; \
	echo "\033[34m----------------------------------------------------------------\033[0m"; \
	if [ $$total_skipped -gt 0 ]; then \
		echo "\033[33mSkipped tests details:\033[0m"; \
		printf "%b\n" "$$skipped_tests_list"; \
		echo "\033[34m----------------------------------------------------------------\033[0m"; \
	fi; \
	if [ -n "$$failed_packages" ]; then \
		echo "\033[31m✗ FAILED packages:$$failed_packages\033[0m"; \
		echo "\033[34m================================================================\033[0m"; \
		exit 1; \
	else \
		echo "\033[32m✓ ALL TESTS PASSED\033[0m"; \
		echo "\033[34m================================================================\033[0m"; \
		exit 0; \
	fi


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
