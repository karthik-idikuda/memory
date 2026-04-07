"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Integration Base                       ║
║  NRNLANG-Ω: INTEGRATIONS — connect to any AI provider   ║
╚══════════════════════════════════════════════════════════╝
"""

from typing import List, Dict, Any

from neuronx.brain.neuron import NeuronBrain


class BaseIntegration:
    """
    Base class for AI provider integrations.
    Subclass for OpenAI, Anthropic, LangChain, etc.
    """

    def __init__(self, brain: NeuronBrain, top_k: int = 7):
        self.brain = brain
        self.top_k = top_k

    def pre_chat(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        NRNLANG-Ω: @> PRE_CHAT — inject memories into system prompt.

        Takes the message list (format: [{"role": "...", "content": "..."}])
        and injects a system message with relevant memories.
        """
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        if not last_user_msg:
            return messages

        ctx = self.brain.get_context(last_user_msg, top_k=self.top_k, remember=True)
        memory_msg = {
            "role": "system",
            "content": ctx.system_prompt_addition,
        }

        # Insert after first system message, or at start
        result = list(messages)
        for i, msg in enumerate(result):
            if msg.get("role") == "system":
                result.insert(i + 1, memory_msg)
                return result
        result.insert(0, memory_msg)
        return result

    def post_chat(self, assistant_response: str) -> None:
        """
        NRNLANG-Ω: POST_CHAT — extract memories from AI response.
        """
        self.brain.remember(assistant_response, source="inference")

    def end_session(self) -> None:
        """End the session and save."""
        self.brain.end_session()


class GenericIntegration(BaseIntegration):
    """Generic integration for any LLM provider using messages format."""
    pass


class OpenAIIntegration(BaseIntegration):
    """Integration adapter for OpenAI API."""

    def create_chat_params(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Build OpenAI chat completion parameters with memory injection."""
        enriched = self.pre_chat(messages)
        return {
            "model": model,
            "messages": enriched,
            **kwargs,
        }


class AnthropicIntegration(BaseIntegration):
    """Integration adapter for Anthropic API."""

    def create_chat_params(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-sonnet-4-20250514",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Build Anthropic message params with memory injection."""
        enriched = self.pre_chat(messages)
        system_content = ""
        user_messages = []
        for msg in enriched:
            if msg["role"] == "system":
                system_content += msg["content"] + "\n"
            else:
                user_messages.append(msg)
        return {
            "model": model,
            "system": system_content.strip(),
            "messages": user_messages,
            **kwargs,
        }


class LangChainIntegration(BaseIntegration):
    """Integration adapter for LangChain."""

    def get_memory_retriever(self):
        """Return a function that LangChain can use as a retriever."""
        def retriever(query: str) -> List[str]:
            results = self.brain.recall(query, top_k=self.top_k)
            return [e.raw for e, _ in results]
        return retriever


class LiteLLMIntegration(BaseIntegration):
    """Integration adapter for LiteLLM (any model via unified API)."""

    def create_chat_params(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        enriched = self.pre_chat(messages)
        return {"model": model, "messages": enriched, **kwargs}
