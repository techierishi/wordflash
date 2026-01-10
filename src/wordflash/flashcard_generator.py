from pathlib import Path
from typing import Dict, List

from .anki_generator import AnkiGenerator
from .audio_service import AudioService
from .image_service import ImageService
from .word_loader import WordLoader


class FlashcardGenerator:
    def __init__(
        self,
        output_dir: Path,
        deck_name: str = "WordFlash Deck",
        source_lang: str = "de",
        target_lang: str = "en",
    ):
        self.output_dir = Path(output_dir)
        self.deck_name = deck_name
        self.source_lang = source_lang
        self.target_lang = target_lang

        self.word_loader = WordLoader(source_lang, target_lang)
        self.image_service = ImageService(self.output_dir)
        self.audio_service = AudioService(self.output_dir, source_lang)
        self.anki_generator = AnkiGenerator(deck_name)

    def generate_from_yaml(self, yaml_path: Path):
        words = self.word_loader.load_from_yaml(str(yaml_path))

        if not self.word_loader.validate_word_list(words):
            raise ValueError("Invalid word list format")

        print(f"Processing {len(words)} words...")

        cards_data = []
        for i, word_data in enumerate(words, 1):
            source_word = word_data["source"]
            target_word = word_data["target"]

            print(f"Processing {i}/{len(words)}: {source_word}")

            image_path = self.image_service.download_image(target_word)
            if image_path:
                print(f"  ✓ Image downloaded")
            else:
                print(f"  ✗ Image download failed")

            audio_path = self.audio_service.generate_audio(source_word)
            if audio_path:
                print(f"  ✓ Audio generated")
            else:
                print(f"  ✗ Audio generation failed")

            self.anki_generator.add_card(
                word=source_word,
                translation=target_word,
                image_path=image_path,
                audio_path=audio_path,
            )

            cards_data.append(
                {
                    "source_word": source_word,
                    "target_word": target_word,
                    "image_path": image_path,
                    "audio_path": audio_path,
                }
            )

        media_files = self.anki_generator.get_media_files(cards_data)
        output_file = self.output_dir / f"{self.deck_name.replace(' ', '_')}.apkg"

        self.anki_generator.generate_package(str(output_file), media_files)

        print(f"\nAnki deck generated: {output_file}")
        print(f"Total cards: {len(words)}")
        print(f"Media files included: {len(media_files)}")

        return str(output_file)
