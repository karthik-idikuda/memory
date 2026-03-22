"""CORTEX-X — Ollama Adapter (local LLM via REST API)."""

from __future__ import annotations
import json
from typing import List, Dict, Any
from cortex.bridges.adapter_base import BaseLLMAdapter
from cortex.exceptions import LLMAdapterError, LLMTimeoutError


class OllamaAdapter(BaseLLMAdapter):
    """Adapter for Ollama local LLM server."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    def generate(self, messages: List[Dict[str, str]], model: str = "llama3.2", **kwargs) -> str:
        import urllib.request
        import urllib.error
        url = f"{self.base_url}/api/chat"
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "stream": False,
            **kwargs,
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("message", {}).get("content", "")
        except urllib.error.URLError as e:
            raise LLMAdapterError(f"Ollama connection failed: {e}") from e

    def health_check(self) -> bool:
        import urllib.request
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        import urllib.request
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            return []
