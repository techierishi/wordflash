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

### Image Approval

When downloading images, WordFlash displays each image for your approval:
- Type `y` to approve and use the image
- Type `n` to reject and try the next image  
- Type `skip` to skip this question

To skip image approval and auto-download first matches:
```bash
uv run wordflash data/kids_learning.yaml --type quiz --no-image-approval
```

**Linux Requirements**: If image viewer fails, install:
```bash
sudo apt install xdg-utils  # or eog for Eye of GNOME
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

All category separate files:
```bash
for file in data/categories/*.yaml; do
  deck_name=$(basename "$file" .yaml | tr '_' ' ')
  uv run wordflash "$file" --type quiz --deck-name "$deck_name"
done
```
## Output

Generates `.apkg` files (Anki packages) with:
- All flashcards with configured media
- Downloaded images
- Generated audio pronunciations

See `data/kids_learning.yaml` for a complete example with 250+ questions covering planets, geography, flags, animals, fish, birds, plants, body parts, and world leaders.

