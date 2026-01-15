import argparse
import sys
from pathlib import Path

import yaml

from .flashcard_generator import FlashcardGenerator
from .quiz_flashcard_generator import QuizFlashcardGenerator


def _detect_input_type(yaml_path: Path) -> str:
    """Auto-detect whether input is vocab or quiz format."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if isinstance(data, dict):
        if "quizzes" in data:
            return "quiz"
        elif "words" in data:
            return "vocab"
        # Check if it looks like quiz data (has questions)
        elif "questions" in data:
            return "quiz"
    
    # Default to vocab
    return "vocab"


def main():
    parser = argparse.ArgumentParser(
        description="Generate Anki flashcards from word lists or quiz data"
    )
    parser.add_argument("input_file", help="Input YAML file with word list or quizzes")
    parser.add_argument(
        "--type",
        choices=["auto", "vocab", "quiz"],
        default="auto",
        help="Input type: auto (detect), vocab (word pairs), or quiz (Q&A)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/output",
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--deck-name", default="WordFlash Deck", help="Name of the Anki deck"
    )
    parser.add_argument(
        "--source-lang",
        default="de",
        help="Source language code (default: de for German)",
    )
    parser.add_argument(
        "--target-lang",
        default="en",
        help="Target language code (default: en for English)",
    )
    parser.add_argument(
        "--question-lang",
        default="en",
        help="Question language for quiz mode (default: en)",
    )
    parser.add_argument(
        "--answer-lang",
        default="en",
        help="Answer language for quiz mode (default: en)",
    )
    parser.add_argument(
        "--no-image-approval",
        action="store_true",
        help="Skip manual image approval (auto-download first match)",
    )
    parser.add_argument(
        "--clipboard-only",
        action="store_true",
        help="Only use clipboard for image input (skip Pixabay and Wikipedia)",
    )

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine input type
    input_type = args.type
    if input_type == "auto":
        input_type = _detect_input_type(input_path)
        print(f"Auto-detected input type: {input_type}")

    try:
        if input_type == "quiz":
            generator = QuizFlashcardGenerator(
                output_dir=output_dir,
                deck_name=args.deck_name,
                question_lang=args.question_lang,
                answer_lang=args.answer_lang,
                manual_image_approval=not args.no_image_approval,
                clipboard_only=args.clipboard_only,
            )
        else:  # vocab
            generator = FlashcardGenerator(
                output_dir=output_dir,
                deck_name=args.deck_name,
                source_lang=args.source_lang,
                target_lang=args.target_lang,
                clipboard_only=args.clipboard_only,
            )

        generator.generate_from_yaml(input_path)

        print("Flashcard generation completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
