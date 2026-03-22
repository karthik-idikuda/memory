"""CORTEX-X — OpenAI Adapter."""

from __future__ import annotations
from typing import List, Dict, Any
from cortex.bridges.adapter_base import BaseLLMAdapter
from cortex.exceptions import LLMAdapterError


class OpenAIAdapter(BaseLLMAdapter):
    """Adapter for OpenAI's GPT API (requires `openai` package)."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key or None)
            except ImportError:
                raise LLMAdapterError("Install openai: pip install cortex-core[openai]")
        return self._client

    def generate(self, messages: List[Dict[str, str]], model: str = "gpt-4o", **kwargs) -> str:
        client = self._get_client()
        try:
            response = client.chat.completions.create(model=model, messages=messages, **kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            raise LLMAdapterError(f"OpenAI error: {e}") from e

    def health_check(self) -> bool:
        try:
            self._get_client()
            return True
        except Exception:
            return False

    def list_models(self) -> List[str]:
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
