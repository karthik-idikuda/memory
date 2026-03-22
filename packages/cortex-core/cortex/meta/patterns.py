"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Error Pattern Recognizer                   ║
║  Causal Pattern Mining for recurring error detection         ║
╚══════════════════════════════════════════════════════════════╝

Detects when the AI keeps making the same TYPE of error.
Patterns = recurring (error_type, context_type) pairs.

Formula: PatternStrength = frequency × recency_factor × severity_weight
  recency_factor = exp(-decay × days_since_last)
"""

from __future__ import annotations

import time
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import defaultdict

from cortex.config import (
    PATTERN_MIN_OCCURRENCES, PATTERN_RECENCY_DECAY,
    PATTERN_SEVERITY_WEIGHTS,
)


@dataclass
class ErrorOccurrence:
    """A single error occurrence."""
    timestamp: float
    thought_id: str = ""
    context: str = ""

    @property
    def age_days(self) -> float:
        return (time.time() - self.timestamp) / 86400.0


@dataclass
class ErrorPattern:
    """A detected recurring error pattern."""
    pattern_id: str
    error_type: str
    context_type: str
    domain: str
    occurrences: List[ErrorOccurrence] = field(default_factory=list)
    resolved: bool = False
    resolution_note: str = ""
    created_at: float = 0.0

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

    @property
    def frequency(self) -> int:
        return len(self.occurrences)

    @property
    def severity(self) -> float:
        return PATTERN_SEVERITY_WEIGHTS.get(self.error_type, 0.5)

    @property
    def recency_factor(self) -> float:
        """Exponential time decay based on most recent occurrence."""
        if not self.occurrences:
            return 0.0
        most_recent = min(o.age_days for o in self.occurrences)
        return math.exp(-PATTERN_RECENCY_DECAY * most_recent)

    @property
    def strength(self) -> float:
        """PatternStrength = frequency × recency_factor × severity_weight"""
        return self.frequency * self.recency_factor * self.severity

    @property
    def is_active(self) -> bool:
        """Pattern is active if it meets minimum occurrences and isn't resolved."""
        return (
            self.frequency >= PATTERN_MIN_OCCURRENCES
            and not self.resolved
            and self.strength > 0.5
        )


class PatternRecognizer:
    """Detects and tracks recurring error patterns.

    Algorithm:
      1. Categorize each error: (error_type, context_type, domain)
      2. Group by pattern key
      3. Compute PatternStrength for each group
      4. If strength > threshold and occurrences >= minimum → confirmed pattern
    """

    def __init__(self):
        self.patterns: Dict[str, ErrorPattern] = {}
        self.total_errors: int = 0

    def record_error(
        self,
        error_type: str,
        context_type: str = "general",
        domain: str = "general",
        thought_id: str = "",
        context: str = "",
    ) -> Optional[ErrorPattern]:
        """Record an error and check if it forms a pattern.

        Args:
            error_type: Category of error (see PATTERN_SEVERITY_WEIGHTS)
            context_type: Type of context where error occurred
            domain: Topic domain
            thought_id: Associated thought ID
            context: Additional context string

        Returns:
            ErrorPattern if pattern is now active, None otherwise
        """
        self.total_errors += 1
        pattern_key = f"{error_type}:{context_type}:{domain}"

        occurrence = ErrorOccurrence(
            timestamp=time.time(),
            thought_id=thought_id,
            context=context,
        )

        if pattern_key not in self.patterns:
            from cortex.core.integrity import pattern_id
            self.patterns[pattern_key] = ErrorPattern(
                pattern_id=pattern_id(error_type, context_type),
                error_type=error_type,
                context_type=context_type,
                domain=domain,
            )

        pattern = self.patterns[pattern_key]
        pattern.occurrences.append(occurrence)

        if pattern.is_active:
            return pattern
        return None

    def get_active_patterns(self) -> List[ErrorPattern]:
        """Get all currently active (unresolved, strong enough) patterns."""
        return sorted(
            [p for p in self.patterns.values() if p.is_active],
            key=lambda p: p.strength,
            reverse=True,
        )

    def get_pattern(self, pattern_key: str) -> Optional[ErrorPattern]:
        """Get a specific pattern by key."""
        return self.patterns.get(pattern_key)

    def resolve_pattern(self, pattern_key: str, note: str = "") -> bool:
        """Mark a pattern as resolved."""
        pattern = self.patterns.get(pattern_key)
        if pattern:
            pattern.resolved = True
            pattern.resolution_note = note
            return True
        return False

    def check_for_pattern(self, error_type: str, context_type: str = "general",
                          domain: str = "general") -> Optional[ErrorPattern]:
        """Check if a pattern exists for this error type without recording."""
        key = f"{error_type}:{context_type}:{domain}"
        pattern = self.patterns.get(key)
        if pattern and pattern.is_active:
            return pattern
        return None

    @property
    def active_count(self) -> int:
        return len(self.get_active_patterns())

    @property
    def resolved_count(self) -> int:
        return sum(1 for p in self.patterns.values() if p.resolved)

    @property
    def pattern_score(self) -> float:
        """Score for METACOG-X: 1.0 = all patterns resolved or none, 0.0 = many active.

        Formula: max(0, 1.0 - (active_count × 0.15))
        More active patterns = lower score.
        """
        return max(0.0, 1.0 - (self.active_count * 0.15))

    def patterns_for_context(self, context_type: str, domain: str = "general") -> List[ErrorPattern]:
        """Get all active patterns matching a context + domain."""
        return [
            p for p in self.get_active_patterns()
            if p.context_type == context_type and p.domain == domain
        ]

    def summary(self) -> Dict[str, Any]:
        return {
            "total_errors": self.total_errors,
            "total_patterns": len(self.patterns),
            "active_patterns": self.active_count,
            "resolved_patterns": self.resolved_count,
            "pattern_score": round(self.pattern_score, 4),
            "top_patterns": [
                {
                    "error_type": p.error_type,
                    "context_type": p.context_type,
                    "frequency": p.frequency,
                    "strength": round(p.strength, 2),
                }
                for p in self.get_active_patterns()[:5]
            ],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_errors": self.total_errors,
            "patterns": {
                k: {
                    "pattern_id": p.pattern_id,
                    "error_type": p.error_type,
                    "context_type": p.context_type,
                    "domain": p.domain,
                    "frequency": p.frequency,
                    "resolved": p.resolved,
                    "resolution_note": p.resolution_note,
                }
                for k, p in self.patterns.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatternRecognizer":
        recognizer = cls()
        recognizer.total_errors = data.get("total_errors", 0)
        return recognizer
