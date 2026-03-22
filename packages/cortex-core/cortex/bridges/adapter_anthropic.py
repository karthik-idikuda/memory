"""CORTEX-X — Anthropic (Claude) Adapter."""

from __future__ import annotations
from typing import List, Dict, Any
from cortex.bridges.adapter_base import BaseLLMAdapter
from cortex.exceptions import LLMAdapterError


class AnthropicAdapter(BaseLLMAdapter):
    """Adapter for Anthropic's Claude API (requires `anthropic` package)."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key or None)
            except ImportError:
                raise LLMAdapterError("Install anthropic: pip install cortex-core[anthropic]")
        return self._client

    def generate(self, messages: List[Dict[str, str]], model: str = "claude-sonnet-4-20250514", **kwargs) -> str:
        client = self._get_client()
        system_msg = ""
        chat_msgs = []
        for m in messages:
            if m["role"] == "system":
                system_msg += m["content"] + "\n"
            else:
                chat_msgs.append(m)
        try:
            response = client.messages.create(
                model=model, max_tokens=4096,
                system=system_msg.strip() if system_msg else "",
                messages=chat_msgs, **kwargs,
            )
            return response.content[0].text
        except Exception as e:
            raise LLMAdapterError(f"Anthropic error: {e}") from e

    def health_check(self) -> bool:
        try:
            self._get_client()
            return True
        except Exception:
            return False

    def list_models(self) -> List[str]:
        return ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-3-5-haiku-20241022"]
