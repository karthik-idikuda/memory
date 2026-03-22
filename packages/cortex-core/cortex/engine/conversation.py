"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Conversation Context Manager               ║
║  Manages context window with auto-summarization              ║
╚══════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional

from cortex.config import (
    MAX_CONTEXT_TOKENS,
    CONVERSATION_SUMMARY_THRESHOLD,
)


class ConversationManager:
    """Manages conversation history with token-aware context window.

    Features:
      - Maintains rolling conversation history
      - Auto-summarizes old messages when context is too large
      - Injects relevant memories and metacognitive context
    """

    def __init__(self, max_tokens: int = MAX_CONTEXT_TOKENS):
        self.max_tokens = max_tokens
        self.turns: List[Dict[str, str]] = []
        self.summaries: List[str] = []
        self.total_turns: int = 0

    def add_turn(self, user_msg: str, assistant_msg: str) -> None:
        """Add a user-assistant turn to history."""
        self.turns.append({"role": "user", "content": user_msg})
        self.turns.append({"role": "assistant", "content": assistant_msg})
        self.total_turns += 1

        # Auto-summarize if too many turns
        if len(self.turns) > CONVERSATION_SUMMARY_THRESHOLD * 2:
            self._summarize_oldest()

    def get_context_messages(self) -> List[Dict[str, str]]:
        """Get conversation messages that fit within token budget."""
        messages = []

        # Add summary context if exists
        if self.summaries:
            summary = " | ".join(self.summaries[-3:])
            messages.append({
                "role": "system",
                "content": f"[Previous conversation summary: {summary}]"
            })

        # Add recent turns (most relevant)
        estimated_tokens = sum(
            self._estimate_tokens(t["content"]) for t in self.turns
        )

        if estimated_tokens <= self.max_tokens * 0.6:
            messages.extend(self.turns)
        else:
            # Take only recent turns that fit
            budget = int(self.max_tokens * 0.6)
            for turn in reversed(self.turns):
                tokens = self._estimate_tokens(turn["content"])
                if budget - tokens < 0:
                    break
                messages.insert(0 if not self.summaries else 1, turn)
                budget -= tokens

        return messages

    def _summarize_oldest(self) -> None:
        """Summarize and remove the oldest turns."""
        if len(self.turns) < 10:
            return

        # Take first 6 messages (3 turns) and summarize
        oldest = self.turns[:6]
        summary_parts = []
        for msg in oldest:
            snippet = msg["content"][:80].replace("\n", " ")
            summary_parts.append(f"{msg['role']}: {snippet}")
        summary = " → ".join(summary_parts)
        self.summaries.append(summary)

        # Remove summarized turns
        self.turns = self.turns[6:]

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation: ~4 chars per token."""
        return len(text) // 4

    def clear(self) -> None:
        """Clear conversation history."""
        self.turns.clear()
        self.summaries.clear()

    @property
    def turn_count(self) -> int:
        return self.total_turns

    @property
    def message_count(self) -> int:
        return len(self.turns)
