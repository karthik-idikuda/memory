"""CORTEX-X — Generic OpenAI-compatible Adapter (stdlib only)."""

from __future__ import annotations
import json
from typing import List, Dict, Any
from cortex.bridges.adapter_base import BaseLLMAdapter
from cortex.exceptions import LLMAdapterError


class GenericAdapter(BaseLLMAdapter):
    """Adapter for any OpenAI-compatible API endpoint. Uses stdlib urllib only."""

    def __init__(self, base_url: str = "http://localhost:8080/v1", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def generate(self, messages: List[Dict[str, str]], model: str = "default", **kwargs) -> str:
        import urllib.request
        url = f"{self.base_url}/chat/completions"
        payload = json.dumps({"model": model, "messages": messages, **kwargs}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise LLMAdapterError(f"Generic adapter error: {e}") from e

    def health_check(self) -> bool:
        import urllib.request
        try:
            with urllib.request.urlopen(f"{self.base_url}/models", timeout=5):
                return True
        except Exception:
            return False

    def list_models(self) -> List[str]:
        import urllib.request
        try:
            with urllib.request.urlopen(f"{self.base_url}/models", timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m.get("id", "") for m in data.get("data", [])]
        except Exception:
            return ["default"]
