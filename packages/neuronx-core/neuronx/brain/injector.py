"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Context Injector                       ║
║  NRNLANG-Ω: @> PUSH_TO_AI — format for LLM injection    ║
╚══════════════════════════════════════════════════════════╝
"""

from typing import List, Tuple

from neuronx.config import PROMPT_SYSTEM
from neuronx.core.node import EngramNode


class ContextInjector:
    """
    NRNLANG-Ω: INJECTOR — formats retrieved memories for AI context injection.
    """

    @staticmethod
    def format_memory(engram: EngramNode, rank: int) -> str:
        """Format a single memory for injection."""
        age_days = engram.age_days
        if age_days < 1:
            age_str = "today"
        elif age_days < 7:
            age_str = f"{int(age_days)}d ago"
        elif age_days < 30:
            age_str = f"{int(age_days/7)}w ago"
        elif age_days < 365:
            age_str = f"{int(age_days/30)}mo ago"
        else:
            age_str = f"{int(age_days/365)}y ago"

        zone = engram.zone[0] if engram.zone else "?"
        conf = f"{engram.confidence:.0%}"
        anchor = " ◆ANCHOR" if engram.is_anchor else ""

        return (
            f"  [{rank}] [{zone}] {engram.raw} "
            f"(conf:{conf}, {age_str}{anchor})"
        )

    @staticmethod
    def format_memories(
        memories: List[Tuple[EngramNode, float]],
    ) -> str:
        """Format list of (engram, score) tuples for AI context."""
        if not memories:
            return "(No relevant memories found)"

        lines = []
        for i, (engram, score) in enumerate(memories, 1):
            lines.append(ContextInjector.format_memory(engram, i))
        return "\n".join(lines)

    @staticmethod
    def build_system_prompt(
        memories: List[Tuple[EngramNode, float]],
    ) -> str:
        """Build complete system prompt with memory context."""
        context = ContextInjector.format_memories(memories)
        return PROMPT_SYSTEM.format(
            count=len(memories),
            memory_context=context,
        )

    @staticmethod
    def inject(memories: List[Tuple[EngramNode, float]]) -> str:
        """Shorthand: build system prompt addition from memories."""
        return ContextInjector.build_system_prompt(memories)
