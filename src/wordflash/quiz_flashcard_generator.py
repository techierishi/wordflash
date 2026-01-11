"""Quiz-specific flashcard generator with flexible media handling."""

from pathlib import Path
from typing import Dict, List

from .anki_generator import AnkiGenerator
from .audio_service import AudioService
from .image_service import ImageService
from .quiz_loader import QuizLoader


class QuizFlashcardGenerator:
    """Generate Anki flashcards from quiz data with flexible media configuration."""

    def __init__(
        self,
        output_dir: Path,
        deck_name: str = "Quiz Deck",
        question_lang: str = "en",
        answer_lang: str = "en",
        manual_image_approval: bool = True,
    ):
        self.output_dir = Path(output_dir)
        self.deck_name = deck_name
        self.question_lang = question_lang
        self.answer_lang = answer_lang
        self.manual_image_approval = manual_image_approval

        self.quiz_loader = QuizLoader()
        self.image_service = ImageService(self.output_dir)
        self.audio_service = AudioService(self.output_dir, language=question_lang)
        self.anki_generator = AnkiGenerator(deck_name, card_type="quiz")

    def generate_from_yaml(self, yaml_path: Path):
        """Generate Anki deck from quiz YAML file."""
        quizzes = self.quiz_loader.load_from_yaml(str(yaml_path))

        if not self.quiz_loader.validate_quiz_list(quizzes):
            raise ValueError("Invalid quiz list format")

        print(f"Processing {len(quizzes)} quiz questions...")

        cards_data = []
        for i, quiz_data in enumerate(quizzes, 1):
            question = quiz_data["question"]
            answer = quiz_data["answer"]
            category = quiz_data.get("category", "Uncategorized")
            q_media = quiz_data.get("question_media", {})
            a_media = quiz_data.get("answer_media", {})

            print(f"\nProcessing {i}/{len(quizzes)}: {question[:60]}...")

            # Process question media
            question_audio_path = None
            question_image_path = None

            if q_media.get("audio"):
                q_lang = quiz_data.get("question_lang", self.question_lang)
                question_audio_path = self.audio_service.generate_audio(question)
                if question_audio_path:
                    print(f"  ✓ Question audio generated")
                else:
                    print(f"  ✗ Question audio generation failed")

            if q_media.get("image"):
                search_term = quiz_data.get(
                    "question_image_search_term", question
                )
                question_image_path = self.image_service.download_image(
                    search_term, manual_approval=self.manual_image_approval
                )
                if question_image_path:
                    print(f"  ✓ Question image downloaded")
                else:
                    print(f"  ✗ Question image download failed")

            # Process answer media
            answer_audio_path = None
            answer_image_path = None

            if a_media.get("audio"):
                a_lang = quiz_data.get("answer_lang", self.answer_lang)
                # Create a temporary audio service with answer language if different
                audio_service = (
                    self.audio_service
                    if a_lang == self.question_lang
                    else AudioService(self.output_dir, language=a_lang)
                )
                answer_audio_path = audio_service.generate_audio(answer)
                if answer_audio_path:
                    print(f"  ✓ Answer audio generated")
                else:
                    print(f"  ✗ Answer audio generation failed")

            if a_media.get("image"):
                search_term = quiz_data.get("answer_image_search_term", answer)
                answer_image_path = self.image_service.download_image(
                    search_term, manual_approval=self.manual_image_approval
                )
                if answer_image_path:
                    print(f"  ✓ Answer image downloaded")
                else:
                    print(f"  ✗ Answer image download failed")

            # Add card to Anki deck
            self.anki_generator.add_quiz_card(
                question_text=question,
                answer_text=answer,
                question_audio_path=question_audio_path,
                answer_audio_path=answer_audio_path,
                question_image_path=question_image_path,
                answer_image_path=answer_image_path,
                category=category,
                question_media_config=q_media,
                answer_media_config=a_media,
            )

            cards_data.append(
                {
                    "question": question,
                    "answer": answer,
                    "category": category,
                    "question_audio_path": question_audio_path,
                    "answer_audio_path": answer_audio_path,
                    "question_image_path": question_image_path,
                    "answer_image_path": answer_image_path,
                }
            )

        # Generate the package
        media_files = self.anki_generator.get_media_files(cards_data)
        output_file = self.output_dir / f"{self.deck_name.replace(' ', '_')}.apkg"

        self.anki_generator.generate_package(str(output_file), media_files)

        print(f"\n✓ Anki deck generated: {output_file}")
        print(f"  Total cards: {len(quizzes)}")
        print(f"  Media files included: {len(media_files)}")

        return str(output_file)

    def get_media_files(self, cards_data: List[Dict]) -> List[str]:
        """Get list of all media files from cards."""
        return self.anki_generator.get_media_files(cards_data)
