"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Confidence Calibration Tracker             ║
║  Modified Brier Score with rolling window + bucketing        ║
╚══════════════════════════════════════════════════════════════╝

Tracks the gap between self-assessed confidence and actual accuracy.
Perfect calibration = 0.0 error. Worst = 1.0.

Formula: CalibrationError = (1/N) × Σ(confidence_i - outcome_i)²

Bucketed calibration divides confidence into 10 ranges (0.0-0.1, 0.1-0.2, ...)
and checks whether the AI's confidence in each bucket matches actual accuracy.
"""

from __future__ import annotations

import time
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from cortex.config import (
    CONFIDENCE_WINDOW_SIZE, CONFIDENCE_BUCKETS,
    CONFIDENCE_DECAY_RATE, CONFIDENCE_DEFAULT,
    CONFIDENCE_LABELS,
)


@dataclass
class CalibrationEntry:
    """A single confidence-vs-accuracy observation."""
    confidence: float
    accuracy: float
    domain: str
    timestamp: float
    thought_id: str = ""

    @property
    def error(self) -> float:
        """Squared error: (confidence - accuracy)²"""
        return (self.confidence - self.accuracy) ** 2

    @property
    def signed_error(self) -> float:
        """Signed error: confidence - accuracy (positive = overconfident)."""
        return self.confidence - self.accuracy

    @property
    def age_days(self) -> float:
        return (time.time() - self.timestamp) / 86400.0


class ConfidenceTracker:
    """Rolling confidence calibration tracker.

    Maintains a window of recent (confidence, accuracy) pairs
    and computes calibration metrics.
    """

    def __init__(self, window_size: int = CONFIDENCE_WINDOW_SIZE):
        self.window_size = window_size
        self.entries: List[CalibrationEntry] = []
        self._bucket_counts: Dict[int, int] = defaultdict(int)
        self._bucket_accuracy_sum: Dict[int, float] = defaultdict(float)
        self._bucket_confidence_sum: Dict[int, float] = defaultdict(float)

    def record(
        self,
        confidence: float,
        accuracy: float,
        domain: str = "general",
        thought_id: str = "",
    ) -> CalibrationEntry:
        """Record a new confidence observation.

        Args:
            confidence: self-assessed confidence (0.0-1.0)
            accuracy: verified accuracy (0.0-1.0)
            domain: topic domain
            thought_id: associated thought

        Returns:
            The created CalibrationEntry
        """
        entry = CalibrationEntry(
            confidence=max(0.0, min(1.0, confidence)),
            accuracy=max(0.0, min(1.0, accuracy)),
            domain=domain,
            timestamp=time.time(),
            thought_id=thought_id,
        )
        self.entries.append(entry)

        # Update bucket stats
        bucket = min(int(entry.confidence * CONFIDENCE_BUCKETS), CONFIDENCE_BUCKETS - 1)
        self._bucket_counts[bucket] += 1
        self._bucket_accuracy_sum[bucket] += entry.accuracy
        self._bucket_confidence_sum[bucket] += entry.confidence

        # Trim to window
        while len(self.entries) > self.window_size:
            old = self.entries.pop(0)
            old_bucket = min(int(old.confidence * CONFIDENCE_BUCKETS), CONFIDENCE_BUCKETS - 1)
            self._bucket_counts[old_bucket] = max(0, self._bucket_counts[old_bucket] - 1)
            self._bucket_accuracy_sum[old_bucket] -= old.accuracy
            self._bucket_confidence_sum[old_bucket] -= old.confidence

        return entry

    @property
    def brier_score(self) -> float:
        """Compute Brier-like calibration error.

        Formula: (1/N) × Σ(confidence_i - accuracy_i)²
        Range: 0.0 (perfect) to 1.0 (worst)
        """
        if not self.entries:
            return 0.0
        total = sum(e.error for e in self.entries)
        return total / len(self.entries)

    @property
    def calibration_score(self) -> float:
        """Inverted Brier score: 1.0 = perfectly calibrated, 0.0 = worst.

        Used as input to METACOG-X.
        """
        return 1.0 - self.brier_score

    @property
    def weighted_brier_score(self) -> float:
        """Brier score with exponential time decay (recent data weighted higher).

        Formula: Σ(w_i × error_i) / Σ(w_i)
        where w_i = exp(-decay × age_days)
        """
        if not self.entries:
            return 0.0

        total_weight = 0.0
        total_error = 0.0
        for entry in self.entries:
            weight = math.exp(-CONFIDENCE_DECAY_RATE * entry.age_days)
            total_weight += weight
            total_error += weight * entry.error

        return total_error / total_weight if total_weight > 0 else 0.0

    @property
    def mean_signed_error(self) -> float:
        """Average signed error.

        Positive = overconfident, negative = underconfident.
        """
        if not self.entries:
            return 0.0
        return sum(e.signed_error for e in self.entries) / len(self.entries)

    @property
    def is_overconfident(self) -> bool:
        """Whether the AI is systematically overconfident."""
        return self.mean_signed_error > 0.1

    @property
    def is_underconfident(self) -> bool:
        """Whether the AI is systematically underconfident."""
        return self.mean_signed_error < -0.1

    @property
    def bias_label(self) -> str:
        """Human-readable bias label."""
        mse = self.mean_signed_error
        if mse > 0.2:
            return "significantly_overconfident"
        elif mse > 0.1:
            return "slightly_overconfident"
        elif mse < -0.2:
            return "significantly_underconfident"
        elif mse < -0.1:
            return "slightly_underconfident"
        else:
            return "well_calibrated"

    def bucket_analysis(self) -> List[Dict[str, Any]]:
        """Detailed per-bucket calibration analysis.

        Returns 10 buckets, each with:
        - range: (low, high)
        - count: number of entries
        - avg_confidence: mean confidence in this bucket
        - avg_accuracy: mean accuracy in this bucket
        - gap: avg_confidence - avg_accuracy
        """
        buckets = []
        for i in range(CONFIDENCE_BUCKETS):
            count = self._bucket_counts[i]
            if count > 0:
                avg_conf = self._bucket_confidence_sum[i] / count
                avg_acc = self._bucket_accuracy_sum[i] / count
            else:
                avg_conf = (i + 0.5) / CONFIDENCE_BUCKETS
                avg_acc = 0.0

            buckets.append({
                "range": (i / CONFIDENCE_BUCKETS, (i + 1) / CONFIDENCE_BUCKETS),
                "count": count,
                "avg_confidence": round(avg_conf, 4),
                "avg_accuracy": round(avg_acc, 4),
                "gap": round(avg_conf - avg_acc, 4) if count > 0 else 0.0,
            })
        return buckets

    def suggest_adjusted_confidence(self, raw_confidence: float) -> float:
        """Suggest a calibrated confidence based on historical data.

        If the AI is overconfident, reduce. If underconfident, increase.
        Formula: adjusted = raw - mean_signed_error × damping_factor
        """
        if len(self.entries) < 5:
            return raw_confidence
        damping = 0.5  # don't overcorrect
        adjusted = raw_confidence - (self.mean_signed_error * damping)
        return max(0.0, min(1.0, adjusted))

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    def domain_breakdown(self) -> Dict[str, Dict[str, float]]:
        """Calibration breakdown by domain."""
        domain_groups: Dict[str, List[CalibrationEntry]] = defaultdict(list)
        for e in self.entries:
            domain_groups[e.domain].append(e)

        result = {}
        for domain, entries in domain_groups.items():
            brier = sum(e.error for e in entries) / len(entries)
            mse = sum(e.signed_error for e in entries) / len(entries)
            result[domain] = {
                "brier_score": round(brier, 4),
                "mean_signed_error": round(mse, 4),
                "count": len(entries),
            }
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Serialize tracker state."""
        return {
            "brier_score": round(self.brier_score, 4),
            "calibration_score": round(self.calibration_score, 4),
            "mean_signed_error": round(self.mean_signed_error, 4),
            "bias_label": self.bias_label,
            "entry_count": self.entry_count,
            "entries": [
                {
                    "confidence": e.confidence,
                    "accuracy": e.accuracy,
                    "domain": e.domain,
                    "timestamp": e.timestamp,
                    "thought_id": e.thought_id,
                }
                for e in self.entries
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfidenceTracker":
        """Deserialize from dict."""
        tracker = cls()
        for e_data in data.get("entries", []):
            entry = CalibrationEntry(
                confidence=e_data["confidence"],
                accuracy=e_data["accuracy"],
                domain=e_data.get("domain", "general"),
                timestamp=e_data.get("timestamp", time.time()),
                thought_id=e_data.get("thought_id", ""),
            )
            tracker.entries.append(entry)
            bucket = min(int(entry.confidence * CONFIDENCE_BUCKETS), CONFIDENCE_BUCKETS - 1)
            tracker._bucket_counts[bucket] += 1
            tracker._bucket_accuracy_sum[bucket] += entry.accuracy
            tracker._bucket_confidence_sum[bucket] += entry.confidence
        return tracker
