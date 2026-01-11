# WordFlash - Anki Flashcard Generator

Generate Anki flashcards from YAML quiz data with images and audio.

## Installation

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone <repository-url>
cd wordflash
uv sync
```

## Usage

```bash
uv run wordflash data/kids_learning.yaml --type quiz --deck-name "Kids Learning"
```

## YAML Format

```yaml
quizzes:
  - category: "Topic"
    questions:
      - question: "Question text?"
        question_media: {text: true, audio: false, image: false}
        answer: "Answer text"
        answer_media: {text: true, audio: false, image: true}
        answer_image_search_term: "optional custom image search"
```

## Media Config

- `text: true/false` - Show text
- `audio: true/false` - Include audio pronunciation
- `image: true/false` - Include image

## Commands

```bash
make install          # Install dependencies
make demo-vocab       # Run vocabulary demo
make demo-quiz        # Run quiz demo
make run ARGS="file.yaml"  # Generate from file
```

## Output

Generates `.apkg` files (Anki packages) with:
- All flashcards with configured media
- Downloaded images
- Generated audio pronunciations

See `data/kids_learning.yaml` for a complete example with 250+ questions covering planets, geography, flags, animals, fish, birds, plants, body parts, and world leaders.

