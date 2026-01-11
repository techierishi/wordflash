"""Quiz loader for handling flexible Q&A flashcard formats."""

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .database_manager import DatabaseManager


class QuizLoader:
    """Load quiz questions with flexible media configurations."""

    def __init__(self):
        self.db_manager = None
        self.db_path = Path("data/output/wordflash.json")

    def _get_db(self):
        if self.db_manager is None:
            self.db_manager = DatabaseManager(self.db_path)
        return self.db_manager

    def load_from_yaml(self, file_path: str) -> List[Dict]:
        """Load quiz data from YAML file.
        
        Expected format:
        quizzes:
          - category: "Presidents"
            questions:
              - question: "Who is the president of the US?"
                question_media:
                  text: true
                  audio: true
                  image: false
                answer: "Donald Trump"
                answer_media:
                  text: true
                  audio: false
                  image: true
                  image_search_term: "Donald Trump"
        """
        with open(file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        quizzes = []

        if isinstance(data, dict):
            if "quizzes" in data and isinstance(data["quizzes"], list):
                quizzes = self._process_quizzes(data["quizzes"])
            else:
                # Treat as single quiz
                quizzes = self._process_quizzes([data])
        elif isinstance(data, list):
            quizzes = self._process_quizzes(data)

        return quizzes

    def _process_quizzes(self, quizzes_list: List[Dict]) -> List[Dict]:
        """Process quiz entries and validate structure."""
        quizzes = []
        for quiz_item in quizzes_list:
            if isinstance(quiz_item, dict):
                # Handle both single category with questions and multiple quizzes
                if "questions" in quiz_item:
                    # This is a quiz with questions
                    category = quiz_item.get("category", "Uncategorized")
                    questions = quiz_item.get("questions", [])
                    
                    for question_data in questions:
                        if isinstance(question_data, dict):
                            processed = self._process_question(
                                question_data, category
                            )
                            if processed:
                                quizzes.append(processed)
                else:
                    # Skip items without questions
                    pass

        return quizzes

    def _process_question(
        self, question_data: Dict, category: str = "Uncategorized"
    ) -> Optional[Dict]:
        """Process individual question and validate structure."""
        if "question" not in question_data or "answer" not in question_data:
            return None

        # Default media configuration (all false except text)
        default_media = {"text": True, "audio": False, "image": False}

        question_media = {
            **default_media,
            **question_data.get("question_media", {}),
        }
        answer_media = {
            **default_media,
            **question_data.get("answer_media", {}),
        }

        processed_question = {
            "question": str(question_data["question"]),
            "answer": str(question_data["answer"]),
            "question_media": question_media,
            "answer_media": answer_media,
            "category": category,
            "notes": question_data.get("notes"),
            # For image search, use provided term or fall back to answer
            "answer_image_search_term": question_data.get(
                "answer_image_search_term", question_data["answer"]
            ),
            "question_image_search_term": question_data.get(
                "question_image_search_term", question_data["question"]
            ),
            # Store original language configuration if specified
            "question_lang": question_data.get("question_lang", "en"),
            "answer_lang": question_data.get("answer_lang", "en"),
        }

        return processed_question

    def store_quiz_to_db(self, quiz_data: Dict) -> bool:
        try:
            db = self._get_db()
            db.add_word({
                "source": quiz_data["question"],
                "target": quiz_data["answer"],
                "category": quiz_data.get("category", "Uncategorized"),
                "type": "quiz",
            })
            return True
        except Exception:
            return False

    def is_quiz_unique(self, question: str, answer: str) -> bool:
        try:
            db = self._get_db()
            from tinydb import Query
            Word = Query()
            word_hash = db._generate_hash(question, answer)
            existing = db.words_table.search(Word.source_hash == word_hash)
            return len(existing) == 0
        except Exception:
            return True

    def validate_quiz_list(self, quizzes: List[Dict]) -> bool:
        """Validate that quiz list has required fields."""
        if not isinstance(quizzes, list) or len(quizzes) == 0:
            return False

        for quiz in quizzes:
            required_fields = {"question", "answer", "question_media", "answer_media"}
            if not all(field in quiz for field in required_fields):
                return False

            # Validate media configs are dicts with text/audio/image keys
            for media_type in ["question_media", "answer_media"]:
                media = quiz.get(media_type, {})
                required_media_keys = {"text", "audio", "image"}
                if not all(key in media for key in required_media_keys):
                    return False

        return True
