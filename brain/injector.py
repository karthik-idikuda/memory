"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Memory Context Injector                ║
║  NRNLANG-Ω: @> PUSH_TO_AI — inject memories into prompt  ║
╚══════════════════════════════════════════════════════════╝

Formats retrieved memories for AI system prompt injection.
Groups by zone (HOT first), includes confidence and age.
"""

import time
import logging

from core.node import (
    Engram, ZONE_HOT, ZONE_WARM, ZONE_COLD, ZONE_SILENT, ZONE_ANCHOR,
)

logger = logging.getLogger("NEURONX.INJECTOR")

# Zone display format
ZONE_LABELS = {
    ZONE_HOT: "🔥 HOT",
    ZONE_ANCHOR: "⚓ ANCHOR",
    ZONE_WARM: "🌡 WARM",
    ZONE_COLD: "❄ COLD",
    ZONE_SILENT: "👻 SILENT",
}

ZONE_ORDER = [ZONE_HOT, ZONE_ANCHOR, ZONE_WARM, ZONE_COLD, ZONE_SILENT]


def format_one_memory(engram: Engram, score: float) -> str:
    """
    Format one memory for injection into AI context.

    Format: [ZONE  SCORE] "text" (conf:X.XX, Xd ago)
    """
    zone_label = ZONE_LABELS.get(engram.zone, engram.zone)
    age = f"{engram.age_days:.0f}"
    reawaken_tag = " [REAWAKENED]" if engram.zone in (ZONE_HOT, ZONE_WARM) and engram.age_days > 90 else ""

    return (
        f"[{zone_label} {score:.2f}] "
        f'"{engram.raw}" '
        f"(conf:{engram.confidence:.2f}, {age}d ago)"
        f"{reawaken_tag}"
    )


def format_memory_context(
    results: list[tuple[Engram, float]],
    max_memories: int = 7,
) -> str:
    """
    NRNLANG-Ω: @7 TOP_SEVEN @> AI — format top memories for injection.

    Groups by zone: HOT memories first, then WARM, then others.
    Includes score, confidence, and age for each memory.
    """
    if not results:
        return "(No memories stored yet — this is the first conversation)"

    # Sort by zone priority, then by score
    def sort_key(item):
        engram, score = item
        zone_rank = ZONE_ORDER.index(engram.zone) if engram.zone in ZONE_ORDER else 5
        return (zone_rank, -score)

    sorted_results = sorted(results[:max_memories], key=sort_key)

    lines = []
    current_zone = None

    for engram, score in sorted_results:
        # Group header when zone changes
        if engram.zone != current_zone:
            current_zone = engram.zone
            zone_label = ZONE_LABELS.get(current_zone, current_zone)
            lines.append(f"── {zone_label} Zone ──")

        lines.append(format_one_memory(engram, score))

    return "\n".join(lines)


def inject_into_prompt(
    system_prompt_template: str,
    results: list[tuple[Engram, float]],
    count: int = None,
) -> str:
    """
    Build the final system prompt with memories injected.

    Takes the MASTER_SYSTEM_PROMPT template and inserts the
    formatted memory context.
    """
    if count is None:
        count = len(results)

    memory_context = format_memory_context(results)

    return system_prompt_template.format(
        memories=memory_context,
        count=count,
    )
