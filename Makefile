# WordFlash Makefile

.PHONY: help install run demo clean build

help:
	@echo "WordFlash Makefile"
	@echo "=================="
	@echo ""
	@echo "Available targets:"
	@echo "  install    Install dependencies"
	@echo "  run        Run WordFlash (usage: make run ARGS='file.yaml')"
	@echo "  demo       Run with sample data"
	@echo "  clean      Clean build artifacts"
	@echo "  build      Build package"

install:
	@echo "📦 Installing dependencies..."
	uv sync

run:
	@echo "🚀 Running WordFlash..."
	uv run wordflash $(ARGS)

demo:
	@echo "🎬 Running demo..."
	uv run wordflash data/test_enhanced_vocab.yaml --deck-name "Demo Deck"

clean:
	@echo "🧹 Cleaning..."
	rm -rf dist/ build/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

build:
	@echo "📦 Building package..."
	uv build
