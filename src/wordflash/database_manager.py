import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tinydb import Query, TinyDB
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage


class DatabaseManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize TinyDB with caching for better performance
        self.db = TinyDB(self.db_path, storage=CachingMiddleware(JSONStorage), indent=2)

        self.words_table = self.db.table("words")
        self.categories_table = self.db.table("categories")
        self.relations_table = self.db.table("word_relations")

        self.init_database()

    def init_database(self):
        if not self.categories_table.all():
            default_categories = [
                {"name": "fruit", "description": "Fruits and berries"},
                {"name": "vegetables", "description": "Vegetables and greens"},
                {"name": "animals", "description": "All types of animals"},
                {"name": "food", "description": "Food items and cuisine"},
                {"name": "vehicles", "description": "Transportation vehicles"},
                {"name": "professions", "description": "Jobs and careers"},
            ]
            self.categories_table.insert_multiple(default_categories)

    def _generate_hash(self, source: str, target: str) -> str:
        combined = f"{source.lower()}:{target.lower()}"
        return hashlib.md5(combined.encode("utf-8")).hexdigest()

    def add_word(self, word_data: Dict[str, Any]) -> Tuple[int, bool]:
        source = word_data["source"]
        target = word_data["target"]
        source_hash = self._generate_hash(source, target)

        Word = Query()
        existing = self.words_table.search(Word.source_hash == source_hash)

        if existing:
            word_id = existing[0].doc_id
            self._update_word_metadata(word_id, word_data, existing[0])
            return word_id, False
        else:
            word_doc = {
                "source": source,
                "target": target,
                "source_hash": source_hash,
                "gender": word_data.get("gender"),
                "plural": word_data.get("plural"),
                "categories": word_data.get("categories", []),
                "notes": word_data.get("notes"),
                "created_at": self._get_timestamp(),
                "updated_at": self._get_timestamp(),
            }

            word_id = self.words_table.insert(word_doc)
            return word_id, True

    def _update_word_metadata(
        self, word_id: int, word_data: Dict[str, Any], existing_doc: Dict[str, Any]
    ):
        existing_categories = existing_doc.get("categories", [])
        new_categories = word_data.get("categories", [])

        combined_categories = list(set(existing_categories + new_categories))

        updates = {
            "categories": combined_categories,
            "updated_at": self._get_timestamp(),
        }

        if not existing_doc.get("gender") and word_data.get("gender"):
            updates["gender"] = word_data["gender"]
        if not existing_doc.get("plural") and word_data.get("plural"):
            updates["plural"] = word_data["plural"]
        if not existing_doc.get("notes") and word_data.get("notes"):
            updates["notes"] = word_data["notes"]

        self.words_table.update(updates, doc_ids=[word_id])

    def _get_timestamp(self) -> str:
        from datetime import datetime

        return datetime.now().isoformat()

    def get_word_by_source(self, source: str) -> Optional[Dict[str, Any]]:
        Word = Query()
        result = self.words_table.search(Word.source == source)

        if result:
            doc = result[0]
            return {
                "id": doc.doc_id,
                "source": doc["source"],
                "target": doc["target"],
                "gender": doc.get("gender"),
                "plural": doc.get("plural"),
                "categories": doc.get("categories", []),
                "notes": doc.get("notes"),
            }
        return None

    def get_duplicates(self) -> List[Dict[str, Any]]:
        all_words = self.words_table.all()
        seen = {}
        duplicates = []

        for word in all_words:
            key = (word["source"], word["target"])
            if key in seen:
                duplicates.append(
                    {
                        "source": word["source"],
                        "target": word["target"],
                        "count": seen[key] + 1,
                    }
                )
                seen[key] += 1
            else:
                seen[key] = 1

        return duplicates

    def get_words_by_category(self, category: str) -> List[Dict[str, Any]]:
        Word = Query()
        results = self.words_table.search(Word.categories.any([category]))

        words = []
        for doc in results:
            words.append(
                {
                    "id": doc.doc_id,
                    "source": doc["source"],
                    "target": doc["target"],
                    "gender": doc.get("gender"),
                    "plural": doc.get("plural"),
                    "categories": doc.get("categories", []),
                    "notes": doc.get("notes"),
                }
            )

        return words

    def get_multi_category_words(self) -> List[Dict[str, Any]]:
        all_words = self.words_table.all()
        multi_category_words = []

        for doc in all_words:
            categories = doc.get("categories", [])
            if len(categories) > 1:
                multi_category_words.append(
                    {
                        "id": doc.doc_id,
                        "source": doc["source"],
                        "target": doc["target"],
                        "gender": doc.get("gender"),
                        "plural": doc.get("plural"),
                        "categories": categories,
                        "notes": doc.get("notes"),
                    }
                )

        return multi_category_words

    def get_all_categories(self) -> List[str]:
        all_words = self.words_table.all()
        all_categories = set()

        for word in all_words:
            categories = word.get("categories", [])
            all_categories.update(categories)

        return sorted(list(all_categories))

    def add_word_relation(self, word_id: int, related_word_id: int, relation_type: str):
        relation_doc = {
            "word_id": word_id,
            "related_word_id": related_word_id,
            "relation_type": relation_type,
        }

        Relation = Query()
        existing = self.relations_table.search(
            (Relation.word_id == word_id)
            & (Relation.related_word_id == related_word_id)
            & (Relation.relation_type == relation_type)
        )

        if not existing:
            self.relations_table.insert(relation_doc)

    def get_word_relations(self, word_id: int) -> List[Dict[str, Any]]:
        Relation = Query()
        relations = self.relations_table.search(Relation.word_id == word_id)

        result = []
        for relation in relations:
            related_word = self.words_table.get(doc_id=relation["related_word_id"])
            if related_word:
                result.append(
                    {
                        "source": related_word["source"],
                        "target": related_word["target"],
                        "relation_type": relation["relation_type"],
                    }
                )

        return result

    def get_statistics(self) -> Dict[str, Any]:
        all_words = self.words_table.all()
        total_words = len(all_words)

        unique_sources = len(set(word["source"] for word in all_words))

        multi_category_count = sum(
            1 for word in all_words if len(word.get("categories", [])) > 1
        )

        categories = self.get_all_categories()

        return {
            "total_words": total_words,
            "unique_sources": unique_sources,
            "multi_category_words": multi_category_count,
            "total_categories": len(categories),
            "categories": categories,
        }

    def search_words(
        self, query: str, search_type: str = "both"
    ) -> List[Dict[str, Any]]:
        Word = Query()

        if search_type == "source":
            results = self.words_table.search(Word.source.search(query))
        elif search_type == "target":
            results = self.words_table.search(Word.target.search(query))
        else:
            results = self.words_table.search(
                (Word.source.search(query)) | (Word.target.search(query))
            )

        words = []
        for doc in results:
            words.append(
                {
                    "id": doc.doc_id,
                    "source": doc["source"],
                    "target": doc["target"],
                    "gender": doc.get("gender"),
                    "plural": doc.get("plural"),
                    "categories": doc.get("categories", []),
                    "notes": doc.get("notes"),
                }
            )

        return words

    def get_words_by_gender(self, gender: str) -> List[Dict[str, Any]]:
        Word = Query()
        results = self.words_table.search(Word.gender == gender)

        words = []
        for doc in results:
            words.append(
                {
                    "id": doc.doc_id,
                    "source": doc["source"],
                    "target": doc["target"],
                    "gender": doc["gender"],
                    "plural": doc.get("plural"),
                    "categories": doc.get("categories", []),
                    "notes": doc.get("notes"),
                }
            )

        return words

    def export_words(self, format_type: str = "dict") -> List[Dict[str, Any]]:
        all_words = self.words_table.all()
        words = []

        for doc in sorted(all_words, key=lambda x: x["source"]):
            word_data = {"source": doc["source"], "target": doc["target"]}

            if doc.get("gender"):
                word_data["gender"] = doc["gender"]
            if doc.get("plural"):
                word_data["plural"] = doc["plural"]
            if doc.get("categories"):
                word_data["categories"] = doc["categories"]
            if doc.get("notes"):
                word_data["notes"] = doc["notes"]

            words.append(word_data)

        return words

    def clear_database(self):
        self.words_table.truncate()
        self.categories_table.truncate()
        self.relations_table.truncate()

    def get_database_info(self) -> Dict[str, Any]:
        return {
            "database_type": "TinyDB",
            "database_path": str(self.db_path),
            "tables": {
                "words": len(self.words_table),
                "categories": len(self.categories_table),
                "relations": len(self.relations_table),
            },
        }

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
