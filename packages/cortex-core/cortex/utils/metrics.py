"""CORTEX-X — Brain Health Metrics."""

from __future__ import annotations
from typing import Dict, Any


def brain_health(
    thought_count: int, wisdom_count: int, active_patterns: int,
    calibration_score: float, hallucination_score: float,
    drift_score: float, growth_score: float,
) -> Dict[str, Any]:
    """Compute overall brain health metrics."""
    # Simple weighted average
    health = (
        calibration_score * 0.25 +
        hallucination_score * 0.25 +
        drift_score * 0.15 +
        growth_score * 0.10 +
        min(wisdom_count / 50, 1.0) * 0.10 +
        max(0, 1.0 - active_patterns * 0.1) * 0.15
    )

    if health >= 0.85:
        label = "excellent"
    elif health >= 0.70:
        label = "healthy"
    elif health >= 0.50:
        label = "developing"
    elif health >= 0.30:
        label = "needs_attention"
    else:
        label = "critical"

    return {
        "score": round(health, 4),
        "label": label,
        "total_thoughts": thought_count,
        "wisdom_count": wisdom_count,
        "active_patterns": active_patterns,
    }


def format_metrics_line(stats: Dict[str, Any]) -> str:
    """Format a compact metrics line for CLI display."""
    return (
        f"thoughts: {stats.get('total_thoughts', 0)} | "
        f"wisdom: {stats.get('wisdom_count', 0)} | "
        f"health: {stats.get('label', '?')} ({stats.get('score', 0):.0%})"
    )
