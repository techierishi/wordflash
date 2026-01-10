from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .database_manager import DatabaseManager


class WordLoader:
    def __init__(
        self,
        source_lang: str = "de",
        target_lang: str = "en",
        db_path: Optional[Path] = None,
    ):
        self.source_lang = source_lang
        self.target_lang = target_lang

        if db_path is None:
            db_path = Path("data/output/wordflash.json")

        self.db_manager = DatabaseManager(db_path)

    def load_from_yaml(self, file_path: str) -> List[Dict[str, str]]:
        with open(file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        words = []

        if isinstance(data, dict):
            if "words" in data and isinstance(data["words"], list):
                words = self._process_enhanced_format(data["words"])
            else:
                words = self._process_simple_format(data)
        elif isinstance(data, list):
            words = self._process_enhanced_format(data)

        self._store_words_in_database(words)

        return self._convert_to_simple_format(words)

    def _process_simple_format(self, data: Dict) -> List[Dict[str, any]]:
        words = []
        for source_word, target_word in data.items():
            word_data = {
                "source": str(source_word),
                "target": str(target_word),
                "categories": ["uncategorized"],
            }
            words.append(word_data)
        return words

    def _process_enhanced_format(self, words_list: List[Dict]) -> List[Dict[str, any]]:
        words = []
        for item in words_list:
            if isinstance(item, dict):
                if "source" in item and "target" in item:
                    word_data = {
                        "source": str(item["source"]),
                        "target": str(item["target"]),
                        "gender": item.get("gender"),
                        "plural": item.get("plural"),
                        "categories": item.get("categories", ["uncategorized"]),
                        "notes": item.get("notes"),
                    }
                    words.append(word_data)
                elif len(item) == 1:
                    source_word, target_word = next(iter(item.items()))
                    word_data = {
                        "source": str(source_word),
                        "target": str(target_word),
                        "categories": ["uncategorized"],
                    }
                    words.append(word_data)
        return words

    def _store_words_in_database(self, words: List[Dict[str, any]]):
        for word_data in words:
            word_id, is_new = self.db_manager.add_word(word_data)
            if not is_new:
                print(
                    f"  ! Duplicate found: {word_data['source']} -> {word_data['target']}"
                )

    def _convert_to_simple_format(
        self, words: List[Dict[str, any]]
    ) -> List[Dict[str, str]]:
        simple_words = []
        for word in words:
            simple_words.append({"source": word["source"], "target": word["target"]})
        return simple_words

    def validate_word_list(self, words: List[Dict[str, str]]) -> bool:
        if not words:
            return False

        for word in words:
            if not isinstance(word, dict):
                return False
            if "source" not in word or "target" not in word:
                return False
            if not word["source"] or not word["target"]:
                return False

        return True

    def get_statistics(self) -> Dict[str, any]:
        return self.db_manager.get_statistics()

    def get_duplicates(self) -> List[Dict[str, any]]:
        return self.db_manager.get_duplicates()

    def get_multi_category_words(self) -> List[Dict[str, any]]:
        return self.db_manager.get_multi_category_words()

    def get_words_by_category(self, category: str) -> List[Dict[str, any]]:
        return self.db_manager.get_words_by_category(category)

    def search_words(
        self, query: str, search_type: str = "both"
    ) -> List[Dict[str, any]]:
        return self.db_manager.search_words(query, search_type)

    def export_enhanced_format(self) -> Dict[str, any]:
        words = self.db_manager.export_words()
        return {"words": words}

    def analyze_vocabulary(self) -> Dict[str, any]:
        stats = self.get_statistics()
        duplicates = self.get_duplicates()
        multi_category = self.get_multi_category_words()

        analysis = {
            "statistics": stats,
            "duplicates": duplicates,
            "multi_category_words": multi_category,
            "category_distribution": {},
        }

        for category in stats["categories"]:
            category_words = self.get_words_by_category(category)
            analysis["category_distribution"][category] = len(category_words)

        return analysis
