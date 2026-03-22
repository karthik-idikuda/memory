"""CORTEX-X — BaseLLMAdapter (Abstract interface for any LLM)."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseLLMAdapter(ABC):
    """Abstract base for all LLM adapters.

    Any LLM can connect to CORTEX-X by implementing this interface.
    """

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        """Generate a response from a list of messages."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the adapter is available."""
        ...

    @abstractmethod
    def list_models(self) -> List[str]:
        """List available models."""
        ...
