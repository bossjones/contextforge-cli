set shell := ["zsh", "-cu"]

# just manual: https://github.com/casey/just/#readme

# Ignore the .env file that is only used by the web service
set dotenv-load := false

CURRENT_DIR := "$(pwd)"

base64_cmd := if "{{os()}}" == "macos" { "base64 -w 0 -i cert.pem -o ca.pem" } else { "base64 -w 0 -i cert.pem > ca.pem" }
grep_cmd := if "{{os()}}" =~ "macos" { "ggrep" } else { "grep" }
sed_cmd := if "{{os()}}" =~ "macos" { "gsed" } else { "sed" }

# Variables
PYTHON := "uv run python"
UV_RUN := "uv run"
# GREP_LANGGRAPH_SDK := `{{grep_cmd}} -h 'langgraph-sdk>=.*",' pyproject.toml | {{sed_cmd}} 's/^[[:space:]]*"//; s/",$//'`
LANGGRAPH_REPLACEMENT := if "{{os()}}" =~ "macos" { `ggrep -h 'langgraph-sdk>=.*",' pyproject.toml | gsed 's/^[[:space:]]*"//; s/",$//'` } else { `grep -h 'langgraph-sdk>=.*",' pyproject.toml | sed 's/^[[:space:]]*"//; s/",$//'` }

# Default values for external docs generation
EXTERNAL_DOCS_PATH := "limbo/bindings/python"
EXTERNAL_DOCS_MODEL := "claude-3.5-sonnet"

# Recipes
# Install the virtual environment and install the pre-commit hooks
install:
	@echo "🚀 Creating virtual environment using uv"
	uv sync
	uv tool upgrade pyright
	uv run pre-commit install

# Run code quality tools.
check:
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	uv lock --locked
	@echo "🚀 Linting code: Running pre-commit"
	uv run pre-commit run -a
	@echo "🚀 Static type checking: Running mypy"
	uv run mypy
	@echo "🚀 Checking for obsolete dependencies: Running deptry"
	uv run deptry .

# # Test the code with pytest
# test:
# 	@echo "🚀 Testing code: Running pytest"
# 	{{UV_RUN}} pytest --diff-width=60 --diff-symbols --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# Build wheel file
build: clean-build
	@echo "🚀 Creating wheel file"
	uvx --from build pyproject-build --installer uv

# Clean build artifacts
clean-build:
	@echo "🚀 Removing build artifacts"
	{{PYTHON}} -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"

# Publish a release to PyPI.
publish:
	@echo "🚀 Publishing."
	uvx twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

# Build and publish.
build-and-publish: build publish

# Test if documentation can be built without warnings or errors
docs-test:
	uv run mkdocs build -s

# Build and serve the documentation
docs:
	uv run mkdocs serve

help:
	@just --list

default: help


# Print the current operating system
info:
		print "OS: {{os()}}"

# Display system information
system-info:
	@echo "CPU architecture: {{ arch() }}"
	@echo "Operating system type: {{ os_family() }}"
	@echo "Operating system: {{ os() }}"

# verify python is running under pyenv
which-python:
		python -c "import sys;print(sys.executable)"

# when developing, you can use this to watch for changes and restart the server
autoreload-code:
	uv run watchmedo auto-restart --pattern "*.py" --recursive --signal SIGTERM uv run goobctl go

# Open the HTML coverage report in the default
local-open-coverage:
	./scripts/open-browser.py file://${PWD}/htmlcov/index.html

# Open the HTML coverage report in the default
open-coverage: local-open-coverage

# Run unit tests and open the coverage report
local-unittest:
	bash scripts/unittest-local
	./scripts/open-browser.py file://${PWD}/htmlcov/index.html

# Run all pre-commit hooks on all files
pre-commit-run-all:
	uv run pre-commit run --all-files

# Install pre-commit hooks
pre-commit-install:
	uv run pre-commit install

# Display the dependency tree of the project
pipdep-tree:
	pipdeptree --python .venv/bin/python3

# install uv tools globally
uv-tool-install:
	uv install invoke
	uv install pipdeptree
	uv install click

# Lint GitHub Actions workflow files
lint-github-actions:
	actionlint

# check that taplo is installed to lint/format TOML
check-taplo-installed:
	@command -v taplo >/dev/null 2>&1 || { echo >&2 "taplo is required but it's not installed. run 'brew install taplo'"; exit 1; }

# Format Python files using pre-commit
fmt-python:
	git ls-files '*.py' '*.ipynb' "Dockerfile" "Dockerfile.*" | xargs uv run pre-commit run --files

# Format Markdown files using pre-commit
fmt-markdown-pre-commit:
	git ls-files '*.md' | xargs uv run pre-commit run --files

# format pyproject.toml using taplo
fmt-toml:
	uv run pre-commit run taplo-format --all-files

# SOURCE: https://github.com/PovertyAction/ipa-data-tech-handbook/blob/ed81492f3917ee8c87f5d8a60a92599a324f2ded/Justfile

# Format all markdown and config files
fmt-markdown:
	git ls-files '*.md' | xargs uv run mdformat
	uv run pre-commit run end-of-file-fixer --all-files

# Format a single markdown file, "f"
fmt-md f:
	uv run mdformat {{ f }}

# format all code using pre-commit config
fmt: fmt-python fmt-toml fmt-markdown fmt-markdown fmt-markdown-pre-commit

# lint python files using ruff
lint-python:
	pre-commit run ruff --all-files

# lint TOML files using taplo
lint-toml: check-taplo-installed
	pre-commit run taplo-lint --all-files

# lint yaml files using yamlfix
lint-yaml:
	pre-commit run yamlfix --all-files

# lint pyproject.toml and detect log_cli = true
lint-check-log-cli:
	pre-commit run detect-pytest-live-log --all-files

# Check format of all markdown files
lint-check-markdown:
	uv run mdformat --check .

# Lint all files in the current directory (and any subdirectories).
lint: lint-python lint-toml lint-check-log-cli lint-check-markdown

# generate type stubs for the project
createstubs:
	./scripts/createstubs.sh

# sweep init
sweep-init:
	uv run sweep init

# TODO: We should try out trunk
# By default, we use the following config that runs Trunk, an opinionated super-linter that installs all the common formatters and linters for your codebase. You can set up and configure Trunk for yourself by following https://docs.trunk.io/get-started.
# sandbox:
#   install:
#     - trunk init
#   check:
#     - trunk fmt {file_path}
#     - trunk check {file_path}

# Perform a dry run of dependency upgrades
upgrade-dry-run:
	uv lock --upgrade --dry-run


# sync all uv deps to editable mode
sync:
	uv sync --all-extras --dev

# Upgrade all dependencies and sync the environment
sync-upgrade-all:
	uv lock --upgrade
	uv sync --all-extras --dev


# Upgrade all dependencies and sync the environment
uv-upgrade-all:
	uv lock --upgrade

