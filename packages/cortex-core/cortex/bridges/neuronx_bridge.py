"""CORTEX-X — NEURON-X Memory Bridge."""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Callable
from cortex.exceptions import NeuronXSyncError


class NeuronXBridge:
    """Bridge to NEURON-X memory system.

    Provides memory recall and storage functions.
    Set the actual NEURON-X instance via configure().
    """

    def __init__(self):
        self._brain = None
        self._recall_fn: Optional[Callable] = None
        self._store_fn: Optional[Callable] = None

    def configure(self, brain: Any = None, recall_fn: Optional[Callable] = None,
                  store_fn: Optional[Callable] = None) -> None:
        """Configure the bridge with a NEURON-X brain instance or custom functions."""
        self._brain = brain
        self._recall_fn = recall_fn
        self._store_fn = store_fn

    def recall(self, query: str, top_k: int = 10) -> List[Dict[str, str]]:
        """Recall memories relevant to query.

        Returns list of dicts with 'id' and 'content' keys.
        """
        if self._recall_fn:
            try:
                return self._recall_fn(query, top_k)
            except Exception as e:
                raise NeuronXSyncError(f"Memory recall failed: {e}") from e

        if self._brain:
            try:
                results = self._brain.recall(query, top_k=top_k)
                if isinstance(results, list):
                    return [
                        {"id": getattr(r, "id", str(i)), "content": str(getattr(r, "content", r))}
                        for i, r in enumerate(results)
                    ]
            except Exception as e:
                raise NeuronXSyncError(f"NEURON-X recall error: {e}") from e

        return []

    def store(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store a new memory in NEURON-X."""
        if self._store_fn:
            try:
                self._store_fn(content, metadata or {})
                return True
            except Exception as e:
                raise NeuronXSyncError(f"Memory store failed: {e}") from e

        if self._brain:
            try:
                self._brain.memorize(content, **(metadata or {}))
                return True
            except Exception as e:
                raise NeuronXSyncError(f"NEURON-X store error: {e}") from e

        return False

    @property
    def is_connected(self) -> bool:
        return self._brain is not None or self._recall_fn is not None
