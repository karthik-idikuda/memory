"""CORTEX-X — SIGMA-X Reasoning Bridge."""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Callable
from cortex.exceptions import SigmaXSyncError


class SigmaXBridge:
    """Bridge to SIGMA-X causal reasoning system.

    Provides causal chain retrieval and creation.
    """

    def __init__(self):
        self._brain = None
        self._recall_fn: Optional[Callable] = None
        self._store_fn: Optional[Callable] = None

    def configure(self, brain: Any = None, recall_fn: Optional[Callable] = None,
                  store_fn: Optional[Callable] = None) -> None:
        """Configure with SIGMA-X brain instance or custom functions."""
        self._brain = brain
        self._recall_fn = recall_fn
        self._store_fn = store_fn

    def recall_chains(self, query: str, top_k: int = 5) -> List[Dict[str, str]]:
        """Recall causal chains relevant to query."""
        if self._recall_fn:
            try:
                return self._recall_fn(query, top_k)
            except Exception as e:
                raise SigmaXSyncError(f"Chain recall failed: {e}") from e

        if self._brain:
            try:
                results = self._brain.query(query, top_k=top_k)
                if isinstance(results, list):
                    return [
                        {"id": getattr(r, "id", str(i)), "content": str(getattr(r, "summary", r))}
                        for i, r in enumerate(results)
                    ]
            except Exception as e:
                raise SigmaXSyncError(f"SIGMA-X query error: {e}") from e

        return []

    def store_chain(self, cause: str, effect: str,
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store a new causal chain in SIGMA-X."""
        if self._store_fn:
            try:
                self._store_fn(cause, effect, metadata or {})
                return True
            except Exception as e:
                raise SigmaXSyncError(f"Chain store failed: {e}") from e

        if self._brain:
            try:
                self._brain.add_chain(cause=cause, effect=effect, **(metadata or {}))
                return True
            except Exception as e:
                raise SigmaXSyncError(f"SIGMA-X store error: {e}") from e

        return False

    @property
    def is_connected(self) -> bool:
        return self._brain is not None or self._recall_fn is not None