# Upgrade all dependencies and sync the environment
uv-upgrade: uv-upgrade-all

# check if uv lock is up to date
uv-lock-check:
	uv lock --check

# check if uv lock is up to date
uv-lock-check-dry-run:
	uv lock --check --dry-run

# Start a background HTTP server for test fixtures
http-server-background:
	#!/bin/bash
	# _PID=$(pgrep -f " -m http.server --bind localhost 19000 -d ./tests/fixtures")
	pkill -f " -m http.server --bind localhost 19000 -d ./tests/fixtures"
	python3 -m http.server --bind localhost 19000 -d ./tests/fixtures &
	echo $! > PATH.PID

# Start an HTTP server for test fixtures
http-server:
	#!/bin/bash
	# _PID=$(pgrep -f " -m http.server --bind localhost 19000 -d ./tests/fixtures")
	pkill -f " -m http.server --bind localhost 19000 -d ./tests/fixtures"
	python3 -m http.server --bind localhost 19000 -d ./tests/fixtures
	echo $! > PATH.PID

# Bump the version by major
major-version-bump:
	uv version
	uv version --bump major

# Bump the version by minor
minor-version-bump:
	uv version
	uv version --bump minor

# Bump the version by patch
patch-version-bump:
	uv version
	uv version --bump patch

# Bump the version by major
version-bump-major: major-version-bump

# Bump the version by minor
version-bump-minor: minor-version-bump

# Bump the version by patch
version-bump-patch: patch-version-bump

# Serve the documentation locally for preview
docs_preview:
	uv run mkdocs serve

# Build the documentation
docs_build:
	uv run mkdocs build

# Deploy the documentation to GitHub Pages
docs_deploy:
	uv run mkdocs gh-deploy --clean

# Generate a draft changelog
changelog:
	uv run towncrier build --version main --draft

# Checkout main branch and pull latest changes
gco:
	gco main
	git pull --rebase

# Show diff for LangChain migration
langchain-migrate-diff:
	langchain-cli migrate --include-ipynb --diff contextforge_cli

# Perform LangChain migration
langchain-migrate:
	langchain-cli migrate --include-ipynb contextforge_cli

# Get the ruff config
get-ruff-config:
	uv run ruff check --show-settings --config pyproject.toml -v -o ruff_config.toml >> ruff.log 2>&1

# Run lint and test
ci:
	{{UV_RUN}} pytest --diff-width=60 --diff-symbols --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# Open a manhole shell
manhole-shell:
	./scripts/manhole-shell

# Find the cassettes directories
find-cassettes-dirs:
	fd -td cassettes

# Delete the cassettes directories
delete-cassettes:
	fd -td cassettes -X rm -ri

# Install brew dependencies
brew-deps:
	brew install libmagic poppler tesseract pandoc qpdf tesseract-lang
	brew install --cask libreoffice

# install aicommits and configure it
init-aicommits:
	npm install -g aicommits
	aicommits config set OPENAI_KEY=$OCO_OPENAI_API_KEY type=conventional model=gpt-4o max-length=100
	aicommits hook install

# Run aider
aider:
	uv run aider -c .aider.conf.yml --aiderignore .aiderignore


# Run aider with O1 preview
aider-o1-preview:
	uv run aider -c .aider.conf.yml --aiderignore .aiderignore --o1-preview --architect --edit-format whole --model o1-mini --no-stream

# Run aider with Sonnet
aider-sonnet:
	uv run aider -c .aider.conf.yml --aiderignore .aiderignore --sonnet --architect --map-tokens 2048 --cache-prompts --edit-format diff

# Run aider with Sonnet in browser
aider-sonnet-browser:
	uv run aider -c .aider.conf.yml --aiderignore .aiderignore --sonnet --architect --map-tokens 2048 --cache-prompts --edit-format diff --browser

# Run aider with Gemini
aider-gemini:
	uv run aider -c .aider.conf.yml --aiderignore .aiderignore --model gemini/gemini-exp-1206 --cache-prompts --edit-format whole

# Run aider with Claude
aider-claude:
	uv run aider -c .aider.conf.yml --aiderignore .aiderignore --model 'anthropic/claude-3-5-sonnet-20241022'


# SOURCE: https://github.com/RobertCraigie/prisma-client-py/blob/da53c4280756f1a9bddc3407aa3b5f296aa8cc10/Makefile#L77
# Remove all generated files and caches
clean:
	#!/bin/bash
	rm -rf .cache
	rm -rf `find . -name __pycache__`
	rm -rf .tests_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf dist
	rm -f coverage.xml

# Create a token for authentication
uv_create_token:
	{{PYTHON}} -c "from contextforge_cli.cli import create_token; create_token()"

# Show current database state
uv_db_current:
	{{PYTHON}} -c "from contextforge_cli.cli import db_current; db_current()"

# Upgrade database to latest version
uv_db_upgrade:
	{{PYTHON}} -c "from contextforge_cli.cli import db_upgrade; db_upgrade()"

# Downgrade database to previous version
uv_db_downgrade:
	{{PYTHON}} -c "from contextforge_cli.cli import db_downgrade; db_downgrade()"

# Export a collection of data
uv_export_collection:
	{{PYTHON}} -c "from contextforge_cli.cli import export_collection; export_collection()"

# Import a collection of data
uv_import_collection:
	{{PYTHON}} -c "from contextforge_cli.cli import import_collection; import_collection()"

# Import a single file
uv_import_file:
	{{PYTHON}} -c "from contextforge_cli.cli import import_file; import_file()"

# Lint markdown files
uv_lint_markdown:
	{{UV_RUN}} pymarkdownlnt --disable-rules=MD013,MD034 scan README.md

# Serve documentation locally
uv_serve_docs:
	{{UV_RUN}} mkdocs serve

# Convert pylint configuration to ruff
uv_pylint_to_ruff:
	{{UV_RUN}} pylint-to-ruff

# Start a simple HTTP server
uv_http:
	{{UV_RUN}} -m http.server 8008

# Display current user
uv_whoami:
	whoami

# Install missing mypy type stubs
uv_mypy_missing:
	{{UV_RUN}} mypy --install-types

# Run pre-commit hooks on all files
uv_fmt:
	{{UV_RUN}} pre-commit run --all-files

# Run pylint checks
uv_pylint:
	{{PYTHON}} -m invoke ci.pylint --everything

# Run pylint with error-only configuration
uv_pylint_error_only:
	{{UV_RUN}} pylint --output-format=colorized --disable=all --max-line-length=120 --enable=F,E --rcfile pyproject.toml contextforge_cli tests

# Run pylint on all files
uv_lint_all:
	{{PYTHON}} -m pylint -j4 --output-format=colorized --rcfile pyproject.toml tests contextforge_cli

# Run ruff linter
uv_lint:
	{{PYTHON}} -m ruff check --fix . --config=pyproject.toml

