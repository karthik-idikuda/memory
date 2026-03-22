"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Drift Detector                             ║
║  Dual-EWMA Cognitive Drift Detection                        ║
╚══════════════════════════════════════════════════════════════╝

Detects when the AI's thinking quality is changing over time.
Uses Dual Exponentially Weighted Moving Average (EWMA) to compare
recent performance against historical baseline.

Algorithm:
  EWMA_recent = smoothed average of last 20 interactions
  EWMA_historical = smoothed average of last 200 interactions
  drift_signal = |EWMA_recent - EWMA_historical|
  If drift_signal > threshold → trigger self-audit
"""

from __future__ import annotations

import time
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from cortex.config import (
    DRIFT_EWMA_ALPHA, DRIFT_THRESHOLD,
    DRIFT_WINDOW_RECENT, DRIFT_WINDOW_HISTORICAL,
)


@dataclass
class DriftMeasurement:
    """A single drift measurement snapshot."""
    ewma_recent: float
    ewma_historical: float
    drift_signal: float
    is_drifting: bool
    timestamp: float = 0.0
    direction: str = "stable"   # "improving", "stable", "degrading"

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class DriftDetector:
    """Dual-EWMA cognitive drift detector.

    Maintains two exponentially weighted moving averages:
    - Recent: short window (last ~20 interactions)
    - Historical: long window (last ~200 interactions)

    When these diverge beyond threshold, drift is detected.
    """

    def __init__(
        self,
        alpha: float = DRIFT_EWMA_ALPHA,
        threshold: float = DRIFT_THRESHOLD,
    ):
        self.alpha = alpha
        self.threshold = threshold
        self.recent_values: List[float] = []
        self.historical_values: List[float] = []
        self.ewma_recent: float = 0.5
        self.ewma_historical: float = 0.5
        self.measurements: List[DriftMeasurement] = []
        self.audit_triggered: bool = False

    def record(self, accuracy: float) -> DriftMeasurement:
        """Record a new accuracy observation and compute drift.

        Args:
            accuracy: Current accuracy metric (0.0-1.0)

        Returns:
            DriftMeasurement with current state
        """
        accuracy = max(0.0, min(1.0, accuracy))

        # Update recent EWMA
        self.recent_values.append(accuracy)
        if len(self.recent_values) > DRIFT_WINDOW_RECENT:
            self.recent_values.pop(0)
        self.ewma_recent = self._compute_ewma(self.recent_values, self.alpha)

        # Update historical EWMA
        self.historical_values.append(accuracy)
        if len(self.historical_values) > DRIFT_WINDOW_HISTORICAL:
            self.historical_values.pop(0)
        # Use lower alpha for historical (more stable)
        self.ewma_historical = self._compute_ewma(
            self.historical_values, self.alpha * 0.3
        )

        # Compute drift signal
        drift_signal = abs(self.ewma_recent - self.ewma_historical)
        is_drifting = drift_signal > self.threshold

        # Determine direction
        if self.ewma_recent > self.ewma_historical + 0.05:
            direction = "improving"
        elif self.ewma_recent < self.ewma_historical - 0.05:
            direction = "degrading"
        else:
            direction = "stable"

        if is_drifting and direction == "degrading":
            self.audit_triggered = True

        measurement = DriftMeasurement(
            ewma_recent=self.ewma_recent,
            ewma_historical=self.ewma_historical,
            drift_signal=drift_signal,
            is_drifting=is_drifting,
            direction=direction,
        )
        self.measurements.append(measurement)
        return measurement

    def _compute_ewma(self, values: List[float], alpha: float) -> float:
        """Compute Exponentially Weighted Moving Average.

        EWMA_t = α × x_t + (1-α) × EWMA_{t-1}
        """
        if not values:
            return 0.5
        ewma = values[0]
        for v in values[1:]:
            ewma = alpha * v + (1 - alpha) * ewma
        return ewma

    @property
    def current_drift(self) -> float:
        """Current drift signal magnitude."""
        return abs(self.ewma_recent - self.ewma_historical)

    @property
    def is_drifting(self) -> bool:
        """Whether drift exceeds threshold."""
        return self.current_drift > self.threshold

    @property
    def drift_direction(self) -> str:
        """Whether performance is improving, stable, or degrading."""
        if self.ewma_recent > self.ewma_historical + 0.05:
            return "improving"
        elif self.ewma_recent < self.ewma_historical - 0.05:
            return "degrading"
        return "stable"

    @property
    def drift_score(self) -> float:
        """Score for METACOG-X: 1.0 = stable, 0.0 = severe drift.

        Formula: 1.0 - min(drift_signal / (2 × threshold), 1.0)
        """
        if self.threshold == 0:
            return 1.0
        return max(0.0, 1.0 - min(self.current_drift / (2 * self.threshold), 1.0))

    def acknowledge_audit(self) -> None:
        """Acknowledge that a self-audit was performed."""
        self.audit_triggered = False

    def trend(self, window: int = 10) -> str:
        """Get recent trend from last N measurements."""
        recent = self.measurements[-window:]
        if len(recent) < 2:
            return "insufficient_data"
        first_half = [m.ewma_recent for m in recent[:len(recent)//2]]
        second_half = [m.ewma_recent for m in recent[len(recent)//2:]]
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        if avg_second > avg_first + 0.05:
            return "improving"
        elif avg_second < avg_first - 0.05:
            return "degrading"
        return "stable"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ewma_recent": round(self.ewma_recent, 4),
            "ewma_historical": round(self.ewma_historical, 4),
            "drift_signal": round(self.current_drift, 4),
            "is_drifting": self.is_drifting,
            "direction": self.drift_direction,
            "drift_score": round(self.drift_score, 4),
            "audit_triggered": self.audit_triggered,
            "measurement_count": len(self.measurements),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DriftDetector":
        detector = cls()
        detector.ewma_recent = data.get("ewma_recent", 0.5)
        detector.ewma_historical = data.get("ewma_historical", 0.5)
        detector.audit_triggered = data.get("audit_triggered", False)
        return detector
