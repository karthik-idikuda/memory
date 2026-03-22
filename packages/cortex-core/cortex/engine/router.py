"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — LLM Router                                ║
║  Routes to any LLM via adapter pattern                      ║
╚══════════════════════════════════════════════════════════════╝

Supports: Anthropic, OpenAI, Ollama, any OpenAI-compatible endpoint.
Adapters are lazy-loaded — no import error if you don't have the SDK.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional

from cortex.config import (
    SUPPORTED_LLMS, DEFAULT_LLM, DEFAULT_MODEL,
    RESPONSE_TIMEOUT_SECONDS,
)
from cortex.exceptions import LLMAdapterError, LLMNotAvailableError


class LLMRouter:
    """Routes generation requests to the correct LLM adapter."""

    def __init__(self):
        self._adapters: Dict[str, Any] = {}

    def register_adapter(self, name: str, adapter: Any) -> None:
        """Register an LLM adapter."""
        self._adapters[name] = adapter

    def generate(
        self,
        messages: List[Dict[str, str]],
        adapter_name: str = DEFAULT_LLM,
        model: str = DEFAULT_MODEL,
        **kwargs,
    ) -> str:
        """Generate a response using the specified adapter.

        Args:
            messages: List of {"role": ..., "content": ...} dicts
            adapter_name: Which LLM adapter to use
            model: Model name/identifier
            **kwargs: Additional generation parameters

        Returns:
            Generated text response
        """
        adapter = self._get_adapter(adapter_name)
        try:
            return adapter.generate(messages, model, **kwargs)
        except Exception as e:
            raise LLMAdapterError(
                f"Generation failed with adapter '{adapter_name}': {e}"
            ) from e

    def _get_adapter(self, name: str) -> Any:
        """Get or lazy-load an adapter."""
        if name in self._adapters:
            return self._adapters[name]

        # Lazy load
        adapter = self._load_adapter(name)
        self._adapters[name] = adapter
        return adapter

    def _load_adapter(self, name: str) -> Any:
        """Lazy-load an adapter by name."""
        if name == "ollama":
            from cortex.bridges.adapter_ollama import OllamaAdapter
            return OllamaAdapter()
        elif name == "anthropic":
            from cortex.bridges.adapter_anthropic import AnthropicAdapter
            return AnthropicAdapter()
        elif name == "openai":
            from cortex.bridges.adapter_openai import OpenAIAdapter
            return OpenAIAdapter()
        elif name == "generic":
            from cortex.bridges.adapter_generic import GenericAdapter
            return GenericAdapter()
        else:
            raise LLMNotAvailableError(
                f"Unknown adapter '{name}'. Available: {SUPPORTED_LLMS}"
            )

    def health_check(self, adapter_name: str) -> bool:
        """Check if an adapter is healthy."""
        try:
            adapter = self._get_adapter(adapter_name)
            return adapter.health_check()
        except Exception:
            return False

    def list_adapters(self) -> List[str]:
        """List registered/available adapter names."""
        return list(set(list(self._adapters.keys()) + SUPPORTED_LLMS))

    def list_models(self, adapter_name: str) -> List[str]:
        """List available models for an adapter."""
        try:
            adapter = self._get_adapter(adapter_name)
            return adapter.list_models()
        except Exception:
            return []