# Run all typecheck tasks
uv_typecheck:
	just uv_typecheck_pyright
	just uv_typecheck_mypy

# Run Pyright type checker
uv_typecheck_pyright:
	rm pyright.log || true
	touch pyright.log
	{{UV_RUN}} pyright --threads {{num_cpus()}} -p pyproject.toml src tests | tee -a pyright.log
	cat pyright.log

typecheck-pydantic:
	#!/bin/bash
	grep -rl --exclude="*.pyc" --exclude="*requirements.txt" -e "pydantic" -e "pydantic_settings" src tests | {{UV_RUN}} pyright --verbose --threads {{num_cpus()}} -p pyproject.toml -

# Verify types using Pyright, ignoring external packages
typecheck: uv_typecheck_pyright

# Verify types using Pyright, ignoring external packages
uv_typecheck_verify_types:
	{{UV_RUN}} pyright --verifytypes src --ignoreexternal --verbose

# Run MyPy type checker and open coverage report
uv_typecheck_mypy:
	just uv_ci_mypy
	just uv_open_mypy_coverage

# Generate changelog draft
uv_docs_changelog:
	{{UV_RUN}} towncrier build --version main --draft

# Run MyPy with various report formats
uv_ci_mypy:
	{{UV_RUN}} mypy --config-file=pyproject.toml --html-report typingcov --cobertura-xml-report typingcov_cobertura --xml-report typingcov_xml --txt-report typingcov_txt .

# Open MyPy coverage report
uv_open_mypy_coverage:
	open typingcov/index.html

# Open Zipkin UI
uv_open_zipkin:
	open http://127.0.0.1:9411

# Open OpenTelemetry endpoint
uv_open_otel:
	open http://127.0.0.1:4317

# Open test coverage report
uv_open_coverage:
	just local-open-coverage

# Open pgAdmin
uv_open_pgadmin:
	open http://127.0.0.1:4000

# Open Prometheus UI
uv_open_prometheus:
	open http://127.0.0.1:9999

# Open Grafana UI
uv_open_grafana:
	open http://127.0.0.1:3333

# Open Chroma UI
uv_open_chroma:
	open http://127.0.0.1:9010

# Open ChromaDB Admin UI
uv_open_chromadb_admin:
	open http://127.0.0.1:4001

# Open all UIs and reports
uv_open_all:
	just uv_open_mypy_coverage
	just uv_open_chroma
	just uv_open_zipkin
	just uv_open_otel
	just uv_open_pgadmin
	just uv_open_prometheus
	just uv_open_grafana
	just uv_open_chromadb_admin
	just uv_open_coverage


# Run simple unit tests with coverage
uv_unittests_simple:
	{{UV_RUN}} pytest --diff-width=60 --diff-symbols --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# Run unit tests in debug mode with extended output
uv_unittests_debug:
	{{UV_RUN}} pytest -s -vv --diff-width=60 --diff-symbols --pdb --pdbcls bpdb:BPdb --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# Run service-related unit tests in debug mode
uv_unittests_debug_services:
	{{UV_RUN}} pytest -m services -s -vv --diff-width=60 --diff-symbols --pdb --pdbcls bpdb:BPdb --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# Run asynciotyper-related unit tests in debug mode
uv_unittests_debug_asynciotyper:
	{{UV_RUN}} pytest -s -vv --diff-width=60 --diff-symbols --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=. -m asynciotyper

# Run pgvector-related unit tests in debug mode
uv_unittests_debug_pgvector:
	{{UV_RUN}} pytest -m pgvectoronly -s -vv --diff-width=60 --diff-symbols --pdb --pdbcls bpdb:BPdb --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# Profile unit tests in debug mode using pyinstrument
uv_profile_unittests_debug:
	{{UV_RUN}} pyinstrument -m pytest -s -vv --diff-width=60 --diff-symbols --pdb --pdbcls bpdb:BPdb --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# Profile unit tests in debug mode using py-spy
uv_spy_unittests_debug:
	{{UV_RUN}} py-spy top -- python -m pytest -s -vv --diff-width=60 --diff-symbols --pdb --pdbcls bpdb:BPdb --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# Run standard unit tests with coverage
uv_unittests:
	{{UV_RUN}} pytest --verbose --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# Run unit tests with VCR in record mode
uv_unittests_vcr_record:
	{{UV_RUN}} pytest --record-mode=all --verbose --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# Run unit tests with VCR in rewrite mode
uv_unittests_vcr_record_rewrite:
	{{UV_RUN}} pytest --record-mode=rewrite --verbose --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# Run unit tests with VCR in once mode
uv_unittests_vcr_record_once:
	{{UV_RUN}} pytest --record-mode=once --verbose --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.

# Run all VCR recording tests
uv_unittests_vcr_record_all: uv_unittests_vcr_record

# Run final VCR recording tests (NOTE: this is the only one that works)
uv_unittests_vcr_record_final: uv_unittests_vcr_record

# Run simple tests without warnings
uv_test_simple:
	{{UV_RUN}} pytest -p no:warnings

# Alias for simple tests without warnings
uv_simple_test:
	{{UV_RUN}} pytest -p no:warnings

# Run unit tests in debug mode with extended output
uv_new_unittests_debug:
	{{UV_RUN}} pytest -s --verbose --pdb --pdbcls bpdb:BPdb --showlocals --tb=short

# Run linting and unit tests
uv_test:
	just uv_lint
	just uv_unittests

# Combine coverage data
uv_coverage_combine:
	{{UV_RUN}} python -m coverage combine

# Generate HTML coverage report
uv_coverage_html:
	{{UV_RUN}} python -m coverage html --skip-covered --skip-empty

# Run pytest with coverage
uv_coverage_pytest:
	{{UV_RUN}} coverage run --rcfile=pyproject.toml -m pytest tests

# Run pytest with coverage in debug mode
uv_coverage_pytest_debug:
	{{UV_RUN}} coverage run --rcfile=pyproject.toml -m pytest --verbose -vvv --pdb --pdbcls bpdb:BPdb --showlocals --tb=short --capture=no tests

# Run pytest with coverage for evals in debug mode
uv_coverage_pytest_evals_debug:
	{{UV_RUN}} coverage run --rcfile=pyproject.toml -m pytest --verbose -vv --pdb --pdbcls bpdb:BPdb --showlocals --tb=short --capture=no -m evals --slow tests

# Run pytest with coverage and memray in debug mode
uv_memray_coverage_pytest_debug:
	{{UV_RUN}} coverage run --rcfile=pyproject.toml -m pytest --verbose -vvv --memray --pdb --pdbcls bpdb:BPdb --showlocals --tb=short --capture=no tests

# Run pytest with coverage and memray for evals in debug mode
uv_memray_coverage_pytest_evals_debug:
	{{UV_RUN}} coverage run --rcfile=pyproject.toml -m pytest --verbose --memray -vv --pdb --pdbcls bpdb:BPdb --showlocals --tb=short --capture=no -m evals --slow tests

