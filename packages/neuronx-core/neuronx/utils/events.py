"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Event System                           ║
║  NRNLANG-Ω: EVENTS — pub/sub for memory lifecycle       ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
from typing import Callable, Dict, List, Any


logger = logging.getLogger("NEURONX.EVENTS")


class EventBus:
    """Simple event bus for NEURON-X lifecycle events."""

    FORGE = "forge"
    ECHO = "echo"
    CLASH = "clash"
    EXPIRE = "expire"
    CRYSTALLIZE = "crystallize"
    REAWAKEN = "reawaken"
    AUDIT = "audit"
    SAVE = "save"
    LOAD = "load"

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def on(self, event: str, handler: Callable) -> None:
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    def off(self, event: str, handler: Callable) -> None:
        if event in self._handlers:
            self._handlers[event] = [h for h in self._handlers[event] if h != handler]

    def emit(self, event: str, **data: Any) -> None:
        if event in self._handlers:
            for handler in self._handlers[event]:
                try:
                    handler(**data)
                except Exception as e:
                    logger.error(f"Event handler error for '{event}': {e}")


# Global event bus singleton
events = EventBus()
