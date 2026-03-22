"""CORTEX-X — Event system for brain lifecycle hooks."""

from __future__ import annotations
from typing import Callable, Dict, List, Any
from collections import defaultdict


class CortexEvent:
    """Simple event system for CORTEX-X lifecycle hooks."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)

    def on(self, event: str, handler: Callable) -> None:
        """Register an event handler."""
        self._handlers[event].append(handler)

    def emit(self, event: str, **kwargs) -> None:
        """Emit an event to all registered handlers."""
        for handler in self._handlers.get(event, []):
            try:
                handler(**kwargs)
            except Exception:
                pass  # Swallow handler errors

    def off(self, event: str, handler: Callable) -> None:
        """Remove a handler."""
        if event in self._handlers:
            try:
                self._handlers[event].remove(handler)
            except ValueError:
                pass


# Pre-defined events
EVENT_THOUGHT_CREATED = "thought.created"
EVENT_THOUGHT_CORRECTED = "thought.corrected"
EVENT_WISDOM_CRYSTALLIZED = "wisdom.crystallized"
EVENT_PATTERN_DETECTED = "pattern.detected"
EVENT_DRIFT_DETECTED = "drift.detected"
EVENT_HALLUCINATION_BLOCKED = "hallucination.blocked"
EVENT_STRATEGY_EVOLVED = "strategy.evolved"
EVENT_BRAIN_SAVED = "brain.saved"
EVENT_BRAIN_LOADED = "brain.loaded"
EVENT_SESSION_STARTED = "session.started"
EVENT_SESSION_ENDED = "session.ended"