# Generate and view coverage report
uv_coverage_report:
	just uv_coverage_pytest
	just uv_coverage_combine
	just uv_coverage_show
	just uv_coverage_html
	just uv_coverage_open

# Generate and view coverage report in debug mode
uv_coverage_report_debug:
	just uv_coverage_pytest_debug
	just uv_coverage_combine
	just uv_coverage_show
	just uv_coverage_html
	just uv_coverage_open

# Generate and view coverage report for evals in debug mode
uv_coverage_report_debug_evals:
	just uv_coverage_pytest_debug
	just uv_coverage_pytest_evals_debug
	just uv_coverage_combine
	just uv_coverage_show
	just uv_coverage_html
	just uv_coverage_open

# Run end-to-end tests with coverage in debug mode
uv_e2e_coverage_pytest_debug:
	{{UV_RUN}} coverage run --rcfile=pyproject.toml -m pytest --verbose --pdb --pdbcls bpdb:BPdb --showlocals --tb=short --capture=no tests -m e2e

# Generate and view end-to-end coverage report in debug mode
uv_e2e_coverage_report_debug:
	just uv_e2e_coverage_pytest_debug
	just uv_coverage_combine
	just uv_coverage_show
	just uv_coverage_html
	just uv_coverage_open

# Show coverage report
uv_coverage_show:
	{{UV_RUN}} python -m coverage report --fail-under=5

# Open coverage report
uv_coverage_open:
	just local-open-coverage

# Run linting and tests (CI)
uv_ci:
	just uv_lint
	just uv_test

# Run debug unit tests and open coverage report (CI debug)
uv_ci_debug:
	just uv_unittests_debug
	just uv_coverage_open

# Run simple unit tests and open coverage report (CI simple)
uv_ci_simple:
	just uv_unittests_simple
	just uv_coverage_open

# Run CI with evals
uv_ci_with_evals:
	just uv_coverage_pytest_debug
	just uv_coverage_pytest_evals_debug
	just uv_coverage_combine
	just uv_coverage_show
	just uv_coverage_html
	just uv_coverage_open

# Run CI with evals and memray
uv_ci_with_evals_memray:
	just uv_memray_coverage_pytest_debug
	just uv_memray_coverage_pytest_evals_debug
	just uv_coverage_combine
	just uv_coverage_show
	just uv_coverage_html
	just uv_coverage_open

# Deploy documentation to GitHub Pages
uv_gh_deploy:
	{{UV_RUN}} mkdocs gh-deploy --force --message '[skip ci] Docs updates'

# Create site directory
uv_mkdir_site:
	mkdir site

# Deploy documentation
uv_deploy_docs:
	just uv_mkdir_site
	just uv_gh_deploy

# Add bespoke adobe concepts to cursor context
add-cursor-context:
	mkdir -p contextforge_cli/vendored || true
	gh repo clone universityofprofessorex/cerebro-bot contextforge_cli/vendored/cerebro-bot || true && cd contextforge_cli/vendored/cerebro-bot && git checkout feature-discord-utils && cd ../../..
	gh repo clone bossjones/sandbox_agent contextforge_cli/vendored/sandbox_agent || true
	gh repo clone langchain-ai/retrieval-agent-template contextforge_cli/vendored/retrieval-agent-template || true
	gh repo clone langchain-ai/rag-research-agent-template contextforge_cli/vendored/rag-research-agent-template || true
	gh repo clone langchain-ai/memory-template contextforge_cli/vendored/memory-template || true
	gh repo clone langchain-ai/react-agent contextforge_cli/vendored/react-agent || true
	gh repo clone langchain-ai/chat-langchain contextforge_cli/vendored/chat-langchain || true
	gh repo clone bossjones/goob_ai contextforge_cli/vendored/goob_ai || true
	gh repo clone langchain-ai/langchain contextforge_cli/vendored/langchain || true
	gh repo clone langchain-ai/langgraph contextforge_cli/vendored/langgraph || true
	gh repo clone CraftSpider/dpytest contextforge_cli/vendored/dpytest || true

	rm -rf contextforge_cli/vendored/cerebro-bot/.git
	rm -rf contextforge_cli/vendored/sandbox_agent/.git
	rm -rf contextforge_cli/vendored/retrieval-agent-template/.git
	rm -rf contextforge_cli/vendored/rag-research-agent-template/.git
	rm -rf contextforge_cli/vendored/memory-template/.git
	rm -rf contextforge_cli/vendored/react-agent/.git
	rm -rf contextforge_cli/vendored/chat-langchain/.git
	rm -rf contextforge_cli/vendored/goob_ai/.git
	rm -rf contextforge_cli/vendored/langchain/.git
	rm -rf contextforge_cli/vendored/langgraph/.git
	rm -rf contextforge_cli/vendored/langchain-academy/.git
	rm -rf contextforge_cli/vendored/dpytest/.git

# List outdated packages
outdated:
	{{UV_RUN}} pip list --outdated

# Install llm cli plugins
install-llm-cli-plugins:
	uv add llm
	uv add llm-cmd llm-clip llm-sentence-transformers llm-replicate llm-perplexity llm-claude-3 llm-python llm-gemini llm-jq

# Smoke test the react agent
smoke-test:
	cd contextforge_cli/agentic/studio/react && {{UV_RUN}} python -m memory_agent

# Commitizen commands
# commit using commitizen
commit:
	{{UV_RUN}} cz commit

commit-help:
	{{UV_RUN}} cz commit -h

# bump version using commitizen
bump:
	{{UV_RUN}} cz bump

# tag using commitizen
tag:
	{{UV_RUN}} cz tag

# release using commitizen
release:
	{{UV_RUN}} cz release

# bump patch version using commitizen
bump-patch:
	{{UV_RUN}} cz bump --patch

# bump minor version using commitizen
bump-minor:
	{{UV_RUN}} cz bump --minor

# bump major version using commitizen
bump-major:
	{{UV_RUN}} cz bump --major

# bump prerelease version using commitizen
bump-prerelease:
	{{UV_RUN}} cz bump --prerelease

# bump postrelease version using commitizen
bump-postrelease:
	{{UV_RUN}} cz bump --postrelease

# Generate AI commit messages
ai-commit:
	aicommits --generate 3 --type conventional

# Run the bot
run:
	{{UV_RUN}} democracyctl run-bot


# Test the code with pytest
test:
	@echo "🚀 Testing code: Running pytest"
	{{UV_RUN}} pytest --diff-width=60 --diff-symbols --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=.


# Test the code with pytest in debug mode
test-debug: uv_new_unittests_debug open-coverage

# Getting corefiles
corefiles:
	{{UV_RUN}} files-to-prompt -e rs -e py -e toml --ignore "node_modules|__pycache__|scripts|debug|.o|deps|release|target|inputs" . | pbcopy

