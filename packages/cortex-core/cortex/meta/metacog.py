"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — METACOG-X Algorithm                        ║
║  8-Component Metacognitive Scoring Engine                    ║
╚══════════════════════════════════════════════════════════════╝

METACOG-X scores HOW WELL the AI is thinking — not WHAT it's thinking.
Higher = better self-awareness. Lower = cognitive blind spots.

Formula:  METACOG-X = Σ(component_i × weight_i) / Σ(weight_i)

Components:
  1. Confidence Calibration  — Brier score accuracy
  2. Contradiction Density   — contradictions per 100 thoughts (inverted)
  3. Hallucination Rate      — % ungrounded responses (inverted)
  4. Drift Velocity          — accuracy change rate (inverted)
  5. Pattern Depth           — error patterns detected and resolved
  6. Wisdom Ratio            — axioms / total thoughts
  7. Strategy Fitness        — avg success rate of strategies
  8. Growth Rate             — improvement slope
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from cortex.config import (
    METACOG_CONFIDENCE_CALIBRATION,
    METACOG_CONTRADICTION_DENSITY,
    METACOG_HALLUCINATION_RATE,
    METACOG_DRIFT_VELOCITY,
    METACOG_PATTERN_DEPTH,
    METACOG_WISDOM_RATIO,
    METACOG_STRATEGY_FITNESS,
    METACOG_GROWTH_RATE,
    METACOG_TOTAL_WEIGHT,
)


@dataclass
class MetacogComponent:
    """A single component of the METACOG-X score."""
    name: str
    raw_value: float      # 0.0 - 1.0 (1.0 = best)
    weight: float
    description: str = ""

    @property
    def weighted_value(self) -> float:
        return self.raw_value * self.weight


@dataclass
class MetacogBreakdown:
    """Full breakdown of a METACOG-X score computation."""
    components: List[MetacogComponent] = field(default_factory=list)
    total_score: float = 0.0
    health_label: str = ""
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_score": round(self.total_score, 4),
            "health_label": self.health_label,
            "components": {
                c.name: {
                    "raw": round(c.raw_value, 4),
                    "weight": c.weight,
                    "weighted": round(c.weighted_value, 4),
                }
                for c in self.components
            },
            "recommendations": self.recommendations,
        }


def metacog_score(
    calibration_score: float = 1.0,
    contradiction_score: float = 1.0,
    hallucination_score: float = 1.0,
    drift_score: float = 1.0,
    pattern_score: float = 1.0,
    wisdom_score: float = 0.0,
    strategy_score: float = 0.5,
    growth_score: float = 0.5,
) -> float:
    """Compute the METACOG-X composite score.

    All inputs should be 0.0-1.0 where 1.0 = best.

    Formula: METACOG-X = Σ(component_i × weight_i) / Σ(weight_i)

    Returns: float between 0.0 and 1.0
    """
    weighted_sum = (
        calibration_score * METACOG_CONFIDENCE_CALIBRATION +
        contradiction_score * METACOG_CONTRADICTION_DENSITY +
        hallucination_score * METACOG_HALLUCINATION_RATE +
        drift_score * METACOG_DRIFT_VELOCITY +
        pattern_score * METACOG_PATTERN_DEPTH +
        wisdom_score * METACOG_WISDOM_RATIO +
        strategy_score * METACOG_STRATEGY_FITNESS +
        growth_score * METACOG_GROWTH_RATE
    )
    return max(0.0, min(1.0, weighted_sum / METACOG_TOTAL_WEIGHT))


def metacog_breakdown(
    calibration_score: float = 1.0,
    contradiction_score: float = 1.0,
    hallucination_score: float = 1.0,
    drift_score: float = 1.0,
    pattern_score: float = 1.0,
    wisdom_score: float = 0.0,
    strategy_score: float = 0.5,
    growth_score: float = 0.5,
) -> MetacogBreakdown:
    """Compute detailed METACOG-X breakdown with per-component analysis.

    Returns MetacogBreakdown with score, label, components, and recommendations.
    """
    components = [
        MetacogComponent(
            name="confidence_calibration",
            raw_value=_clamp(calibration_score),
            weight=METACOG_CONFIDENCE_CALIBRATION,
            description="How well self-assessed confidence matches actual accuracy",
        ),
        MetacogComponent(
            name="contradiction_density",
            raw_value=_clamp(contradiction_score),
            weight=METACOG_CONTRADICTION_DENSITY,
            description="Rate of self-contradictions (1.0 = no contradictions)",
        ),
        MetacogComponent(
            name="hallucination_rate",
            raw_value=_clamp(hallucination_score),
            weight=METACOG_HALLUCINATION_RATE,
            description="Proportion of evidence-backed responses (1.0 = fully grounded)",
        ),
        MetacogComponent(
            name="drift_velocity",
            raw_value=_clamp(drift_score),
            weight=METACOG_DRIFT_VELOCITY,
            description="Stability of accuracy over time (1.0 = stable)",
        ),
        MetacogComponent(
            name="pattern_depth",
            raw_value=_clamp(pattern_score),
            weight=METACOG_PATTERN_DEPTH,
            description="Error patterns detected and resolved (1.0 = all resolved)",
        ),
        MetacogComponent(
            name="wisdom_ratio",
            raw_value=_clamp(wisdom_score),
            weight=METACOG_WISDOM_RATIO,
            description="Ratio of crystallized wisdom to total thoughts",
        ),
        MetacogComponent(
            name="strategy_fitness",
            raw_value=_clamp(strategy_score),
            weight=METACOG_STRATEGY_FITNESS,
            description="Average success rate of active strategies",
        ),
        MetacogComponent(
            name="growth_rate",
            raw_value=_clamp(growth_score),
            weight=METACOG_GROWTH_RATE,
            description="Improvement slope over recent sessions",
        ),
    ]

    total = metacog_score(
        calibration_score, contradiction_score, hallucination_score,
        drift_score, pattern_score, wisdom_score,
        strategy_score, growth_score,
    )

    label = metacog_health_label(total)
    recommendations = _generate_recommendations(components)

    return MetacogBreakdown(
        components=components,
        total_score=total,
        health_label=label,
        recommendations=recommendations,
    )


def metacog_health_label(score: float) -> str:
    """Convert METACOG-X score to human-readable health label.

    Score ranges:
      0.85 - 1.00 → "excellent"   (highly self-aware)
      0.70 - 0.85 → "good"        (solid self-awareness)
      0.50 - 0.70 → "developing"  (growing awareness)
      0.30 - 0.50 → "emerging"    (limited awareness)
      0.00 - 0.30 → "nascent"     (minimal awareness)
    """
    if score >= 0.85:
        return "excellent"
    elif score >= 0.70:
        return "good"
    elif score >= 0.50:
        return "developing"
    elif score >= 0.30:
        return "emerging"
    else:
        return "nascent"


def _generate_recommendations(components: List[MetacogComponent]) -> List[str]:
    """Generate improvement recommendations based on weak components."""
    recs = []
    for comp in components:
        if comp.raw_value < 0.4:
            recs.append(f"CRITICAL: {comp.name} is at {comp.raw_value:.0%} — {comp.description}")
        elif comp.raw_value < 0.6:
            recs.append(f"IMPROVE: {comp.name} at {comp.raw_value:.0%} — needs attention")
    return recs


def _clamp(value: float) -> float:
    """Clamp value to [0.0, 1.0]."""
    return max(0.0, min(1.0, value))
