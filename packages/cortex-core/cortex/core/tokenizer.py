"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Tokenizer                                  ║
║  Shared text processing for metacognitive analysis           ║
╚══════════════════════════════════════════════════════════════╝

Provides text tokenization, keyword extraction, domain detection,
claim extraction, and semantic overlap computation.
Used by hallucination shield, contradiction detector, and pattern recognizer.
"""

from __future__ import annotations

import re
import math
from collections import Counter
from typing import List, Tuple, Set

from cortex.config import STOP_WORDS


def tokenize(text: str) -> List[str]:
    """Split text into lowercase tokens, removing punctuation."""
    return re.findall(r'[a-zA-Z0-9]+', text.lower())


def tokenize_filtered(text: str) -> List[str]:
    """Tokenize and remove stop words."""
    return [t for t in tokenize(text) if t not in STOP_WORDS]


def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    """Extract top-K keywords by frequency (stop words removed)."""
    tokens = tokenize_filtered(text)
    counter = Counter(tokens)
    return [word for word, _ in counter.most_common(top_k)]


def extract_claims(text: str) -> List[str]:
    """Extract individual claims/sentences from text.

    A claim is roughly one sentence or one assertion.
    Used by the hallucination shield to check each claim independently.
    """
    # Split on sentence boundaries
    sentences = re.split(r'[.!?]+', text)
    claims = []
    for s in sentences:
        s = s.strip()
        if len(s) > 10:  # skip very short fragments
            claims.append(s)
    return claims if claims else [text.strip()] if text.strip() else []


def jaccard_similarity(tokens_a: List[str], tokens_b: List[str]) -> float:
    """Compute Jaccard similarity between two token lists.

    J(A,B) = |A ∩ B| / |A ∪ B|
    """
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    if not set_a and not set_b:
        return 1.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def cosine_similarity(tokens_a: List[str], tokens_b: List[str]) -> float:
    """Compute cosine similarity using bag-of-words representation.

    cos(A,B) = (A · B) / (|A| × |B|)
    """
    counter_a = Counter(tokens_a)
    counter_b = Counter(tokens_b)
    all_tokens = set(counter_a.keys()) | set(counter_b.keys())
    if not all_tokens:
        return 1.0

    dot_product = sum(counter_a.get(t, 0) * counter_b.get(t, 0) for t in all_tokens)
    mag_a = math.sqrt(sum(v ** 2 for v in counter_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in counter_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot_product / (mag_a * mag_b)


def semantic_overlap(text_a: str, text_b: str) -> float:
    """Compute semantic overlap between two texts.

    Combines Jaccard and cosine similarity:
    overlap = 0.4 × jaccard + 0.6 × cosine
    """
    tokens_a = tokenize_filtered(text_a)
    tokens_b = tokenize_filtered(text_b)
    j = jaccard_similarity(tokens_a, tokens_b)
    c = cosine_similarity(tokens_a, tokens_b)
    return 0.4 * j + 0.6 * c


def detect_domain(text: str) -> str:
    """Auto-detect the domain/topic of text.

    Uses keyword matching against known domain vocabularies.
    Returns the best-matching domain name.
    """
    tokens = set(tokenize_filtered(text))

    domain_keywords = {
        "programming": {"code", "function", "variable", "class", "bug",
                       "error", "api", "database", "server", "python",
                       "javascript", "import", "array", "string", "loop",
                       "debug", "compile", "runtime", "syntax", "git"},
        "science": {"experiment", "hypothesis", "data", "research",
                   "theory", "analysis", "study", "evidence", "result",
                   "observation", "measurement", "control", "sample"},
        "math": {"equation", "formula", "calculate", "number", "proof",
                "theorem", "algebra", "geometry", "calculus", "probability",
                "statistics", "integral", "derivative", "matrix"},
        "business": {"revenue", "market", "customer", "product", "strategy",
                    "growth", "sales", "profit", "investment", "startup",
                    "company", "budget", "cost", "pricing", "roi"},
        "writing": {"paragraph", "essay", "story", "character", "plot",
                   "narrative", "draft", "edit", "publish", "author",
                   "fiction", "nonfiction", "chapter", "poem"},
        "health": {"symptom", "treatment", "diagnosis", "medicine",
                  "health", "patient", "disease", "doctor", "medical",
                  "therapy", "wellness", "exercise", "diet", "nutrition"},
        "education": {"learn", "teach", "student", "course", "exam",
                     "study", "lecture", "curriculum", "grade", "school",
                     "university", "degree", "homework", "assignment"},
    }

    best_domain = "general"
    best_score = 0

    for domain, keywords in domain_keywords.items():
        overlap = len(tokens & keywords)
        if overlap > best_score:
            best_score = overlap
            best_domain = domain

    return best_domain


def ngrams(tokens: List[str], n: int = 2) -> List[Tuple[str, ...]]:
    """Generate n-grams from a token list."""
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def token_fingerprint(text: str) -> str:
    """Create a compact fingerprint from text for quick comparison.

    Sorts unique filtered tokens and joins them.
    """
    tokens = sorted(set(tokenize_filtered(text)))
    return "|".join(tokens[:20])
