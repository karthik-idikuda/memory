"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Thought Trace                              ║
║  Transparent thinking logger — shows HOW the AI thinks       ║
╚══════════════════════════════════════════════════════════════╝

Every response includes a ThoughtTrace showing:
  - Each reasoning step
  - Memories recalled
  - Causal chains activated
  - Metacognitive flags
  - Past errors avoided
  - Axioms applied
  - Strategy used
  - Growth delta
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from cortex.config import TRACE_MAX_DEPTH


@dataclass
class TraceStep:
    """A single step in the thought trace."""
    step_number: int
    action: str            # "recall", "reason", "generate", "monitor", etc.
    description: str
    duration_ms: float = 0.0
    confidence: float = 0.0
    flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_number,
            "action": self.action,
            "description": self.description,
            "duration_ms": round(self.duration_ms, 1),
            "confidence": round(self.confidence, 2),
            "flags": self.flags,
        }


@dataclass
class ThoughtTrace:
    """Complete trace of how the AI produced a response.

    This is the transparency layer — users can see exactly how
    the AI arrived at its answer.
    """
    trace_id: str = ""
    steps: List[TraceStep] = field(default_factory=list)
    memories_recalled: int = 0
    chains_activated: int = 0
    confidence: float = 0.0
    metacog_flags: List[str] = field(default_factory=list)
    past_errors_avoided: List[str] = field(default_factory=list)
    axioms_applied: List[str] = field(default_factory=list)
    strategy_used: str = ""
    growth_delta: float = 0.0
    zone: str = ""
    total_time_ms: float = 0.0
    created_at: float = 0.0

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

    def add_step(
        self,
        action: str,
        description: str,
        duration_ms: float = 0.0,
        confidence: float = 0.0,
        flags: Optional[List[str]] = None,
    ) -> TraceStep:
        """Add a reasoning step to the trace."""
        step = TraceStep(
            step_number=len(self.steps) + 1,
            action=action,
            description=description,
            duration_ms=duration_ms,
            confidence=confidence,
            flags=flags or [],
        )
        if len(self.steps) < TRACE_MAX_DEPTH:
            self.steps.append(step)
        self.total_time_ms += duration_ms
        return step

    def flag(self, flag: str) -> None:
        """Add a metacognitive flag."""
        if flag not in self.metacog_flags:
            self.metacog_flags.append(flag)

    def record_memory_recall(self, count: int) -> None:
        """Record how many memories were recalled."""
        self.memories_recalled = count

    def record_chains(self, count: int) -> None:
        """Record how many causal chains were activated."""
        self.chains_activated = count

    def record_error_avoided(self, error: str) -> None:
        """Record a past error that was successfully avoided."""
        self.past_errors_avoided.append(error)

    def record_axiom_applied(self, axiom: str) -> None:
        """Record a wisdom axiom that was applied."""
        self.axioms_applied.append(axiom)

    def finalize(self, confidence: float, zone: str, growth_delta: float = 0.0) -> None:
        """Finalize the trace with final metrics."""
        self.confidence = confidence
        self.zone = zone
        self.growth_delta = growth_delta

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def has_flags(self) -> bool:
        return len(self.metacog_flags) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "steps": [s.to_dict() for s in self.steps],
            "memories_recalled": self.memories_recalled,
            "chains_activated": self.chains_activated,
            "confidence": round(self.confidence, 2),
            "metacog_flags": self.metacog_flags,
            "past_errors_avoided": self.past_errors_avoided,
            "axioms_applied": self.axioms_applied,
            "strategy_used": self.strategy_used,
            "growth_delta": round(self.growth_delta, 4),
            "zone": self.zone,
            "total_time_ms": round(self.total_time_ms, 1),
        }

    def format_compact(self) -> str:
        """Format trace as a compact string for display.

        Example:
          ⟨ ·recall(23 memories) ·reason(5 chains) ·generate(87% conf)
            ·monitor[🛡✓ →→] ·respond ⟩ 142ms
        """
        parts = ["⟨"]
        for step in self.steps:
            flags_str = ""
            if step.flags:
                flags_str = f"[{' '.join(step.flags)}]"
            parts.append(f"·{step.action}{flags_str}")
        parts.append(f"⟩ {self.total_time_ms:.0f}ms")
        return " ".join(parts)

    def format_detailed(self) -> str:
        """Format trace as detailed multi-line string."""
        lines = [f"═══ ThoughtTrace {self.trace_id[:8]} ═══"]
        for step in self.steps:
            line = f"  {step.step_number}. [{step.action}] {step.description}"
            if step.flags:
                line += f" → {', '.join(step.flags)}"
            if step.duration_ms > 0:
                line += f" ({step.duration_ms:.0f}ms)"
            lines.append(line)

        lines.append(f"  memories: {self.memories_recalled} | "
                     f"chains: {self.chains_activated} | "
                     f"confidence: {self.confidence:.0%} | "
                     f"zone: {self.zone}")

        if self.metacog_flags:
            lines.append(f"  flags: {', '.join(self.metacog_flags)}")
        if self.past_errors_avoided:
            lines.append(f"  avoided: {', '.join(self.past_errors_avoided[:3])}")
        if self.axioms_applied:
            lines.append(f"  wisdom: {', '.join(self.axioms_applied[:3])}")

        lines.append(f"  total: {self.total_time_ms:.0f}ms | growth: {self.growth_delta:+.2%}")
        return "\n".join(lines)


class TraceLogger:
    """Manages thought traces across the session."""

    def __init__(self):
        self.traces: List[ThoughtTrace] = []

    def new_trace(self) -> ThoughtTrace:
        """Create and register a new trace."""
        from cortex.core.integrity import generate_id
        trace = ThoughtTrace(trace_id=generate_id("trace"))
        self.traces.append(trace)
        return trace

    @property
    def trace_count(self) -> int:
        return len(self.traces)

    def recent(self, count: int = 5) -> List[ThoughtTrace]:
        """Get recent traces."""
        return self.traces[-count:]

    def avg_confidence(self) -> float:
        """Average confidence across all traces."""
        if not self.traces:
            return 0.0
        return sum(t.confidence for t in self.traces) / len(self.traces)

    def avg_time_ms(self) -> float:
        """Average response time across all traces."""
        if not self.traces:
            return 0.0
        return sum(t.total_time_ms for t in self.traces) / len(self.traces)
