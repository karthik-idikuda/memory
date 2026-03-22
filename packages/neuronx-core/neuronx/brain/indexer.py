"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Subject Indexer                        ║
║  NRNLANG-Ω: INDEX — O(n×k) contradiction lookup         ║
╚══════════════════════════════════════════════════════════╝

BUG-014 FIX: Pre-filter contradiction candidates using subject index.
Reduces O(n²) to approximately O(n × k) where k << n.
"""

from typing import Dict, Set, List

from neuronx.core.node import EngramNode
from neuronx.utils.tokenizer import tokenize


class SubjectIndex:
    """
    NRNLANG-Ω: SUBJECT_INDEX — fast token-to-engram lookup.

    Maps subject_tokens → set of engram_ids.
    Used by ContradictionEngine to avoid O(n²) comparison.
    """

    def __init__(self):
        self._index: Dict[str, Set[str]] = {}

    def add(self, engram: EngramNode) -> None:
        """Index an engram by its tokens."""
        tokens = tokenize(engram.raw)
        for token in tokens:
            if token not in self._index:
                self._index[token] = set()
            self._index[token].add(engram.id)

    def remove(self, engram: EngramNode) -> None:
        """Remove an engram from the index."""
        tokens = tokenize(engram.raw)
        for token in tokens:
            if token in self._index:
                self._index[token].discard(engram.id)
                if not self._index[token]:
                    del self._index[token]

    def find_candidates(self, text: str, min_shared: int = 1) -> Set[str]:
        """
        Find engram IDs sharing at least min_shared tokens with text.
        Returns set of candidate engram IDs.
        """
        tokens = tokenize(text)
        candidates: Dict[str, int] = {}
        for token in tokens:
            if token in self._index:
                for eid in self._index[token]:
                    candidates[eid] = candidates.get(eid, 0) + 1

        return {eid for eid, count in candidates.items() if count >= min_shared}

    def rebuild(self, engrams: Dict[str, EngramNode]) -> None:
        """Rebuild the entire index from scratch."""
        self._index.clear()
        for engram in engrams.values():
            if engram.is_active_engram():
                self.add(engram)

    @property
    def token_count(self) -> int:
        return len(self._index)

    @property
    def total_entries(self) -> int:
        return sum(len(eids) for eids in self._index.values())
