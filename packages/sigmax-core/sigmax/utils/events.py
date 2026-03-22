"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Event System                             ║
║  SigmaEvent — track every brain operation                  ║
╚══════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class SigmaEvent:
    """A single brain event."""
    event_type: str = ""
    data: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            'event_type': self.event_type,
            'data': self.data,
            'timestamp': self.timestamp,
        }


class EventBus:
    """Simple event bus for SIGMA-X brain operations."""

    def __init__(self, max_history: int = 1000):
        self._listeners: Dict[str, List[Callable]] = {}
        self._history: List[SigmaEvent] = []
        self._max_history = max_history

    def on(self, event_type: str, callback: Callable) -> None:
        """Register a listener for an event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def off(self, event_type: str, callback: Callable) -> None:
        """Remove a listener."""
        if event_type in self._listeners:
            self._listeners[event_type] = [
                cb for cb in self._listeners[event_type] if cb != callback
            ]

    def emit(self, event_type: str, data: Optional[dict] = None) -> None:
        """Emit an event to all registered listeners."""
        event = SigmaEvent(event_type=event_type, data=data or {})
        self._history.append(event)

        # Trim history
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        # Notify listeners
        for callback in self._listeners.get(event_type, []):
            try:
                callback(event)
            except Exception:
                pass  # listeners should not crash the brain

        # Also notify wildcard listeners
        for callback in self._listeners.get('*', []):
            try:
                callback(event)
            except Exception:
                pass

    @property
    def history(self) -> List[SigmaEvent]:
        return list(self._history)

    def get_events_by_type(self, event_type: str) -> List[SigmaEvent]:
        return [e for e in self._history if e.event_type == event_type]

    def clear_history(self) -> int:
        count = len(self._history)
        self._history.clear()
        return count


# Standard event types
EVENT_CHAIN_CREATED = "chain.created"
EVENT_CHAIN_DELETED = "chain.deleted"
EVENT_CHAIN_STRENGTHENED = "chain.strengthened"
EVENT_EVIDENCE_ADDED = "evidence.added"
EVENT_PREDICTION_CREATED = "prediction.created"
EVENT_PREDICTION_VERIFIED = "prediction.verified"
EVENT_PREDICTION_FALSIFIED = "prediction.falsified"
EVENT_AXIOM_CRYSTALLIZED = "axiom.crystallized"
EVENT_ZONE_CHANGED = "zone.changed"
EVENT_BRAIN_SAVED = "brain.saved"
EVENT_BRAIN_LOADED = "brain.loaded"
EVENT_AUDIT_COMPLETE = "audit.complete"
EVENT_BRIDGE_SYNCED = "bridge.synced"
