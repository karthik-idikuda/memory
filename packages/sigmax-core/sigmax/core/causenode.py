"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — CauseNode                               ║
║  CAULANG-Ω: CAUSENODE — the atomic unit of reasoning     ║
╚══════════════════════════════════════════════════════════╝

CauseNode is to SIGMA-X what EngramNode is to NEURON-X.
25 fields capture every dimension of a causal relationship.

One CauseNode = one cause → effect relationship.
A causal chain = multiple linked CauseNodes.
"""

from __future__ import annotations

import math
import uuid
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

from sigmax.config import (
    CAUSAL_DECAY_RATES,
    CONFIDENCE_MIN, CONFIDENCE_MAX,
    CONFIDENCE_LEVELS,
    CAUSE_TYPES,
    ZONE_ACTIVE, ZONE_WARM, ZONE_DORMANT, ZONE_AXIOM, ZONE_ARCHIVED,
    ZONE_HEAT_THRESHOLDS,
    AXIOM_CONFIDENCE_THRESHOLD,
    CAULANG_CHAIN_SYMBOLS,
    CAULANG_ZONE_SYMBOLS,
    CAULANG_CONFIDENCE_SYMBOLS,
    CAULANG_EVIDENCE_SYMBOLS,
    HEAT_ACCESS_WEIGHT, HEAT_RECENCY_WEIGHT,
    HEAT_EVIDENCE_WEIGHT, HEAT_PREDICTION_WEIGHT,
    HEAT_CONFIDENCE_WEIGHT,
    MAX_CHAIN_WEIGHT, MIN_CHAIN_WEIGHT,
)
from sigmax.exceptions import CauseNodeValidationError


def _generate_id() -> str:
    """Generate a unique 16-byte hex ID for a CauseNode."""
    return uuid.uuid4().hex[:32]


def _now() -> float:
    """Current UNIX timestamp."""
    return time.time()


@dataclass
class CauseNode:
    """
    The atomic unit of causal reasoning in SIGMA-X.

    25 fields capturing:
    - Identity (id, cause, effect, type)
    - Confidence & strength (confidence, weight, decay_class)
    - Evidence tracking (evidence_for, evidence_against)
    - Prediction tracking (predictions_made, predictions_correct, predictions_failed)
    - Temporal (created_at, last_accessed, access_count)
    - Classification (zone, tags, subject, source)
    - Linking (parent_id, child_ids, neuronx_link_id)
    - Notation (caulang_notation)
    - Counterfactuals (counterfactual_count)
    """

    # ── Identity ──
    id: str = field(default_factory=_generate_id)
    cause: str = ""
    effect: str = ""
    cause_type: str = "direct"

    # ── Confidence & Strength ──
    confidence: float = 0.50
    weight: float = 1.0
    decay_class: str = "medium"

    # ── Evidence Tracking ──
    evidence_for: int = 0
    evidence_against: int = 0

    # ── Prediction Tracking ──
    predictions_made: int = 0
    predictions_correct: int = 0
    predictions_failed: int = 0

    # ── Temporal ──
    created_at: float = field(default_factory=_now)
    last_accessed: float = field(default_factory=_now)
    access_count: int = 0

    # ── Classification ──
    zone: str = ZONE_ACTIVE
    tags: list = field(default_factory=list)
    subject: str = ""
    source: str = "inference"
    chain_id: Optional[str] = None       # groups nodes in the same causal chain

    # ── Linking ──
    parent_id: Optional[str] = None
    child_ids: list = field(default_factory=list)
    neuronx_link_id: Optional[str] = None

    # ── Notation ──
    caulang_notation: str = ""

    # ── Counterfactuals ──
    counterfactual_count: int = 0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # VALIDATION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def __post_init__(self):
        """Validate all fields after construction."""
        if not self.cause or not isinstance(self.cause, str):
            raise CauseNodeValidationError("cause must be a non-empty string")
        if not self.effect or not isinstance(self.effect, str):
            raise CauseNodeValidationError("effect must be a non-empty string")
        if self.cause_type not in CAUSE_TYPES:
            raise CauseNodeValidationError(
                f"cause_type must be one of {CAUSE_TYPES}, got '{self.cause_type}'"
            )
        if self.decay_class not in CAUSAL_DECAY_RATES:
            raise CauseNodeValidationError(
                f"decay_class must be one of {list(CAUSAL_DECAY_RATES.keys())}, "
                f"got '{self.decay_class}'"
            )
        # Clamp confidence
        self.confidence = max(CONFIDENCE_MIN, min(CONFIDENCE_MAX, self.confidence))
        # Clamp weight
        self.weight = max(MIN_CHAIN_WEIGHT, min(MAX_CHAIN_WEIGHT, self.weight))
        # Generate CAULANG notation if empty
        if not self.caulang_notation:
            self.caulang_notation = self.to_caulang()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # COMPUTED PROPERTIES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def age_days(self) -> float:
        """Age in days since creation."""
        return (_now() - self.created_at) / 86400.0

    @property
    def decay_rate(self) -> float:
        """Current decay rate (λ) based on decay_class."""
        return CAUSAL_DECAY_RATES.get(self.decay_class, 0.005)

    @property
    def current_decay(self) -> float:
        """Current decay amount: 1 - e^(-λ × age_days)."""
        return 1.0 - math.exp(-self.decay_rate * self.age_days)

    @property
    def effective_confidence(self) -> float:
        """Confidence adjusted for decay: confidence × e^(-λ × age_days)."""
        if self.decay_class == "permanent":
            return self.confidence
        return self.confidence * math.exp(-self.decay_rate * self.age_days)

    @property
    def evidence_net(self) -> int:
        """Net evidence count: for - against."""
        return self.evidence_for - self.evidence_against

    @property
    def prediction_accuracy(self) -> float:
        """Prediction accuracy ratio (0.0 if no predictions made)."""
        if self.predictions_made == 0:
            return 0.0
        return self.predictions_correct / self.predictions_made

    @property
    def confidence_label(self) -> str:
        """Human-readable confidence level."""
        if self.confidence >= CONFIDENCE_LEVELS["axiom"]:
            return "axiom"
        elif self.confidence >= CONFIDENCE_LEVELS["strong"]:
            return "strong"
        elif self.confidence >= CONFIDENCE_LEVELS["moderate"]:
            return "moderate"
        return "speculative"

    @property
    def is_axiom(self) -> bool:
        """True if this node has been crystallized as an axiom."""
        return self.zone == ZONE_AXIOM or self.confidence >= AXIOM_CONFIDENCE_THRESHOLD

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # METHODS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_recency(self) -> float:
        """
        Recency score: e^(-λ × days_since_last_access).
        More recently accessed = higher score.
        """
        days_since = (_now() - self.last_accessed) / 86400.0
        return math.exp(-self.decay_rate * max(0, days_since))

    def get_heat(self) -> float:
        """
        Compute causal heat for zone assignment.

        heat = ACCESS_W × min(access/20, 1.0)
             + RECENCY_W × recency
             + EVIDENCE_W × tanh(net_evidence / 5.0)
             + PREDICTION_W × prediction_accuracy
             + CONFIDENCE_W × confidence
        """
        access_score = min(self.access_count / 20.0, 1.0)
        recency_score = self.get_recency()
        evidence_score = math.tanh(self.evidence_net / 5.0)
        # Normalize evidence_score to [0, 1]
        evidence_normalized = (evidence_score + 1.0) / 2.0
        pred_score = self.prediction_accuracy

        heat = (
            HEAT_ACCESS_WEIGHT * access_score +
            HEAT_RECENCY_WEIGHT * recency_score +
            HEAT_EVIDENCE_WEIGHT * evidence_normalized +
            HEAT_PREDICTION_WEIGHT * pred_score +
            HEAT_CONFIDENCE_WEIGHT * self.confidence
        )
        return max(0.0, min(1.0, heat))

    def compute_zone(self) -> str:
        """
        Determine the thermal zone based on heat and confidence.

        Priority: AXIOM > ACTIVE > WARM > DORMANT > ARCHIVED
        """
        if self.is_axiom:
            return ZONE_AXIOM

        heat = self.get_heat()

        if heat >= ZONE_HEAT_THRESHOLDS[ZONE_ACTIVE]:
            return ZONE_ACTIVE
        elif heat >= ZONE_HEAT_THRESHOLDS[ZONE_WARM]:
            return ZONE_WARM
        elif heat >= ZONE_HEAT_THRESHOLDS[ZONE_DORMANT]:
            return ZONE_DORMANT
        return ZONE_ARCHIVED

    def update_zone(self) -> str:
        """Compute and assign the current zone. Returns the new zone."""
        self.zone = self.compute_zone()
        return self.zone

    def touch(self) -> None:
        """Record an access — update last_accessed and increment access_count."""
        self.last_accessed = _now()
        self.access_count += 1

    def add_evidence(self, is_support: bool) -> None:
        """
        Add supporting or contradicting evidence.
        Adjusts confidence accordingly.
        """
        if is_support:
            self.evidence_for += 1
            self.confidence = min(
                CONFIDENCE_MAX,
                self.confidence + 0.03
            )
        else:
            self.evidence_against += 1
            self.confidence = max(
                CONFIDENCE_MIN,
                self.confidence - 0.05
            )
        self.update_zone()

    def record_prediction(self, correct: bool) -> None:
        """
        Record prediction outcome.
        Adjusts confidence based on correctness.
        """
        self.predictions_made += 1
        if correct:
            self.predictions_correct += 1
            self.confidence = min(
                CONFIDENCE_MAX,
                self.confidence + 0.05
            )
        else:
            self.predictions_failed += 1
            self.confidence = max(
                CONFIDENCE_MIN,
                self.confidence - 0.10
            )
        self.update_zone()

    def strengthen(self, amount: float = 0.12) -> None:
        """Increase weight (capped at MAX_CHAIN_WEIGHT)."""
        self.weight = min(MAX_CHAIN_WEIGHT, self.weight + amount)

    def weaken(self, amount: float = 0.12) -> None:
        """Decrease weight (floored at MIN_CHAIN_WEIGHT)."""
        self.weight = max(MIN_CHAIN_WEIGHT, self.weight - amount)

    def crystallize(self) -> bool:
        """
        Attempt to crystallize this node as an AXIOM.
        Returns True if crystallization succeeded.

        Requirements:
        - confidence >= AXIOM threshold
        - access_count >= threshold
        - evidence_net >= threshold
        - prediction_accuracy >= threshold (if predictions made)
        """
        from sigmax.config import (
            AXIOM_ACCESS_THRESHOLD,
            AXIOM_EVIDENCE_NET_THRESHOLD,
            AXIOM_PREDICTION_ACCURACY_THRESHOLD,
        )

        if self.confidence < AXIOM_CONFIDENCE_THRESHOLD:
            return False
        if self.access_count < AXIOM_ACCESS_THRESHOLD:
            return False
        if self.evidence_net < AXIOM_EVIDENCE_NET_THRESHOLD:
            return False
        if (self.predictions_made > 0 and
                self.prediction_accuracy < AXIOM_PREDICTION_ACCURACY_THRESHOLD):
            return False

        self.zone = ZONE_AXIOM
        self.decay_class = "permanent"
        self.caulang_notation = self.to_caulang()
        return True

    def to_caulang(self) -> str:
        """
        Generate CAULANG-Ω notation for this node.

        Format: [ZONE] CAUSE ~>~ EFFECT (confidence) [evidence] {predictions}
        Example: ⚡ [A] "rain" ~>~ "wet road" (!) [+3/-1] {5/6 →✓}
        """
        chain_sym = CAULANG_CHAIN_SYMBOLS.get(
            self.cause_type.upper(), "~>~"
        )
        zone_sym = CAULANG_ZONE_SYMBOLS.get(self.zone, "◈")
        conf_sym = CAULANG_CONFIDENCE_SYMBOLS.get(
            self.confidence_label, "(~)"
        )

        notation = f'{zone_sym} "{self.cause}" {chain_sym} "{self.effect}" {conf_sym}'

        # Evidence
        if self.evidence_for > 0 or self.evidence_against > 0:
            notation += f' [+{self.evidence_for}/-{self.evidence_against}]'

        # Predictions
        if self.predictions_made > 0:
            acc_pct = int(self.prediction_accuracy * 100)
            notation += f' {{{self.predictions_correct}/{self.predictions_made} {acc_pct}%}}'

        return notation

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CauseNode:
        """Deserialize from dictionary."""
        # Filter to only known field names
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        # Skip validation for deserialized nodes by creating without __post_init__
        node = object.__new__(cls)
        for fname, fld in cls.__dataclass_fields__.items():
            if fname in filtered:
                setattr(node, fname, filtered[fname])
            elif fld.default is not fld.default_factory:
                setattr(node, fname, fld.default if fld.default is not fld.default_factory else None)
            else:
                setattr(node, fname, fld.default_factory())
        return node

    def to_summary(self) -> str:
        """One-line human summary."""
        return (
            f"[{self.zone}] \"{self.cause}\" → \"{self.effect}\" "
            f"(conf={self.confidence:.2f}, type={self.cause_type}, "
            f"ev={self.evidence_net:+d}, pred={self.prediction_accuracy:.0%})"
        )

    def __repr__(self) -> str:
        return (
            f"CauseNode(id={self.id[:8]}..., "
            f"cause='{self.cause[:30]}', "
            f"effect='{self.effect[:30]}', "
            f"type={self.cause_type}, "
            f"conf={self.confidence:.2f}, "
            f"zone={self.zone})"
        )
