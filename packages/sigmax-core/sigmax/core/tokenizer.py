"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Tokenizer                               ║
║  CAULANG-Ω: TOKENIZER — words to atoms                   ║
╚══════════════════════════════════════════════════════════╝

Custom tokenizer for causal text processing.
Extracts meaningful words, detects causal signal words,
and computes word overlap (Jaccard similarity).

Shared philosophy with NEURON-X tokenizer but tuned for
causal language detection.
"""

from __future__ import annotations

import re
from typing import FrozenSet, List, Set, Tuple

from sigmax.config import STOP_WORDS, CAUSAL_SIGNAL_WORDS


# Pre-compiled patterns for performance
_WORD_PATTERN = re.compile(r'[a-zA-Z]{2,}')
_SENTENCE_PATTERN = re.compile(r'[.!?]+\s+')
_CAUSAL_SPLIT_PATTERN = re.compile(
    r'\b(?:because|since|therefore|thus|hence|consequently|'
    r'so\s+that|leads?\s+to|results?\s+in|causes?|caused\s+by|'
    r'due\s+to|owing\s+to|as\s+a\s+result|for\s+this\s+reason|'
    r'if\s+.*?\s+then)\b',
    re.IGNORECASE
)


def tokenize(text: str) -> List[str]:
    """
    Extract meaningful words from text.

    1. Lowercase
    2. Extract words (2+ alpha chars)
    3. Remove stop words

    Returns list of tokens (preserves order, allows duplicates).
    """
    if not text or not isinstance(text, str):
        return []
    words = _WORD_PATTERN.findall(text.lower())
    return [w for w in words if w not in STOP_WORDS]


def tokenize_unique(text: str) -> FrozenSet[str]:
    """Tokenize and return unique tokens as a frozenset."""
    return frozenset(tokenize(text))


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """
    Compute Jaccard similarity between two sets.
    J(A,B) = |A ∩ B| / |A ∪ B|
    Returns 0.0 if both sets are empty.
    """
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    if union == 0:
        return 0.0
    return intersection / union


def word_overlap(text_a: str, text_b: str) -> float:
    """
    Compute word overlap (Jaccard) between two texts.
    Uses tokenized, stop-word-filtered sets.
    """
    tokens_a = tokenize_unique(text_a)
    tokens_b = tokenize_unique(text_b)
    return jaccard_similarity(set(tokens_a), set(tokens_b))


def causal_resonance(query: str, cause: str, effect: str) -> float:
    """
    Compute causal resonance between a query and a cause-effect pair.

    resonance = (jaccard(query, cause) + jaccard(query, effect)) / 2.0

    This is the CAUSAL_RESONANCE component of the SIGMA score.
    """
    query_tokens = set(tokenize_unique(query))
    cause_tokens = set(tokenize_unique(cause))
    effect_tokens = set(tokenize_unique(effect))

    cause_sim = jaccard_similarity(query_tokens, cause_tokens)
    effect_sim = jaccard_similarity(query_tokens, effect_tokens)

    return (cause_sim + effect_sim) / 2.0


def detect_causal_signals(text: str) -> List[str]:
    """
    Detect causal signal words present in the text.
    Returns list of found signal words.
    """
    if not text:
        return []
    words = set(_WORD_PATTERN.findall(text.lower()))
    return sorted(words & CAUSAL_SIGNAL_WORDS)


def has_causal_language(text: str) -> bool:
    """Check if text contains any causal signal words."""
    return len(detect_causal_signals(text)) > 0


def split_causal_text(text: str) -> List[Tuple[str, str]]:
    """
    Split text into potential cause-effect pairs using causal markers.

    Returns list of (cause_fragment, effect_fragment) tuples.
    Uses regex to find causal connectors and split around them.
    """
    if not text:
        return []

    pairs = []
    # Find all causal split points
    matches = list(_CAUSAL_SPLIT_PATTERN.finditer(text))

    if not matches:
        return []

    for match in matches:
        before = text[:match.start()].strip()
        after = text[match.end():].strip()

        # Clean up: take last sentence of before, first sentence of after
        if before:
            sentences = _SENTENCE_PATTERN.split(before)
            before = sentences[-1].strip() if sentences else before

        if after:
            sentences = _SENTENCE_PATTERN.split(after)
            after = sentences[0].strip() if sentences else after

        if before and after and len(before) > 3 and len(after) > 3:
            pairs.append((before, after))

    return pairs


def extract_subjects(text: str) -> List[str]:
    """
    Extract potential subjects (proper nouns, capitalized words) from text.
    Simple heuristic: words that start with uppercase (not at sentence start).
    """
    if not text:
        return []

    words = text.split()
    subjects = []

    for i, word in enumerate(words):
        cleaned = re.sub(r'[^a-zA-Z]', '', word)
        if not cleaned:
            continue
        # Skip first word of text and words after sentence-ending punctuation
        if i > 0 and cleaned[0].isupper() and cleaned.lower() not in STOP_WORDS:
            subjects.append(cleaned)

    return list(dict.fromkeys(subjects))  # preserve order, deduplicate


def compute_text_hash(text: str) -> int:
    """
    Compute a fast, deterministic hash for text.
    Used for quick duplicate detection (not cryptographic).
    """
    h = 0
    for token in tokenize(text):
        h = (h * 31 + hash(token)) & 0xFFFFFFFF
    return h


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison:
    - Lowercase
    - Strip whitespace
    - Collapse multiple spaces
    - Remove punctuation
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text
