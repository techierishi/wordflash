import argparse
import sys
from pathlib import Path

from .flashcard_generator import FlashcardGenerator


def main():
    parser = argparse.ArgumentParser(
        description="Generate Anki flashcards from word lists"
    )
    parser.add_argument("input_file", help="Input YAML file with word list")
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

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = FlashcardGenerator(
        output_dir=output_dir,
        deck_name=args.deck_name,
        source_lang=args.source_lang,
        target_lang=args.target_lang,
    )

    try:
        generator.generate_from_yaml(input_path)
        print("Flashcard generation completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
