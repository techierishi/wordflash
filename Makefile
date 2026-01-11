# WordFlash Makefile

.PHONY: help install run demo demo-vocab demo-quiz clean build

help:
	@echo "WordFlash Makefile"
	@echo "=================="
	@echo ""
	@echo "Available targets:"
	@echo "  install      Install dependencies"
	@echo "  run          Run WordFlash (usage: make run ARGS='file.yaml')"
	@echo "  demo         Run with sample data"
	@echo "  demo-vocab   Run with sample vocabulary data"
	@echo "  demo-quiz    Run with sample quiz data"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build package"

install:
	@echo "📦 Installing dependencies..."
	uv sync

run:
	@echo "🚀 Running WordFlash..."
	uv run wordflash $(ARGS)

demo: demo-vocab

demo-vocab:
	@echo "🎬 Running vocab demo..."
	uv run wordflash data/test_enhanced_vocab.yaml --deck-name "Demo Deck"

demo-quiz:
	@echo "🎯 Running quiz demo..."
	uv run wordflash data/sample_quiz.yaml --deck-name "Quiz Demo" --type quiz

clean:
	@echo "🧹 Cleaning..."
	rm -rf dist/ build/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

build:
	@echo "📦 Building package..."
	uv build
