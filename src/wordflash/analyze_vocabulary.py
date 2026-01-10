import argparse
import sys
from pathlib import Path

from .database_manager import DatabaseManager
from .word_loader import WordLoader


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_section(title: str):
    print(f"\n{title}:")
    print("-" * len(title) + "-")


def analyze_vocabulary(yaml_file: str, db_path: str = None):
    print("WordFlash Vocabulary Analysis")
    print_header("Loading and Processing Vocabulary")

    if db_path:
        db_path = Path(db_path)
    else:
        db_path = Path("data/output/wordflash_analysis.json")

    word_loader = WordLoader(db_path=db_path)

    if yaml_file:
        print(f"Loading vocabulary from: {yaml_file}")
        words = word_loader.load_from_yaml(yaml_file)
        print(f"Loaded {len(words)} word pairs")

    analysis = word_loader.analyze_vocabulary()

    print_header("Vocabulary Statistics")
    stats = analysis["statistics"]
    print(f"Total words in database: {stats['total_words']}")
    print(f"Unique source words: {stats['unique_sources']}")
    print(f"Multi-category words: {stats['multi_category_words']}")
    print(f"Total categories: {stats['total_categories']}")

    print_section("Categories")
    for i, category in enumerate(stats["categories"], 1):
        word_count = analysis["category_distribution"].get(category, 0)
        print(f"  {i:2d}. {category:<20} ({word_count:3d} words)")

    duplicates = analysis["duplicates"]
    if duplicates:
        print_section("Duplicate Words")
        for dup in duplicates:
            print(
                f"  '{dup['source']}' -> '{dup['target']}' (appears {dup['count']} times)"
            )
    else:
        print_section("Duplicate Words")
        print("  No duplicates found")

    multi_category = analysis["multi_category_words"]
    if multi_category:
        print_section("Multi-Category Words")
        print(f"Found {len(multi_category)} words that appear in multiple categories:")

        for word in multi_category[:20]:
            categories_str = ", ".join(word["categories"])
            print(f"  '{word['source']}' -> '{word['target']}'")
            print(f"    Categories: {categories_str}")
            if word.get("notes"):
                print(f"    Notes: {word['notes']}")
            print()

        if len(multi_category) > 20:
            print(f"  ... and {len(multi_category) - 20} more")

    print_header("Category Analysis")

    category_pairs = [
        ("food", "sea_animals"),
        ("vehicles", "transportation"),
        ("hotel", "travel"),
        ("professions", "work"),
        ("toys", "children"),
    ]

    for cat1, cat2 in category_pairs:
        words1 = set(w["source"] for w in word_loader.get_words_by_category(cat1))
        words2 = set(w["source"] for w in word_loader.get_words_by_category(cat2))
        overlap = words1.intersection(words2)

        if overlap:
            print(f"\nOverlap between '{cat1}' and '{cat2}': {len(overlap)} words")
            for word in sorted(overlap):
                print(f"  - {word}")

    print_header("Gender Distribution")
    db_manager = word_loader.db_manager

    all_words = db_manager.words_table.all()
    gender_counts = {}

    for word in all_words:
        gender = word.get("gender")
        if gender:
            gender_counts[gender] = gender_counts.get(gender, 0) + 1

    total_gendered = sum(gender_counts.values())

    if total_gendered > 0:
        print(f"Words with gender information: {total_gendered}")
        for gender, count in gender_counts.items():
            percentage = (count / total_gendered) * 100
            print(f"  {gender:<10}: {count:3d} ({percentage:5.1f}%)")
    else:
        print("No gender information found")

    print_header("Recommendations")

    recommendations = []

    if duplicates:
        recommendations.append(f"Review {len(duplicates)} duplicate entries")

    if multi_category:
        recommendations.append(
            f"Consider creating specialized decks for {len(multi_category)} multi-category words"
        )

    missing_gender = stats["total_words"] - sum(
        count for count in gender_counts.values()
    )
    if missing_gender > 0:
        recommendations.append(f"Add gender information for {missing_gender} words")

    categories_with_few_words = [
        cat for cat, count in analysis["category_distribution"].items() if count < 5
    ]
    if categories_with_few_words:
        recommendations.append(
            f"Consider expanding {len(categories_with_few_words)} categories with few words"
        )

    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    else:
        print("  Vocabulary structure looks good!")

    print_header("Search Examples")
    print("Try these commands to explore your vocabulary:")
    print(f"  python {sys.argv[0]} --search Fisch")
    print(f"  python {sys.argv[0]} --category food")
    print(f"  python {sys.argv[0]} --gender feminine")


