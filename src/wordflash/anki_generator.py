import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional

import genanki


class AnkiGenerator:
    def __init__(self, deck_name: str = "WordFlash Deck"):
        self.deck_name = deck_name
        self.model = self._create_model()
        self.deck = genanki.Deck(
            deck_id=self._generate_deck_id(deck_name), name=deck_name
        )

    def _create_model(self) -> genanki.Model:
        return genanki.Model(
            model_id=1607392319,
            name="WordFlash Model",
            fields=[
                {"name": "Image"},
                {"name": "Word"},
                {"name": "Translation"},
                {"name": "Audio"},
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": "{{Image}}",
                    "afmt": '{{FrontSide}}<hr id="answer">{{Word}}<br>{{Translation}}<br>{{Audio}}',
                },
            ],
            css="""
                .card {
                    font-family: arial;
                    font-size: 20px;
                    text-align: center;
                    color: black;
                    background-color: white;
                }

                img {
                    max-width: 400px;
                    max-height: 300px;
                    border-radius: 10px;
                }

                .word {
                    font-size: 24px;
                    font-weight: bold;
                    margin: 10px 0;
                }

                .translation {
                    font-size: 18px;
                    color: #666;
                    margin: 10px 0;
                }
            """,
        )

    def _generate_deck_id(self, deck_name: str) -> int:
        return int(hashlib.md5(deck_name.encode()).hexdigest()[:8], 16)

    def add_card(
        self,
        word: str,
        translation: str,
        image_path: Optional[str] = None,
        audio_path: Optional[str] = None,
    ):
        image_html = ""
        if image_path and os.path.exists(image_path):
            image_filename = os.path.basename(image_path)
            image_html = f'<img src="{image_filename}">'

        audio_html = ""
        if audio_path and os.path.exists(audio_path):
            audio_filename = os.path.basename(audio_path)
            audio_html = f"[sound:{audio_filename}]"

        note = genanki.Note(
            model=self.model, fields=[image_html, word, translation, audio_html]
        )

        self.deck.add_note(note)

    def generate_package(self, output_path: str, media_files: List[str] = None) -> str:
        if media_files is None:
            media_files = []

        package = genanki.Package(self.deck)
        package.media_files = [f for f in media_files if os.path.exists(f)]

        package.write_to_file(output_path)
        return output_path

    def get_media_files(self, cards_data: List[Dict]) -> List[str]:
        media_files = []

        for card in cards_data:
            if card.get("image_path") and os.path.exists(card["image_path"]):
                media_files.append(card["image_path"])
            if card.get("audio_path") and os.path.exists(card["audio_path"]):
                media_files.append(card["audio_path"])

        return media_files
