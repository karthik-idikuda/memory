"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — ThoughtNode                                ║
║  The fundamental unit of metacognitive memory                ║
║  28 fields — every dimension of a thought captured           ║
╚══════════════════════════════════════════════════════════════╝

ThoughtNode captures not just WHAT the AI thought, but:
  - HOW CONFIDENT it was
  - WHETHER it was accurate
  - WHAT EVIDENCE supported it
  - WHETHER it contradicted itself
  - WHAT PATTERN it belongs to
  - WHAT STRATEGY produced it
"""

from __future__ import annotations

import hashlib
import time
import math
from dataclasses import dataclass, field, fields, asdict
from typing import Optional, List, Dict, Any

from cortex.config import (
    CONFIDENCE_DEFAULT, DECAY_MEDIUM, DECAY_PERMANENT,
    ZONE_FOCUSED, ALL_THOUGHT_TYPES, THOUGHT_RESPONSE,
    THOUGHT_WISDOM, ALL_ZONES,
    CORTEXLANG_THOUGHT_SYMBOLS, CORTEXLANG_ZONE_SYMBOLS,
    CORTEXLANG_META_SYMBOLS,
)
from cortex.exceptions import ThoughtNodeValidationError


def _generate_thought_id(content: str, context: str) -> str:
    """Generate unique 32-char hex ID from content + context + timestamp."""
    raw = f"{content}:{context}:{time.time()}:{id(content)}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def _now() -> float:
    """Current UNIX timestamp."""
    return time.time()


@dataclass
class ThoughtNode:
    """
    28-field metacognitive thought node.

    Captures the full lifecycle of a single thought:
    identity, metacognitive state, temporal info, classification,
    linking, evolution tracking, and notation.
    """

    # ── Identity (4 fields) ──
    id: str = ""
    thought_type: str = THOUGHT_RESPONSE
    content: str = ""
    context: str = ""

    # ── Metacognitive State (5 fields) ──
    confidence: float = CONFIDENCE_DEFAULT
    actual_accuracy: float = -1.0       # -1 = unverified
    calibration_error: float = 0.0
    hallucination_score: float = 0.0
    evidence_ratio: float = 1.0

    # ── Temporal (4 fields) ──
    created_at: float = 0.0
    last_accessed: float = 0.0
    access_count: int = 0
    session_id: str = ""

    # ── Classification (3 fields) ──
    zone: str = ZONE_FOCUSED
    domain: str = "general"
    tags: List[str] = field(default_factory=list)

    # ── Linking (6 fields) ──
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)
    memory_ids: List[str] = field(default_factory=list)
    chain_ids: List[str] = field(default_factory=list)
    pattern_id: Optional[str] = None
    strategy_id: Optional[str] = None

    # ── Evolution (4 fields) ──
    version: int = 1
    was_corrected: bool = False
    correction_note: str = ""
    growth_contribution: float = 0.0

    # ── Notation (1 field) ──
    cortexlang_notation: str = ""

    # ── Computed (1 field) ──
    decay_rate: float = DECAY_MEDIUM

    def __post_init__(self):
        """Auto-generate ID and timestamps if not provided."""
        now = _now()
        if not self.id:
            self.id = _generate_thought_id(self.content, self.context)
        if self.created_at == 0.0:
            self.created_at = now
        if self.last_accessed == 0.0:
            self.last_accessed = now
        if self.thought_type == THOUGHT_WISDOM:
            self.decay_rate = DECAY_PERMANENT
        if not self.cortexlang_notation:
            self.cortexlang_notation = self._generate_notation()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # COMPUTED PROPERTIES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def age_seconds(self) -> float:
        """How old this thought is in seconds."""
        return _now() - self.created_at

    @property
    def age_days(self) -> float:
        """How old this thought is in days."""
        return self.age_seconds / 86400.0

    @property
    def is_verified(self) -> bool:
        """Whether actual_accuracy has been set."""
        return self.actual_accuracy >= 0.0

    @property
    def calibration_quality(self) -> str:
        """Human-readable calibration label."""
        if not self.is_verified:
            return "unverified"
        err = abs(self.calibration_error)
        if err <= 0.1:
            return "excellent"
        elif err <= 0.25:
            return "good"
        elif err <= 0.5:
            return "fair"
        else:
            return "poor"

    @property
    def is_wisdom(self) -> bool:
        """Whether this thought is a crystallized wisdom axiom."""
        return self.thought_type == THOUGHT_WISDOM

    @property
    def effective_confidence(self) -> float:
        """Confidence adjusted by historical calibration error.

        Formula: effective = confidence × (1 - calibration_error)
        """
        if not self.is_verified:
            return self.confidence
        adjustment = 1.0 - abs(self.calibration_error)
        return max(0.0, min(1.0, self.confidence * adjustment))

    @property
    def staleness(self) -> float:
        """How stale this thought is (0=fresh, 1=ancient).

        Formula: staleness = 1 - exp(-decay_rate × age_days)
        """
        if self.decay_rate == DECAY_PERMANENT:
            return 0.0
        return 1.0 - math.exp(-self.decay_rate * self.age_days)

    @property
    def link_count(self) -> int:
        """Total number of links to other entities."""
        count = len(self.child_ids) + len(self.memory_ids) + len(self.chain_ids)
        if self.parent_id:
            count += 1
        if self.pattern_id:
            count += 1
        if self.strategy_id:
            count += 1
        return count

    @property
    def hallucination_level(self) -> str:
        """Human-readable hallucination alert level."""
        score = self.evidence_ratio
        if score >= 0.7:
            return "safe"
        elif score >= 0.4:
            return "caution"
        elif score >= 0.2:
            return "warning"
        else:
            return "critical"

    @property
    def confidence_label(self) -> str:
        """Human-readable confidence label."""
        c = self.confidence
        if c < 0.30:
            return "speculative"
        elif c < 0.50:
            return "uncertain"
        elif c < 0.70:
            return "moderate"
        elif c < 0.85:
            return "confident"
        else:
            return "certain"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # METHODS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def touch(self) -> None:
        """Record an access — updates timestamp and count."""
        self.last_accessed = _now()
        self.access_count += 1

    def correct(self, note: str, actual_accuracy: float) -> None:
        """Mark this thought as corrected by user.

        Updates calibration error and evolution tracking.

        Args:
            note: What the user said was wrong
            actual_accuracy: What the real accuracy was (0.0-1.0)
        """
        if not (0.0 <= actual_accuracy <= 1.0):
            raise ThoughtNodeValidationError(
                f"actual_accuracy must be 0.0-1.0, got {actual_accuracy}"
            )
        self.was_corrected = True
        self.correction_note = note
        self.actual_accuracy = actual_accuracy
        self.calibration_error = self.confidence - actual_accuracy
        self.version += 1
        self.touch()

    def verify(self, actual_accuracy: float) -> None:
        """Verify accuracy without marking as corrected.

        Args:
            actual_accuracy: The verified accuracy (0.0-1.0)
        """
        if not (0.0 <= actual_accuracy <= 1.0):
            raise ThoughtNodeValidationError(
                f"actual_accuracy must be 0.0-1.0, got {actual_accuracy}"
            )
        self.actual_accuracy = actual_accuracy
        self.calibration_error = self.confidence - actual_accuracy
        self.touch()

    def add_child(self, child_id: str) -> None:
        """Link a child thought."""
        if child_id not in self.child_ids:
            self.child_ids.append(child_id)

    def add_memory_link(self, memory_id: str) -> None:
        """Link to a NEURON-X memory."""
        if memory_id not in self.memory_ids:
            self.memory_ids.append(memory_id)

    def add_chain_link(self, chain_id: str) -> None:
        """Link to a SIGMA-X causal chain."""
        if chain_id not in self.chain_ids:
            self.chain_ids.append(chain_id)

    def crystallize(self) -> None:
        """Promote this thought to permanent wisdom.

        Changes type to 'wisdom' and sets decay to permanent.
        """
        self.thought_type = THOUGHT_WISDOM
        self.decay_rate = DECAY_PERMANENT
        self.version += 1
        self.cortexlang_notation = self._generate_notation()
        self.touch()

    def validate(self) -> List[str]:
        """Validate all fields, return list of error messages (empty = valid)."""
        errors = []
        if not self.id:
            errors.append("id is empty")
        if len(self.id) != 32:
            errors.append(f"id must be 32 chars, got {len(self.id)}")
        if self.thought_type not in ALL_THOUGHT_TYPES:
            errors.append(f"invalid thought_type: {self.thought_type}")
        if not self.content:
            errors.append("content is empty")
        if not (0.0 <= self.confidence <= 1.0):
            errors.append(f"confidence must be 0.0-1.0, got {self.confidence}")
        if self.actual_accuracy != -1.0 and not (0.0 <= self.actual_accuracy <= 1.0):
            errors.append(f"actual_accuracy must be -1 or 0.0-1.0, got {self.actual_accuracy}")
        if not (0.0 <= self.evidence_ratio <= 1.0):
            errors.append(f"evidence_ratio must be 0.0-1.0, got {self.evidence_ratio}")
        if not (0.0 <= self.hallucination_score <= 1.0):
            errors.append(f"hallucination_score must be 0.0-1.0, got {self.hallucination_score}")
        if self.zone not in ALL_ZONES:
            errors.append(f"invalid zone: {self.zone}")
        if self.created_at <= 0:
            errors.append("created_at must be positive UNIX timestamp")
        if self.access_count < 0:
            errors.append("access_count must be non-negative")
        if self.version < 1:
            errors.append("version must be >= 1")
        if self.decay_rate < 0:
            errors.append("decay_rate must be non-negative")
        return errors

    def is_valid(self) -> bool:
        """Return True if all fields are valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThoughtNode":
        """Deserialize from dictionary."""
        valid_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        node = cls(**filtered)
        return node

    def to_cortexlang(self) -> str:
        """Generate CORTEXLANG-Ω notation for this thought."""
        return self._generate_notation()

    def summary(self) -> str:
        """Single-line summary for debugging."""
        return (
            f"[{self.thought_type.upper()}] "
            f"conf={self.confidence:.2f} "
            f"ev={self.evidence_ratio:.2f} "
            f"zone={self.zone} "
            f"links={self.link_count} "
            f"{'CORRECTED ' if self.was_corrected else ''}"
            f"'{self.content[:60]}...'" if len(self.content) > 60 else
            f"[{self.thought_type.upper()}] "
            f"conf={self.confidence:.2f} "
            f"ev={self.evidence_ratio:.2f} "
            f"zone={self.zone} "
            f"links={self.link_count} "
            f"{'CORRECTED ' if self.was_corrected else ''}"
            f"'{self.content}'"
        )

    def _generate_notation(self) -> str:
        """Build CORTEXLANG-Ω notation string."""
        parts = []

        # Thought type symbol
        type_sym = CORTEXLANG_THOUGHT_SYMBOLS.get(
            self.thought_type.upper(), "◎"
        )
        parts.append(type_sym)

        # Zone symbol
        zone_sym = CORTEXLANG_ZONE_SYMBOLS.get(self.zone, "")
        if zone_sym:
            parts.append(zone_sym)

        # Confidence symbol
        if self.confidence >= 0.85:
            parts.append(CORTEXLANG_META_SYMBOLS["CONFIDENCE_HIGH"])
        elif self.confidence >= 0.50:
            parts.append(CORTEXLANG_META_SYMBOLS["CONFIDENCE_MED"])
        else:
            parts.append(CORTEXLANG_META_SYMBOLS["CONFIDENCE_LOW"])

        # Hallucination shield symbol
        level = self.hallucination_level
        if level == "safe":
            parts.append(CORTEXLANG_META_SYMBOLS["HALLUCINATION_SAFE"])
        elif level in ("caution", "warning"):
            parts.append(CORTEXLANG_META_SYMBOLS["HALLUCINATION_WARN"])
        else:
            parts.append(CORTEXLANG_META_SYMBOLS["HALLUCINATION_CRIT"])

        # Content snippet
        snippet = self.content[:40].replace("\n", " ") if self.content else "∅"
        parts.append(f'"{snippet}"')

        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"ThoughtNode(id='{self.id[:8]}...', "
            f"type='{self.thought_type}', "
            f"conf={self.confidence:.2f}, "
            f"zone='{self.zone}')"
        )

    @classmethod
    def field_count(cls) -> int:
        """Return the number of dataclass fields."""
        return len(fields(cls))