# Install youtube-transcript
install-youtube-transcript:
	cargo install youtube-transcript

# Run linting
test-lint:
	uv run pylint --output-format=colorized --disable=all --max-line-length=120 --enable=F,E --rcfile pyproject.toml contextforge_cli tests

# Run linting for duplicate code
test-lint-similarities:
	uv run pylint --disable=all --enable=duplicate-code --output-format=colorized --max-line-length=120 --rcfile pyproject.toml contextforge_cli tests

# Verify types with pyright
pyright-verify-types:
	#!/usr/bin/env bash
	# Get the list of installed packages
	packages=$(uv run pip freeze | cut -d '=' -f 1)

	rm -f pyright-verify-types.log
	touch pyright-verify-types.log

	# Iterate through each package
	for package in $packages; do
			echo "Checking package: $package"
			echo "----------------------------------------"

			# Run pyright and print the output
			# uv run pyright --verifytypes "$package" --verbose
			uv run pyright --verifytypes "$package" | tee -a pyright-verify-types.log

			echo "----------------------------------------"
	done

	echo "Verification complete."

# Create stubs for missing packages
pyright-createstubs-missing:
	./scripts/pyright_createstub_missing.sh

# Generate AI documentation from source files
generate-ai-docs:
	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/koalabot_advanced.xml"
	uv run files-to-prompt /Users/malcolm/dev/KoalaBot/tests/cogs \
	/Users/malcolm/dev/KoalaBot/tests/conftest.py \
	/Users/malcolm/dev/KoalaBot/tests/test_koalabot.py \
	/Users/malcolm/dev/KoalaBot/tests/test_utils.py \
	/Users/malcolm/dev/KoalaBot/tests/tests_utils \
	/Users/malcolm/dev/KoalaBot/tests/cogs/text_filter \
	/Users/malcolm/dev/KoalaBot/koala/cogs/text_filter \
	/Users/malcolm/dev/KoalaBot/koalabot.py \
	/Users/malcolm/dev/KoalaBot/koala/utils.py \
	--cxml -o ~/dev/bossjones/contextforge-cli/ai_docs/koalabot_advanced.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/koalabot_cog_testing.xml"
	uv run files-to-prompt \
	/Users/malcolm/dev/KoalaBot/tests/conftest.py \
	/Users/malcolm/dev/KoalaBot/koala/cogs/text_filter \
	/Users/malcolm/dev/KoalaBot/tests/tests_utils \
	/Users/malcolm/dev/KoalaBot/tests/cogs/text_filter \
	/Users/malcolm/dev/KoalaBot/koalabot.py \
	--cxml -o ~/dev/bossjones/contextforge-cli/ai_docs/koalabot_cog_testing.xml


	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/movienightbot.xml"
	uv run files-to-prompt /Users/malcolm/dev/MovieNightBot/tests/conftest.py \
	/Users/malcolm/dev/MovieNightBot/tests/utils.py \
	/Users/malcolm/dev/MovieNightBot/tests/actions \
	/Users/malcolm/dev/MovieNightBot/movienightbot/application.py \
	/Users/malcolm/dev/MovieNightBot/movienightbot/util.py \
	/Users/malcolm/dev/MovieNightBot/movienightbot/commands \
	--cxml -o ~/dev/bossjones/contextforge-cli/ai_docs/movienightbot.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/dptest.xml"
	uv run files-to-prompt /Users/malcolm/Documents/ai_docs/rtdocs/dpytest.readthedocs.io/en/latest \
	--cxml -o ~/dev/bossjones/contextforge-cli/ai_docs/dptest.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/pytest_aiohttp_testing.xml"
	uv run files-to-prompt /Users/malcolm/Documents/ai_docs/rtdocs/docs.aiohttp.org/en/stable/testing.html \
	--cxml -o ~/dev/bossjones/contextforge-cli/ai_docs/pytest_aiohttp_testing.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/sandbox_agent_testing.xml"
	uv run files-to-prompt /Users/malcolm/dev/bossjones/sandbox_agent/tests/test_bot.py \
	/Users/malcolm/dev/bossjones/sandbox_agent/tests/conftest.py \
	/Users/malcolm/dev/bossjones/sandbox_agent/src/sandbox_agent/bot.py \
	/Users/malcolm/dev/bossjones/sandbox_agent/src/sandbox_agent/cogs \
	--cxml -o ~/dev/bossjones/contextforge-cli/ai_docs/sandbox_agent_testing.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/dpytest_minimal_test_examples.xml"
	uv run files-to-prompt \
	/Users/malcolm/dev/dpytest/tests/test_edit.py \
	/Users/malcolm/dev/dpytest/tests/test_fetch_message.py \
	/Users/malcolm/dev/dpytest/tests/test_configure.py \
	/Users/malcolm/dev/dpytest/tests/test_send.py \
	/Users/malcolm/dev/dpytest/tests/test_verify_embed.py \
	/Users/malcolm/dev/dpytest/tests/test_verify_file.py \
	/Users/malcolm/dev/dpytest/tests/test_verify_message.py \
	/Users/malcolm/dev/dpytest/tests/test_activity.py \
	--cxml -o ~/dev/bossjones/contextforge-cli/ai_docs/dpytest_minimal_test_examples.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/vcrpy_docs.xml"
	uv run files-to-prompt \
	/Users/malcolm/Documents/ai_docs/rtdocs/vcrpy.readthedocs.io/en/latest/configuration.html \
	/Users/malcolm/Documents/ai_docs/rtdocs/vcrpy.readthedocs.io/en/latest/api.html \
	/Users/malcolm/Documents/ai_docs/rtdocs/vcrpy.readthedocs.io/en/latest/advanced.html \
	/Users/malcolm/Documents/ai_docs/rtdocs/vcrpy.readthedocs.io/en/latest/debugging.html \
	--cxml -o ~/dev/bossjones/contextforge-cli/ai_docs/vcrpy_docs.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/gallery_dl_tests.xml"
	uv run files-to-prompt \
	/Users/malcolm/dev/gallery-dl/test/__init__.py \
	/Users/malcolm/dev/gallery-dl/test/test_cache.py \
	/Users/malcolm/dev/gallery-dl/test/test_config.py \
	/Users/malcolm/dev/gallery-dl/test/test_cookies.py \
	/Users/malcolm/dev/gallery-dl/test/test_downloader.py \
	/Users/malcolm/dev/gallery-dl/test/test_extractor.py \
	/Users/malcolm/dev/gallery-dl/test/test_formatter.py \
	/Users/malcolm/dev/gallery-dl/test/test_job.py \
	/Users/malcolm/dev/gallery-dl/test/test_oauth.py \
	/Users/malcolm/dev/gallery-dl/test/test_output.py \
	/Users/malcolm/dev/gallery-dl/test/test_postprocessor.py \
	/Users/malcolm/dev/gallery-dl/test/test_results.py \
	/Users/malcolm/dev/gallery-dl/test/test_text.py \
	/Users/malcolm/dev/gallery-dl/test/test_util.py \
	/Users/malcolm/dev/gallery-dl/test/test_ytdl.py \
	--cxml -o ~/dev/bossjones/contextforge-cli/ai_docs/gallery_dl_tests.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/cerebro.xml"
	uv run files-to-prompt /Users/malcolm/dev/universityofprofessorex/cerebro-bot/cerebro_bot/cogs/autoresize.py --cxml -o ~/dev/bossjones/contextforge-cli/ai_docs/cerebro_bot/autoresize_cog.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/contextforge_cli_logsetup.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/bossjones/contextforge-cli/tests/test_logsetup.py \
			/Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/bot_logger/logsetup.py \
			--cxml -o ai_docs/prompts/contextforge_cli_logsetup.xml


	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/structlog_test_examples.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/bot_logger/logsetup.py \
			/Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/bot_logger/logsetup.py \
			--cxml -o ai_docs/prompts/structlog_test_examples.xml


	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/dpytest_docs_test_and_code.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/dpytest/discord \
			/Users/malcolm/dev/dpytest/tests \
			/Users/malcolm/dev/dpytest/docs \
			--cxml -o ai_docs/prompts/dpytest_docs_test_and_code.xml

	# KoalaBot documentation
	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/KoalaBot_docs_test_and_code.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/KoalaBot/koalabot.py \
			/Users/malcolm/dev/KoalaBot/tests \
			/Users/malcolm/dev/KoalaBot/koala \
			--cxml -o ai_docs/prompts/data/KoalaBot_docs_test_and_code.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/ClassMateBot_docs_test_and_code.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/ClassMateBot/conftest.py \
			/Users/malcolm/dev/ClassMateBot/bot.py \
			/Users/malcolm/dev/ClassMateBot/test \
			/Users/malcolm/dev/ClassMateBot/cogs \
			--cxml -o ai_docs/prompts/data/ClassMateBot_docs_test_and_code.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/TeachersPetBot_docs_test_and_code.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/TeachersPetBot/src \
			/Users/malcolm/dev/TeachersPetBot/test \
			/Users/malcolm/dev/TeachersPetBot/bot.py \
			/Users/malcolm/dev/TeachersPetBot/BotBackup.py \
			/Users/malcolm/dev/TeachersPetBot/conftest.py \
			/Users/malcolm/dev/TeachersPetBot/cogs \
			/Users/malcolm/dev/TeachersPetBot/configs \
			/Users/malcolm/dev/TeachersPetBot/__init__.py \
			/Users/malcolm/dev/TeachersPetBot/initialize_db_script.py \
			--cxml -o ai_docs/prompts/data/TeachersPetBot_docs_test_and_code.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/contextforge_cli_with_segfault.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/bossjones/contextforge-cli \
			--cxml -o ai_docs/prompts/data/contextforge_cli_with_segfault.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/cpython_test_asyncio.xml"

	uv run files-to-prompt \
			/Users/malcolm/dev/cpython/Lib/test/test_asyncio \
			--cxml -o ai_docs/prompts/data/cpython_test_asyncio.xml


	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/vcrpy_docs_test_and_code.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/vcrpy/vcr \
			/Users/malcolm/dev/vcrpy/tests \
			/Users/malcolm/dev/vcrpy/docs \
			--cxml -o ai_docs/prompts/data/vcrpy_docs_test_and_code.xml


	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/pytest_recording_docs_test_and_code.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/pytest-recording/src \
			/Users/malcolm/dev/pytest-recording/tests \
			/Users/malcolm/dev/pytest-recording/docs \
			--cxml -o ai_docs/prompts/data/pytest_recording_docs_test_and_code.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/langgraph_docs_test_and_code.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/langchain-ai/langgraph/libs/langgraph/langgraph \
			/Users/malcolm/dev/langchain-ai/langgraph/libs/langgraph/tests \
			--cxml -o ai_docs/prompts/data/langgraph_docs_test_and_code.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/langgraph_sdk_docs_test_and_code.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/langchain-ai/langgraph/libs/sdk-py/langgraph_sdk \
			--cxml -o ai_docs/prompts/data/langgraph_sdk_docs_test_and_code.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/langsmith_sdk_code.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/langchain-ai/langsmith-sdk/python/langsmith \
			--cxml -o ai_docs/prompts/data/langsmith_sdk_code.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/langgraph_cli_code.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/langchain-ai/langgraph/libs/cli/tests \
			/Users/malcolm/dev/langchain-ai/langgraph/libs/cli/langgraph_cli \
			--cxml -o ai_docs/prompts/data/langgraph_cli_code.xml


	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/home_assistant_code.xml"
	uv run files-to-prompt  /Users/malcolm/dev/home-assistant/core/homeassistant/core.py \
		/Users/malcolm/dev/home-assistant/core/homeassistant/block_async_io.py \
		/Users/malcolm/dev/home-assistant/core/homeassistant/util/async_.py \
		/Users/malcolm/dev/home-assistant/core/homeassistant/util/logging.py \
		/Users/malcolm/dev/home-assistant/core/homeassistant/util/loop.py \
		--cxml -o ai_docs/prompts/data/home_assistant_code.xml


	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/home_assistant_bootstrap_and_thread.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/home-assistant/core/homeassistant/__main__.py \
			/Users/malcolm/dev/home-assistant/core/homeassistant/bootstrap.py \
			/Users/malcolm/dev/home-assistant/core/homeassistant/util/thread.py \
			/Users/malcolm/dev/home-assistant/core/homeassistant/util/timeout.py \
			/Users/malcolm/dev/home-assistant/core/homeassistant/util/executor.py \
			--cxml -o ai_docs/prompts/data/home_assistant_bootstrap_and_thread.xml

	@echo "🔥🔥 Rendering: ~/dev/bossjones/contextforge-cli/ai_docs/home_assistant_profiler.xml"
	uv run files-to-prompt \
			/Users/malcolm/dev/home-assistant/core/homeassistant/components/profiler \
			--cxml -o ai_docs/prompts/data/home_assistant_profiler.xml

	@echo "🔥🔥 Rendering: contextforge_cli main branch with tests"
	uv run files-to-prompt /Users/malcolm/dev/bossjones/contextforge-cli-main/contextforge_cli /Users/malcolm/dev/bossjones/contextforge-cli-main/tests --cxml -o ai_docs/prompts/data/contextforge_cli_main_branch_with_tests.xml

	@echo "AI documentation generation complete"

