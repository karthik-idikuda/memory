"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Custom Tokenizer                       ║
║  NRNLANG-Ω: TOKENIZE — extract meaningful signal tokens  ║
╚══════════════════════════════════════════════════════════╝

Custom tokenizer with no external NLP dependencies.
Uses the exact stop words list from the NEURON-X specification.
"""

import re
from typing import FrozenSet

from neuronx.config import STOP_WORDS


def tokenize(text: str) -> FrozenSet[str]:
    """
    NRNLANG-Ω: TOKENIZE — extract meaningful signal tokens.

    Steps (exact spec):
      1. text.lower()
      2. re.sub(r'[^a-z0-9\\s]', ' ', text)
      3. text.split()
      4. filter(lambda t: len(t) >= 3, tokens)
      5. filter(lambda t: t not in STOP_WORDS, tokens)
      6. return frozenset(tokens)
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    words = text.split()
    tokens = frozenset(
        t for t in words
        if len(t) >= 3 and t not in STOP_WORDS
    )
    return tokens


def jaccard(a: FrozenSet[str], b: FrozenSet[str]) -> float:
    """
    NRNLANG-Ω: JACCARD(a, b)

    ta = tokenize(a)
    tb = tokenize(b)
    if not ta and not tb: return 1.0
    if not ta or not tb: return 0.0
    return len(ta & tb) / len(ta | tb)
    """
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    intersection = a & b
    union = a | b
    if not union:
        return 0.0
    return len(intersection) / len(union)


def jaccard_text(text_a: str, text_b: str) -> float:
    """Convenience: compute Jaccard similarity between two text strings."""
    return jaccard(tokenize(text_a), tokenize(text_b))
