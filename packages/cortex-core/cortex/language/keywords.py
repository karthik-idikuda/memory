"""CORTEX-X — CORTEXLANG-Ω Keywords."""

from cortex.config import CORTEXLANG_KEYWORDS

# Flat list of all keywords
ALL_KEYWORDS = []
for category_keywords in CORTEXLANG_KEYWORDS.values():
    ALL_KEYWORDS.extend(category_keywords)
ALL_KEYWORDS_SET = frozenset(ALL_KEYWORDS)

# Keyword → category mapping
KEYWORD_CATEGORY = {}
for cat, kws in CORTEXLANG_KEYWORDS.items():
    for kw in kws:
        KEYWORD_CATEGORY[kw] = cat


def is_keyword(word: str) -> bool:
    """Check if a word is a CORTEXLANG keyword."""
    return word.upper() in ALL_KEYWORDS_SET


def category_of(word: str) -> str:
    """Get the category of a keyword."""
    return KEYWORD_CATEGORY.get(word.upper(), "unknown")


def keywords_for_category(category: str) -> list:
    """Get all keywords in a category."""
    return CORTEXLANG_KEYWORDS.get(category, [])


def all_categories() -> list:
    """List all keyword categories."""
    return list(CORTEXLANG_KEYWORDS.keys())
