# Makefile for Home Assistant Migration Tool

.PHONY: help install clean test build wheel

# Default target
help:
	@echo "Home Assistant Migration Tool Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Virtual Environment Targets:"
	@echo "  venv         - Create virtual environment"
	@echo "  venv-install - Create venv and install dependencies"
	@echo "  venv-activate - Show activation command"
	@echo ""
	@echo "Build/Install Targets:"
	@echo "  install      - Install dependencies"
	@echo "  build        - Build the package"
	@echo "  wheel        - Build wheel distribution"
	@echo "  install-wheel - Build and install wheel"
	@echo "  clean        - Clean build artifacts"
	@echo "  test         - Run tests"
	@echo ""
	@echo "Migration Targets:"
	@echo "  setup        - Run migration step 1 (setup)"
	@echo "  compute      - Run migration step 2 (compute)"
	@echo "  apply        - Run migration step 3 (apply)"
	@echo "  migrate      - Full migration workflow"
	@echo ""

# Virtual environment targets
venv:
	@echo "🐍 Creating virtual environment..."
	python -m venv .venv

venv-install:
	@echo "🐍 Creating virtual environment and installing dependencies..."
	python -m venv .venv
	. .venv/bin/activate && pip install -e .

venv-activate:
	@echo "🐍 To activate the virtual environment, run:"
	@echo "   source .venv/bin/activate"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	. .venv/bin/activate && pip install -e .

# Build the package
build:
	@echo "🔨 Building package..."
	. .venv/bin/activate && python -m build --no-isolation

# Build wheel distribution
wheel:
	@echo "🎡 Building wheel..."
	. .venv/bin/activate && python -m build --wheel --no-isolation

# Build and install wheel
install-wheel:
	@echo "🎡 Building and installing wheel..."
	. .venv/bin/activate && python -m build --wheel --no-isolation
	. .venv/bin/activate && pip install dist/*.whl --force-reinstall

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info/
	rm -rf __pycache__/ */__pycache__/ */*/__pycache__/

# Run tests
test:
	@echo "🧪 Running tests..."
	. .venv/bin/activate && python -m pytest tests/ -v

# Migration step 1: Setup
setup:
	@echo "🚀 Running migration step 1: Setup"
	. .venv/bin/activate && python scripts/migration_step1_setup.py

# Migration step 2: Compute
compute:
	@echo "🔍 Running migration step 2: Compute"
	@echo "Usage: MIGRATION_NAME=name DESCRIPTION="description" make compute"
	. .venv/bin/activate && python scripts/migration_step2_compute.py "$(MIGRATION_NAME)" "$(DESCRIPTION)"

# Migration step 3: Apply
apply:
	@echo "🎯 Running migration step 3: Apply"
	. .venv/bin/activate && python scripts/migration_step3_apply.py

# Shortcut for full migration workflow
migrate:
	@echo "🔄 Running full migration workflow"
	make setup
	@echo "Make your modifications in migration/desired/ then press Enter..."
	read dummy
	@echo "Enter migration name:"
	read migration_name
	@echo "Enter migration description:"
	read description
	python scripts/migration_step2_compute.py "$$migration_name" "$$description"
	@echo "Review changes, then press Enter to apply..."
	read dummy
	make apply