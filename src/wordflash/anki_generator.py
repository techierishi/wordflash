import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Literal

import genanki


class AnkiGenerator:
    def __init__(
        self,
        deck_name: str = "WordFlash Deck",
        card_type: Literal["vocab", "quiz"] = "vocab",
    ):
        self.deck_name = deck_name
        self.card_type = card_type
        self.model = self._create_model()
        self.deck = genanki.Deck(
            deck_id=self._generate_deck_id(deck_name), name=deck_name
        )

    def _create_model(self) -> genanki.Model:
        """Create a flexible model supporting both vocab and quiz modes."""
        if self.card_type == "quiz":
            return self._create_quiz_model()
        else:
            return self._create_vocab_model()

    def _create_vocab_model(self) -> genanki.Model:
        """Original vocabulary model."""
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
            css=self._get_vocab_css(),
        )

    def _create_quiz_model(self) -> genanki.Model:
        """Model for flexible quiz cards with dynamic front/back."""
        return genanki.Model(
            model_id=1607392320,  # Different ID from vocab model
            name="WordFlash Quiz Model",
            fields=[
                {"name": "QuestionText"},
                {"name": "QuestionAudio"},
                {"name": "QuestionImage"},
                {"name": "AnswerText"},
                {"name": "AnswerAudio"},
                {"name": "AnswerImage"},
                {"name": "Category"},
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": """
                        <div class="question-container">
                            {{#QuestionImage}}<div class="question-image">{{QuestionImage}}</div>{{/QuestionImage}}
                            {{#QuestionText}}<div class="question-text">{{QuestionText}}</div>{{/QuestionText}}
                            {{#QuestionAudio}}<div class="question-audio">{{QuestionAudio}}</div>{{/QuestionAudio}}
                        </div>
                    """,
                    "afmt": """
                        {{FrontSide}}
                        <hr id="answer">
                        <div class="answer-container">
                            {{#AnswerImage}}<div class="answer-image">{{AnswerImage}}</div>{{/AnswerImage}}
                            {{#AnswerText}}<div class="answer-text">{{AnswerText}}</div>{{/AnswerText}}
                            {{#AnswerAudio}}<div class="answer-audio">{{AnswerAudio}}</div>{{/AnswerAudio}}
                        </div>
                    """,
                },
            ],
            css=self._get_quiz_css(),
        )

    def _get_vocab_css(self) -> str:
        """CSS for vocabulary cards."""
        return """
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
        """

    def _get_quiz_css(self) -> str:
        """CSS for quiz cards with flexible layouts."""
        return """
            .card {
                font-family: arial;
                font-size: 18px;
                text-align: center;
                color: #1a1a1a;
                background-color: white;
                padding: 20px;
            }

            .question-container, .answer-container {
                margin: 10px 0;
            }

            .question-text {
                font-size: 20px;
                font-weight: bold;
                margin: 15px 0;
                padding: 15px;
                background-color: #e3f2fd;
                color: #0d47a1;
                border-radius: 8px;
                border-left: 4px solid #1976d2;
            }

            .answer-text {
                font-size: 22px;
                font-weight: bold;
                margin: 15px 0;
                padding: 15px;
                background-color: #c8e6c9;
                color: #1b5e20;
                border-radius: 8px;
                border-left: 4px solid #388e3c;
            }

            .question-image, .answer-image {
                margin: 15px 0;
            }

            img {
                max-width: 500px;
                max-height: 400px;
                border-radius: 10px;
                margin: 10px 0;
            }

            .question-audio, .answer-audio {
                margin: 10px 0;
            }
        """

    def _generate_deck_id(self, deck_name: str) -> int:
        return int(hashlib.md5(deck_name.encode()).hexdigest()[:8], 16)

    def add_card(
        self,
        word: str,
        translation: str,
        image_path: Optional[str] = None,
        audio_path: Optional[str] = None,
    ):
        """Add vocabulary-style card (for backward compatibility)."""
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

    def add_quiz_card(
        self,
        question_text: str,
        answer_text: str,
        question_audio_path: Optional[str] = None,
        answer_audio_path: Optional[str] = None,
        question_image_path: Optional[str] = None,
        answer_image_path: Optional[str] = None,
        category: str = "Uncategorized",
        question_media_config: Optional[Dict] = None,
        answer_media_config: Optional[Dict] = None,
    ):
        """Add quiz-style card with flexible media configuration.
        
        Args:
            question_text: The question text
            answer_text: The answer text
            question_audio_path: Path to question audio file
            answer_audio_path: Path to answer audio file
            question_image_path: Path to question image
            answer_image_path: Path to answer image
            category: Category for the question
            question_media_config: Dict with 'text', 'audio', 'image' booleans
            answer_media_config: Dict with 'text', 'audio', 'image' booleans
        """
        default_config = {"text": True, "audio": False, "image": False}
        q_config = {**default_config, **(question_media_config or {})}
        a_config = {**default_config, **(answer_media_config or {})}

        # Build question content
        q_text_html = f"<p>{question_text}</p>" if q_config.get("text") else ""
        q_audio_html = ""
        if q_config.get("audio") and question_audio_path:
            if os.path.exists(question_audio_path):
                audio_filename = os.path.basename(question_audio_path)
                q_audio_html = f"[sound:{audio_filename}]"

        q_image_html = ""
        if q_config.get("image") and question_image_path:
            if os.path.exists(question_image_path):
                image_filename = os.path.basename(question_image_path)
                q_image_html = f'<img src="{image_filename}">'

        # Build answer content
        a_text_html = f"<p>{answer_text}</p>" if a_config.get("text") else ""
        a_audio_html = ""
        if a_config.get("audio") and answer_audio_path:
            if os.path.exists(answer_audio_path):
                audio_filename = os.path.basename(answer_audio_path)
                a_audio_html = f"[sound:{audio_filename}]"

        a_image_html = ""
        if a_config.get("image") and answer_image_path:
            if os.path.exists(answer_image_path):
                image_filename = os.path.basename(answer_image_path)
                a_image_html = f'<img src="{image_filename}">'

        # Create note with all 7 fields for quiz model
        note = genanki.Note(
            model=self.model,
            fields=[
                q_text_html,           # QuestionText
                q_audio_html,          # QuestionAudio
                q_image_html,          # QuestionImage
                a_text_html,           # AnswerText
                a_audio_html,          # AnswerAudio
                a_image_html,          # AnswerImage
                category,              # Category
            ],
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
            # Handle vocab-style cards (image_path, audio_path)
            if card.get("image_path") and os.path.exists(card["image_path"]):
                media_files.append(card["image_path"])
            if card.get("audio_path") and os.path.exists(card["audio_path"]):
                media_files.append(card["audio_path"])
            
            # Handle quiz-style cards (question/answer_*_path)
            for media_type in [
                "question_audio_path",
                "answer_audio_path",
                "question_image_path",
                "answer_image_path",
            ]:
                if card.get(media_type) and os.path.exists(card[media_type]):
                    if card[media_type] not in media_files:
                        media_files.append(card[media_type])

        return media_files
