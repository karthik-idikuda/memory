"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Growth Engine                              ║
║  5-dimensional self-improvement tracking                    ║
╚══════════════════════════════════════════════════════════════╝

Tracks improvement across 5 dimensions:
  1. accuracy_delta      — is the AI getting more accurate?
  2. calibration_delta   — is confidence calibration improving?
  3. hallucination_delta — are hallucinations decreasing?
  4. strategy_delta      — are strategies getting better?
  5. wisdom_delta        — is wisdom accumulating?

GrowthScore = Σ(delta_i × weight_i) / Σ(weight_i)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from cortex.config import (
    GROWTH_MEASUREMENT_INTERVAL,
    GROWTH_DIMENSION_WEIGHTS,
    GROWTH_TOTAL_WEIGHT,
)


@dataclass
class GrowthMeasurement:
    """A single growth measurement snapshot."""
    timestamp: float
    accuracy: float
    calibration: float
    hallucination: float
    strategy: float
    wisdom: float
    growth_score: float = 0.0
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "accuracy": round(self.accuracy, 4),
            "calibration": round(self.calibration, 4),
            "hallucination": round(self.hallucination, 4),
            "strategy": round(self.strategy, 4),
            "wisdom": round(self.wisdom, 4),
            "growth_score": round(self.growth_score, 4),
            "label": self.label,
        }


class GrowthEngine:
    """5-dimensional self-improvement tracker.

    Measures improvement trends across metacognitive dimensions.
    """

    def __init__(self):
        self.measurements: List[GrowthMeasurement] = []
        self.interaction_count: int = 0

    def measure(
        self,
        accuracy: float = 0.5,
        calibration: float = 0.5,
        hallucination: float = 0.5,
        strategy: float = 0.5,
        wisdom: float = 0.0,
    ) -> float:
        """Take a growth measurement.

        Args:
            accuracy: Current accuracy score (0-1)
            calibration: Current calibration score (0-1)
            hallucination: Current hallucination shield score (0-1)
            strategy: Current strategy fitness score (0-1)
            wisdom: Current wisdom accumulation score (0-1)

        Returns:
            Growth score for this measurement
        """
        self.interaction_count += 1

        measurement = GrowthMeasurement(
            timestamp=time.time(),
            accuracy=accuracy,
            calibration=calibration,
            hallucination=hallucination,
            strategy=strategy,
            wisdom=wisdom,
        )

        # Compute growth (delta from previous measurement)
        if self.measurements:
            prev = self.measurements[-1]
            deltas = {
                "accuracy_delta": accuracy - prev.accuracy,
                "calibration_delta": calibration - prev.calibration,
                "hallucination_delta": hallucination - prev.hallucination,
                "strategy_delta": strategy - prev.strategy,
                "wisdom_delta": wisdom - prev.wisdom,
            }
            growth_score = sum(
                deltas[k] * GROWTH_DIMENSION_WEIGHTS[k]
                for k in deltas
            ) / GROWTH_TOTAL_WEIGHT

            measurement.growth_score = growth_score
            measurement.label = self._label(growth_score)
        else:
            measurement.growth_score = 0.0
            measurement.label = "baseline"

        self.measurements.append(measurement)
        return measurement.growth_score

    def _label(self, score: float) -> str:
        """Growth label from score."""
        if score > 0.05:
            return "growing"
        elif score > 0.01:
            return "improving"
        elif score > -0.01:
            return "stable"
        elif score > -0.05:
            return "declining"
        else:
            return "regressing"

    @property
    def current_score(self) -> float:
        """Most recent growth score."""
        if not self.measurements:
            return 0.0
        return self.measurements[-1].growth_score

    @property
    def trend(self) -> str:
        """Overall trend from recent measurements."""
        if len(self.measurements) < 3:
            return "insufficient_data"
        recent = self.measurements[-5:]
        avg_score = sum(m.growth_score for m in recent) / len(recent)
        return self._label(avg_score)

    @property
    def growth_symbol(self) -> str:
        """📈 📊 📉"""
        score = self.current_score
        if score > 0.01:
            return "📈"
        elif score > -0.01:
            return "📊"
        else:
            return "📉"

    @property
    def total_measurements(self) -> int:
        return len(self.measurements)

    def history(self, count: int = 10) -> List[GrowthMeasurement]:
        """Get recent measurements."""
        return self.measurements[-count:]

    def dimension_trends(self) -> Dict[str, str]:
        """Trend per dimension."""
        if len(self.measurements) < 2:
            return {}
        recent = self.measurements[-5:]
        first = recent[0]
        last = recent[-1]
        return {
            "accuracy": self._label(last.accuracy - first.accuracy),
            "calibration": self._label(last.calibration - first.calibration),
            "hallucination": self._label(last.hallucination - first.hallucination),
            "strategy": self._label(last.strategy - first.strategy),
            "wisdom": self._label(last.wisdom - first.wisdom),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_score": round(self.current_score, 4),
            "trend": self.trend,
            "total_measurements": self.total_measurements,
            "interaction_count": self.interaction_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GrowthEngine":
        engine = cls()
        engine.interaction_count = data.get("interaction_count", 0)
        return engine