# Regenerate contextforge-cli ai docs
regenerate-contextforge-cli-ai-docs:
	uv run files-to-prompt /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/exceptions /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/exceptions/__init__.py /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/factories /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/models /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/services /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/shell /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/subcommands /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/utils --cxml -o ai_docs/prompts/data/contextforge_cli_exceptions.xml

	uv run files-to-prompt /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/__init__.py /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/__main__.py /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/__version__.py /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/aio_settings.py /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/asynctyper.py /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/base.py /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/cli.py /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/constants.py /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/debugger.py /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/foo.py /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/llm_manager.py /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/main.py /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/requirements.txt /Users/malcolm/dev/bossjones/contextforge-cli/contextforge_cli/types.py --cxml -o ai_docs/prompts/data/contextforge_cli_init.xml



# Run unit tests in debug mode with extended output
test-twitter-cog-debug:
	uv run pytest -s --verbose --showlocals --tb=short --disable-warnings --pdb --pdbcls bpdb:BPdb --showlocals tests/cogs/test_twitter_cog.py
# {{UV_RUN}} pytest --capture=tee-sys -vvvv --pdb --pdbcls bpdb:BPdb --showlocals --full-trace -k  test_download_tweet_success_twitter_cog
# {{UV_RUN}} pytest -s --verbose  --showlocals --tb=short -k  test_download_tweet_success_twitter_cog
# {{UV_RUN}} pytest -k  test_download_tweet_success_twitter_cog

