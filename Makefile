.PHONY: help archive deb clean install test test-cov lint lint-fix dev setup-dev

help: ## Show this help message
	@echo "🌹 ROSE Link - Build Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# === Development ===

setup-dev: ## Setup development environment
	@echo "🔧 Setting up development environment..."
	@cd backend && python3 -m venv venv && \
		. venv/bin/activate && \
		pip install --upgrade pip && \
		pip install -r requirements.txt && \
		pip install -r requirements-dev.txt
	@echo "✅ Development environment ready"
	@echo "   Run: source backend/venv/bin/activate"

dev-backend: ## Run backend in development mode
	@echo "🐍 Starting backend..."
	@cd backend && python3 -m venv venv && \
		. venv/bin/activate && \
		pip install -r requirements.txt && \
		python main.py

dev: dev-backend ## Alias for dev-backend

# === Testing ===

test: ## Run backend tests
	@echo "🧪 Running tests..."
	@cd backend && . venv/bin/activate && pytest

test-cov: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	@cd backend && . venv/bin/activate && \
		pytest --cov=. --cov-report=term-missing --cov-report=html:coverage_html
	@echo "📊 Coverage report: backend/coverage_html/index.html"

test-fast: ## Run tests without coverage (faster)
	@echo "🧪 Running tests (fast mode)..."
	@cd backend && . venv/bin/activate && pytest --no-cov -q

test-watch: ## Run tests in watch mode
	@echo "🧪 Running tests in watch mode..."
	@cd backend && . venv/bin/activate && ptw -- --no-cov -q

test-api: ## Test backend API health
	@echo "🧪 Testing backend API..."
	@curl -s http://127.0.0.1:8000/api/health | jq

# === Linting & Quality ===

lint: ## Run linting checks
	@echo "🔍 Running linters..."
	@cd backend && . venv/bin/activate && \
		ruff check . && \
		echo "✅ Linting passed"

lint-fix: ## Fix linting issues automatically
	@echo "🔧 Fixing linting issues..."
	@cd backend && . venv/bin/activate && \
		ruff check . --fix && \
		ruff format .
	@echo "✅ Linting fixes applied"

typecheck: ## Run type checking
	@echo "🔍 Running type checker..."
	@cd backend && . venv/bin/activate && \
		mypy . --ignore-missing-imports

security: ## Run security scan
	@echo "🔒 Running security scan..."
	@cd backend && . venv/bin/activate && \
		bandit -r . -ll --exclude ./tests

# === Build ===

archive: ## Build tar.gz archive
	@echo "🗜️  Building archive..."
	@bash scripts/build-archive.sh

deb: ## Build Debian package
	@echo "📦 Building Debian package..."
	@bash scripts/build-deb.sh

all: archive deb ## Build both archive and deb package

# === Installation ===

install: ## Install ROSE Link (requires sudo)
	@echo "🚀 Installing ROSE Link..."
	@sudo bash install.sh

# === Repository Management ===

setup-repo: ## Setup APT repository structure
	@echo "📦 Setting up APT repository..."
	@cd scripts/apt-repo && bash setup_repo.sh

add-package: ## Add package to APT repo (usage: make add-package PKG=file.deb)
	@echo "📦 Adding package to repository..."
	@cd scripts/apt-repo && bash add_package.sh ../../$(PKG)

publish-repo: ## Publish APT repo to GitHub Pages
	@echo "📤 Publishing repository..."
	@cd scripts/apt-repo && bash publish_to_github.sh

# === Utilities ===

clean: ## Clean build artifacts
	@echo "🧹 Cleaning..."
	@rm -f *.tar.gz *.deb
	@rm -rf debian/opt debian/etc
	@rm -rf roselink-repo
	@rm -rf backend/__pycache__ backend/*.pyc
	@rm -rf backend/.pytest_cache backend/.coverage
	@rm -rf backend/coverage_html backend/coverage.xml
	@rm -rf backend/venv
	@rm -rf web/node_modules
	@echo "✅ Clean complete"

chmod: ## Fix script permissions
	@echo "🔧 Fixing permissions..."
	@chmod +x install.sh
	@chmod +x scripts/*.sh
	@chmod +x scripts/apt-repo/*.sh
	@chmod +x system/rose-watchdog.sh
	@echo "✅ Permissions fixed"

version: ## Show version
	@cat VERSION 2>/dev/null || echo "unknown"
	@echo "VPN Router for Raspberry Pi"
	@echo "See PRODUCT_FEATURES.md for full capabilities"

sync-version: ## Sync version across all components from VERSION file
	@./scripts/sync-version.sh

# === CI/CD Simulation ===

ci: lint test-cov security ## Run full CI pipeline locally
	@echo "✅ CI pipeline passed"
