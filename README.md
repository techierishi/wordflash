# WordFlash - Anki Flashcard Generator

Generate Anki flashcards from YAML word lists with images and audio.

## Installation

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup project
git clone <repository-url>
cd wordflash
uv sync
```

## Usage

```bash
# Generate flashcards
uv run wordflash data/sample_words.yaml

# With options
uv run wordflash data/sample_words.yaml --deck-name "German Vocab" --source-lang de
```

## YAML Format

```yaml
Hund: dog
Katze: cat
Haus: house
```

## Makefile Commands

```bash
make install    # Install dependencies
make demo       # Run with sample data
make clean      # Clean build artifacts
```

The application generates Anki .apkg files with images and audio for language learning.