# Run unit tests specifically for twitter cog
test-twitter-cog:
	uv run pytest -s --verbose --showlocals --tb=short --disable-warnings tests/cogs/test_twitter_cog.py
# {{UV_RUN}} pytest --capture=tee-sys -k  test_download_tweet_success_twitter_cog

# In order to properly create new cassette files, you must first delete the existing cassette files and directories. This will regenerate all cassette files and rerun tests.

# Delete existing cassettes
delete-existing-cassettes:
	./scripts/delete-existing-cassettes.sh

# delete all cassette files and directories, regenerate all cassette files and rerun tests
local-regenerate-cassettes:
	@echo -e "\nDelete all cassette files and directories\n"
	just delete-existing-cassettes
	@echo -e "\nRegenerate all cassette files using --record-mode=all\n"
	@echo -e "\nNOTE: This is expected to FAIL the first time when it is recording the cassette files!\n"
	just uv_unittests_vcr_record_final || true
	@echo -e "\nrun regulate tests to verify that the cassettes are working\n"
	just test-debug

# (alias) delete all cassette files and directories, regenerate all cassette files and rerun tests
local-regenerate-vcr: local-regenerate-cassettes

# Regenerate all cassette files and rerun tests
regenerate-cassettes: local-regenerate-cassettes

# Run unit tests in debug mode with extended output
test-gallery-dl-debug:
	uv run pytest --capture=tee-sys --pdb --pdbcls bpdb:BPdb --showlocals --tb=short -k test_run_single_tweet

# Run unit tests specifically for gallery-dl
test-gallery-dl:
	uv run pytest --capture=tee-sys -k test_run_single_tweet

# Run unit tests specifically for dropbox
generate-cassettes-dropboxonly:
	{{UV_RUN}} pytest --record-mode=once --verbose --showlocals --tb=short --cov-append --cov-report=term-missing --junitxml=junit/test-results.xml --cov-report=xml:cov.xml --cov-report=html:htmlcov --cov-report=annotate:cov_annotate --cov=. -m dropboxonly

# Run unit tests specifically for dropbox
test-dropbox:
	uv run pytest --showlocals --tb=short --capture=tee-sys -m dropboxonly

# Run unit tests specifically for dropbox in debug mode
test-dropbox-debug:
	uv run pytest --showlocals --tb=short --capture=tee-sys --pdb --pdbcls bpdb:BPdb -m dropboxonly

# Run unit tests in debug mode with extended output
test-autocrop-cog-debug:
	{{UV_RUN}} pytest --capture=tee-sys -vvvv --pdb --pdbcls bpdb:BPdb --showlocals --full-trace tests/unittests/chatbot/cogs/test_autocrop.py

# Run unit tests in debug mode with extended output
test-toolsonly-cog-debug:
	{{UV_RUN}} pytest --capture=tee-sys -vvvv --pdb --pdbcls bpdb:BPdb --showlocals tests/unittests/chatbot/cogs/ tests/unittests/agentic/tools/

# Run unit tests specifically for tools
test-toolsonly-cog:
	uv run pytest --showlocals --tb=short --capture=tee-sys tests/unittests/chatbot/cogs/ tests/unittests/agentic/tools/

# Run unit tests in debug mode with extended output
test-logsetup-debug:
	uv run pytest -s --verbose --showlocals --tb=short -p no:warnings --pdb --pdbcls bpdb:BPdb tests/test_logsetup.py

# Run unit tests specifically for tools
test-logsetup:
	uv run pytest -s --verbose --showlocals --tb=short -p no:warnings tests/test_logsetup.py

# Results (0.97s):
#       11 passed
#        8 failed
#          - tests/test_logsetup.py:476 test_module_name_processor
#          - tests/test_logsetup.py:528 test_timestamp_formatting
#          - tests/test_logsetup.py:569 test_error_formatting
#          - tests/test_logsetup.py:654 test_processor_chain_ordering
#          - tests/cogs/test_twitter_cog.py:396 test_twitter_cog_on_ready
#          - tests/cogs/test_twitter_cog.py:414 test_twitter_cog_on_guild_join
#          - tests/cogs/test_twitter_cog.py:444 test_tweet_help_command
#          - tests/cogs/test_twitter_cog.py:657 test_cleanup_temp_dir
#        4 skipped
# error: Recipe `test-logsetup-and-bot` failed on line 1170 with exit code 1

# run structlog tests and bot tests
test-oneonly:
	uv run pytest -s -vvvv --showlocals --tb=short --disable-warnings tests/unittests/agentic/test_utils.py

test-logsetup-oneonly:
	uv run pytest -s -vvvv --showlocals --tb=short --disable-warnings tests/test_logsetup.py tests/cogs/test_twitter_cog.py -k  test_twitter_cog_on_guild_join

# run structlog tests and bot tests
test-logsetup-and-bot:
	uv run pytest -s --verbose --showlocals --tb=short --disable-warnings tests/test_logsetup.py tests/cogs/test_twitter_cog.py

# run structlog tests in debug mode
test-logsetup-and-bot-debug:
	uv run pytest -s -vvvv --showlocals --tb=short --disable-warnings --pdb --pdbcls bpdb:BPdb tests/test_logsetup.py tests/cogs/test_twitter_cog.py

# DISABLED: uv run pytest --capture=tee-sys tests/unittests/utils/test_utils_dropbox_.py
# use this with aider to fix tests incrementally

# Run unit tests specifically for utils
test-fix:
	uv run pytest -q -s tests/unittests/utils/test_utils_dropbox_.py

test-aio-settings:
	uv run pytest -s --verbose --showlocals --tb=short tests/test_aio_settings.py