def search_vocabulary(db_path: str, query: str, search_type: str = "both"):
    db_path = Path(db_path) if db_path else Path("data/output/wordflash_analysis.json")
    word_loader = WordLoader(db_path=db_path)

    results = word_loader.search_words(query, search_type)

    print(f"Search results for '{query}' (type: {search_type}):")
    print(f"Found {len(results)} matches")
    print()

    for word in results:
        categories_str = ", ".join(word["categories"])
        print(f"'{word['source']}' -> '{word['target']}'")
        print(f"  Categories: {categories_str}")
        if word.get("gender"):
            print(f"  Gender: {word['gender']}")
        if word.get("plural"):
            print(f"  Plural: {word['plural']}")
        if word.get("notes"):
            print(f"  Notes: {word['notes']}")
        print()


def show_category(db_path: str, category: str):
    db_path = Path(db_path) if db_path else Path("data/output/wordflash_analysis.json")
    word_loader = WordLoader(db_path=db_path)

    words = word_loader.get_words_by_category(category)

    print(f"Words in category '{category}':")
    print(f"Found {len(words)} words")
    print()

    for word in words:
        other_categories = [cat for cat in word["categories"] if cat != category]
        print(f"'{word['source']}' -> '{word['target']}'")
        if other_categories:
            print(f"  Also in: {', '.join(other_categories)}")
        if word.get("gender"):
            print(f"  Gender: {word['gender']}")
        if word.get("notes"):
            print(f"  Notes: {word['notes']}")
        print()


def show_gender(db_path: str, gender: str):
    db_path = Path(db_path) if db_path else Path("data/output/wordflash_analysis.json")
    word_loader = WordLoader(db_path=db_path)

    words = word_loader.db_manager.get_words_by_gender(gender)

    print(f"Words with gender '{gender}':")
    print(f"Found {len(words)} words")
    print()

    for word in words:
        categories_str = ", ".join(word.get("categories", []))

        print(f"'{word['source']}' -> '{word['target']}'")
        print(f"  Categories: {categories_str}")
        if word.get("plural"):
            print(f"  Plural: {word['plural']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze WordFlash vocabulary database"
    )

    parser.add_argument(
        "yaml_file",
        nargs="?",
        help="YAML file to analyze (optional if database exists)",
    )

    parser.add_argument(
        "--db-path",
        help="Database file path (default: data/output/wordflash_analysis.json)",
    )

    parser.add_argument("--search", help="Search for words containing this term")

    parser.add_argument(
        "--search-type",
        choices=["source", "target", "both"],
        default="both",
        help="Type of search to perform",
    )

    parser.add_argument("--category", help="Show words in specific category")

    parser.add_argument(
        "--gender",
        choices=["masculine", "feminine", "neuter"],
        help="Show words of specific gender",
    )

    args = parser.parse_args()

    if args.search:
        search_vocabulary(args.db_path, args.search, args.search_type)
    elif args.category:
        show_category(args.db_path, args.category)
    elif args.gender:
        show_gender(args.db_path, args.gender)
    else:
        if not args.yaml_file:
            print("Error: YAML file required for full analysis")
            sys.exit(1)

        if not Path(args.yaml_file).exists():
            print(f"Error: File '{args.yaml_file}' not found")
            sys.exit(1)

        analyze_vocabulary(args.yaml_file, args.db_path)


if __name__ == "__main__":
    main()
