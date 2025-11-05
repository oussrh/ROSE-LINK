.PHONY: help archive deb clean install test

help: ## Show this help message
	@echo "🌹 ROSE Link - Build Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

archive: ## Build tar.gz archive
	@echo "🗜️  Building archive..."
	@bash scripts/build-archive.sh

deb: ## Build Debian package
	@echo "📦 Building Debian package..."
	@bash scripts/build-deb.sh

all: archive deb ## Build both archive and deb package

clean: ## Clean build artifacts
	@echo "🧹 Cleaning..."
	@rm -f *.tar.gz *.deb
	@rm -rf debian/opt debian/etc
	@rm -rf roselink-repo
	@rm -rf backend/__pycache__ backend/*.pyc
	@rm -rf backend/venv
	@echo "✅ Clean complete"

install: ## Install ROSE Link (requires sudo)
	@echo "🚀 Installing ROSE Link..."
	@sudo bash install.sh

dev-backend: ## Run backend in development mode
	@echo "🐍 Starting backend..."
	@cd backend && python3 -m venv venv && \
		. venv/bin/activate && \
		pip install -r requirements.txt && \
		python main.py

test-backend: ## Test backend API
	@echo "🧪 Testing backend..."
	@curl -s http://127.0.0.1:8000/api/health | jq

setup-repo: ## Setup APT repository structure
	@echo "📦 Setting up APT repository..."
	@cd scripts/apt-repo && bash setup_repo.sh

add-package: ## Add package to APT repo (usage: make add-package PKG=file.deb)
	@echo "📦 Adding package to repository..."
	@cd scripts/apt-repo && bash add_package.sh ../../$(PKG)

publish-repo: ## Publish APT repo to GitHub Pages
	@echo "📤 Publishing repository..."
	@cd scripts/apt-repo && bash publish_to_github.sh

chmod: ## Fix script permissions
	@echo "🔧 Fixing permissions..."
	@chmod +x install.sh
	@chmod +x scripts/*.sh
	@chmod +x scripts/apt-repo/*.sh
	@chmod +x system/rose-watchdog.sh
	@echo "✅ Permissions fixed"

version: ## Show version
	@echo "ROSE Link v0.1.0"
	@echo "Routeur VPN sur Raspberry Pi 4"