test-aio-settings-debug:
	uv run pytest -s --verbose --showlocals --tb=short --pdb --pdbcls bpdb:BPdb tests/test_aio_settings.py

# Generate langgraph dockerfile for studio
generate-langgraph-dockerfile-studio:
	#!/bin/bash
	cd cookbook/studio && langgraph dockerfile -c langgraph.json Dockerfile

# Generate langgraph dockerfile
generate-langgraph-dockerfile:
	uv export --no-hashes --format requirements-txt -o contextforge_cli/requirements.txt
	gsed -i "s/langgraph-sdk==0.1.46/{{LANGGRAPH_REPLACEMENT}}/g" contextforge_cli/requirements.txt
	langgraph dockerfile -c langgraph.json Dockerfile
	cat Dockerfile

# Build docker image for debugging
docker-build-debug:
	docker build -f Dockerfile.debugging -t contextforge-cli-debugging .

# Run docker image for debugging
docker-run-debug:
	docker run -it contextforge-cli-debugging

# Update requirements.txt from pyproject.toml using yq
update-requirements:
	@echo "🚀 Updating requirements.txt from pyproject.toml for use with Langgraph studio"
	./update_requirements.sh
	langgraph dockerfile -c langgraph.json Dockerfile
	cat Dockerfile


# Tail the LangGraph Studio logs
tail-langgraph-studio:
	log stream --predicate 'process == "LangGraph Studio"' --level info

logs-langgraph-studio:
	#!/bin/bash
	log show --predicate 'process == "LangGraph Studio"' --last 5m --debug --info --backtrace

# Access the Docker VM debug shell
docker-debug-shell:
		socat -d -d ~/Library/Containers/com.docker.docker/Data/debug-shell.sock pty,rawer
		@echo "Now run 'screen /dev/ttys0xx' in a new terminal (replace ttys0xx with the PTY output)"

# Access Docker VM using a privileged container
docker-vm-shell:
		docker run -it --rm --privileged --pid=host --name nsenter1 justincormack/nsenter1

# View overall Docker disk usage
docker-disk-usage:
		docker system df

# View detailed Docker disk usage
docker-disk-usage-verbose:
		docker system df -v

# List Docker images and their sizes
docker-list-images:
		docker image ls

# List all containers and their sizes
docker-list-containers:
		docker container ls -a

# Check the size of the Docker disk image file
docker-check-image-size:
		ls -klsh ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw

# Remove unused Docker objects
docker-prune:
	#!/bin/bash
	docker system prune --filter "until=$((60*24))h"

# Aggressively reclaim space (use with caution)
docker-reclaim-space:
		docker run --privileged --pid=host docker/desktop-reclaim-space

# Run all disk usage checks
docker-check-all:
		@just docker-disk-usage
		@just docker-disk-usage-verbose
		@just docker-list-images
		@just docker-list-containers
		@just docker-check-image-size

# Generate external documentation with configurable path and model
generate-external-docs path=EXTERNAL_DOCS_PATH model=EXTERNAL_DOCS_MODEL:
	#!/usr/bin/env bash
	uv run files-to-prompt {{path}} -c | uv run llm -m {{model}} -s 'write extensive usage documentation in markdown, including realistic usage examples' > {{path}}/docs.md
# Generate external documentation with configurable path and model
generate-advice path=EXTERNAL_DOCS_PATH model=EXTERNAL_DOCS_MODEL:
	#!/usr/bin/env bash
	uv run files-to-prompt {{path}} -c | uv run llm -m {{model}} -s 'step by step advice on how to implement automated tests for this, which is hard because the tests need to work a number of different ways within this project. Provide all code at the end.'


generate-langgraph-dockerfile-langraph-simple:
	@echo "🚀 Updating requirements.txt from pyproject.toml for use with Langgraph studio"
	./update_requirements.sh
	langgraph dockerfile -c langgraph.json Dockerfile
	echo "" >> Dockerfile
	echo "CMD bash -l" >> Dockerfile
	echo "" >> Dockerfile
	cat Dockerfile

# Build docker image for debugging and testing containers (NOTE: this is a langgraph specific dockerfile, use this to verify that the langgraph studio version of the dockerfile is working)
docker-build-langraph:
	@just generate-langgraph-dockerfile-langraph-simple
	docker build -f Dockerfile -t democracy-langraph .

# Run docker image for debugging
docker-run-langraph:
	docker run -it --entrypoint=/bin/bash democracy-langraph -l

# Update cursorrules.xml and aider_rules
update-rules:
	@echo "🚀 Updating cursorrules"
	cp -a cursorrules.xml .cursorrules
	@echo "🚀 Updating aider_rules"
	cp -a cursorrules.xml aider_configs/aider_rules
	git add .cursorrules aider_configs/aider_rules cursorrules.xml

# Find all special imports
find-all-special-imports:
	rg -t py '^\s*(from|import)\s+(discord|pydantic|pydantic_settings|dpytest)' contextforge_cli/ tests

# Find all unittest.mock imports and usage
find-all-mock-imports:
	rg -t py '^\s*(from|import)\s+unittest\.mock|^\s*from\s+unittest\s+import\s+.*mock'


# Add lint comments to files in contextforge_cli and tests
add-lint-comments-dry-run:
	./scripts/add_lint_comments.py --dir contextforge_cli --dry-run
	./scripts/add_lint_comments.py --dir tests --dry-run

# Add lint comments to files in contextforge_cli and tests
add-lint-comments:
	./scripts/add_lint_comments.py --dir contextforge_cli
	./scripts/add_lint_comments.py --dir tests


# Install the cursor update agent
install-cursor-update:
	mkdir -p ~/Library/LaunchAgents
	cp  -a ./hack/com.bossjones.cursor-update.plist ~/Library/LaunchAgents/
	launchctl load ~/Library/LaunchAgents/com.bossjones.cursor-update.plist

# Uninstall the cursor update agent
uninstall-cursor-update:
	launchctl unload ~/Library/LaunchAgents/com.bossjones.cursor-update.plist
	rm -v ~/Library/LaunchAgents/com.bossjones.cursor-update.plist

# print the directory tree of the project
tree:
	tree -L 3 -I "*.pyc|__pycache__|.git|.pytest_cache|.ruff_cache|.mypy_cache|.coverage|htmlcov|.venv|.env|*.egg-info|build|dist|node_modules|.DS_Store"


code2prompt-example:
	@echo "🚀 Generating code2prompt example. See: https://github.com/mufeedvh/code2prompt"
	code2prompt /Users/malcolm/dev/langchain-ai/langgraph --include="*.py,*.toml,*.pyi" --tokens --output=langgraph.txt

open-claude-config:
	cursor ~/Library/Application\ Support/Claude/claude_desktop_config.json

playwright-install-chrome:
	@echo "🚀 Installing Playwright Chrome browser"
	uv run python -m playwright install chromium
