"""CORTEX-X — CORTEXLANG-Ω Emitter (Operations → Notation)."""

from __future__ import annotations
from typing import Dict, Any, Optional
from cortex.config import (
    CORTEXLANG_META_SYMBOLS, CORTEXLANG_THOUGHT_SYMBOLS,
    CORTEXLANG_ZONE_SYMBOLS, CORTEXLANG_LINK_SYMBOLS,
)


def emit_thought(
    thought_type: str, zone: str, confidence: float,
    evidence_ratio: float, content: str,
) -> str:
    """Emit CORTEXLANG notation for a thought.

    Example output: ◎ ⚡ ⊕⊕ 🛡✓ "How to sort a list in Python"
    """
    parts = []

    # Type symbol
    type_sym = CORTEXLANG_THOUGHT_SYMBOLS.get(thought_type.upper(), "◎")
    parts.append(type_sym)

    # Zone symbol
    zone_sym = CORTEXLANG_ZONE_SYMBOLS.get(zone, "")
    if zone_sym:
        parts.append(zone_sym)

    # Confidence
    if confidence >= 0.85:
        parts.append(CORTEXLANG_META_SYMBOLS["CONFIDENCE_HIGH"])
    elif confidence >= 0.50:
        parts.append(CORTEXLANG_META_SYMBOLS["CONFIDENCE_MED"])
    else:
        parts.append(CORTEXLANG_META_SYMBOLS["CONFIDENCE_LOW"])

    # Shield
    if evidence_ratio >= 0.7:
        parts.append(CORTEXLANG_META_SYMBOLS["HALLUCINATION_SAFE"])
    elif evidence_ratio >= 0.4:
        parts.append(CORTEXLANG_META_SYMBOLS["HALLUCINATION_WARN"])
    else:
        parts.append(CORTEXLANG_META_SYMBOLS["HALLUCINATION_CRIT"])

    # Content snippet
    snippet = content[:40].replace("\n", " ").replace('"', "'")
    parts.append(f'"{snippet}"')

    return " ".join(parts)


def emit_trace(steps: list, total_ms: float) -> str:
    """Emit compact trace notation.

    Example: ⟨ ·recall ·reason ·generate ·monitor ⟩ 142ms
    """
    trace_parts = [CORTEXLANG_META_SYMBOLS["TRACE_START"]]
    for step in steps:
        name = step.get("action", step) if isinstance(step, dict) else str(step)
        trace_parts.append(f"{CORTEXLANG_META_SYMBOLS['TRACE_STEP']}{name}")
    trace_parts.append(f"{CORTEXLANG_META_SYMBOLS['TRACE_END']} {total_ms:.0f}ms")
    return " ".join(trace_parts)


def emit_growth(score: float) -> str:
    """Emit growth symbol."""
    if score > 0.01:
        return CORTEXLANG_META_SYMBOLS["GROWTH_UP"]
    elif score > -0.01:
        return CORTEXLANG_META_SYMBOLS["GROWTH_FLAT"]
    else:
        return CORTEXLANG_META_SYMBOLS["GROWTH_DOWN"]


def emit_link(from_id: str, to_id: str, link_type: str) -> str:
    """Emit a link notation."""
    sym = CORTEXLANG_LINK_SYMBOLS.get(link_type, "→")
    return f"{from_id[:8]} {sym} {to_id[:8]}"


def emit_strategy_result(success: bool) -> str:
    """Emit strategy outcome symbol."""
    return CORTEXLANG_META_SYMBOLS["STRATEGY_WIN" if success else "STRATEGY_FAIL"]


def emit_drift(direction: str) -> str:
    """Emit drift symbol."""
    if direction == "stable":
        return CORTEXLANG_META_SYMBOLS["DRIFT_STABLE"]
    elif direction == "improving":
        return CORTEXLANG_META_SYMBOLS["DRIFT_DETECTED"]
    else:
        return CORTEXLANG_META_SYMBOLS["DRIFT_CRITICAL"]
