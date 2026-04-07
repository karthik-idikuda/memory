"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — ENGRAM Node                            ║
║  NRNLANG-Ω: ⊕ ENGRAM_FORGE → the act of creation       ║
║  The fundamental memory particle of the brain            ║
╚══════════════════════════════════════════════════════════╝

An ENGRAM is a single stored memory unit — the atom of NEURON-X.
Every piece of knowledge, preference, fact, emotion, or event
is stored as one EngramNode with 20 fields tracking its
entire lifecycle from birth to potential expiration.

NRNLANG-Ω ENGRAM NOTATION:
  ENGRAM { id:"..." raw:"..." born:T[...] heat:0.71~>[H] spark:0.88⚡ ... }
"""

import math
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict

from neuronx.config import (
    DECAY_RATES, ZONE_HOT, ZONE_WARM, ZONE_SILENT,
    ZONE_HEAT_VALUES, TRUTH_ACTIVE, TRUTH_EXPIRED, MAX_WEIGHT, MIN_WEIGHT, NRNLANG_EMOTION_SYMBOLS,
)


HALF_LIVES = {k: math.log(2) / v for k, v in DECAY_RATES.items()}


@dataclass
class EngramNode:
    """
    NRNLANG-Ω: ENGRAM — One stored memory unit (the fundamental particle)

    ╔══╗ ENGRAM_BORN → a new memory comes into existence

    20 required fields:
      id, raw, born, last_seen, heat, surprise_score, weight,
      access_count, decay_class, bonds, zone, confidence, emotion,
      source, valid_from, valid_until, superseded_by, contradicts,
      tags, is_anchor
    """

    # ── Core Identity ──
    id: str = ""                                    # 16-char SHA-256 fingerprint
    raw: str = ""                                   # original memory text (immutable)

    # ── Temporal ──
    born: float = 0.0                               # T[birth] unix timestamp
    last_seen: float = 0.0                          # T[last_access] unix timestamp
    valid_from: float = 0.0                         # when this truth became active
    valid_until: Optional[float] = None             # when expired (None = still active)

    # ── Scoring ──
    heat: float = 0.5                               # thermal score 0.0–1.0
    surprise_score: float = 0.0                     # score at birth (SPARK_LEGACY, immutable)
    weight: float = 1.0                             # strength 0.1–3.0
    confidence: float = 0.80                        # reliability 0.0–1.0

    # ── Classification ──
    decay_class: str = "fact"                       # fact/opinion/emotion/event/identity
    emotion: str = "neutral"                        # happy/sad/excited/curious/angry/neutral/love/fear
    tags: List[str] = field(default_factory=list)   # categorical tags
    zone: str = ZONE_WARM                           # HOT/WARM/COLD/SILENT

    # ── Truth State ──
    truth: str = TRUTH_ACTIVE                       # active/expired/contested
    superseded_by: Optional[str] = None             # id of newer contradicting engram
    contradicts: List[str] = field(default_factory=list)   # conflicting engram ids

    # ── Source ──
    source: str = "user"                            # user/inference/import

    # ── Connection Graph ──
    bonds: Dict[str, float] = field(default_factory=dict)  # {engram_id: synapse_strength}

    # ── Usage ──
    access_count: int = 0                           # total retrieval count

    # ── Anchor (BUG-005 FIX) ──
    is_anchor: bool = False                         # crystallized, never moves to SILENT

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Computed Properties
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_decay_rate(self) -> float:
        """NRNLANG-Ω: ~~ DECAY — get the exponential decay rate for this class."""
        return DECAY_RATES.get(self.decay_class, 0.001)

    @property
    def half_life(self) -> float:
        """NRNLANG-Ω: HALFLIFE — days for recency score to halve."""
        return HALF_LIVES.get(self.decay_class, 693.0)

    @property
    def age_days(self) -> float:
        """Days since birth."""
        if self.born <= 0:
            return 0.0
        return max(0.0, (time.time() - self.born) / 86400.0)

    @property
    def days_since_seen(self) -> float:
        """Days since last access."""
        if self.last_seen <= 0:
            return self.age_days
        return max(0.0, (time.time() - self.last_seen) / 86400.0)

    @property
    def recency_score(self) -> float:
        """
        NRNLANG-Ω: RECENCY_CURVE = exp(-λ × days_since_last_seen)
        """
        lam = self.get_decay_rate()
        return math.exp(-lam * self.days_since_seen)

    def is_active_engram(self) -> bool:
        """NRNLANG-Ω: ◈ ENGRAM_LIVE — this memory is currently active."""
        return self.truth == TRUTH_ACTIVE

    def is_expired_engram(self) -> bool:
        """NRNLANG-Ω: ╚══╝ ENGRAM_DIED — this memory expired."""
        return self.truth == TRUTH_EXPIRED

    def is_ghost(self) -> bool:
        """NRNLANG-Ω: ○ ENGRAM_GHOST — silent but capable of reawakening."""
        return self.zone == ZONE_SILENT and self.truth == TRUTH_ACTIVE

    @property
    def emotion_symbol(self) -> str:
        """NRNLANG-Ω: Get the NRNLANG emotion symbol."""
        return NRNLANG_EMOTION_SYMBOLS.get(self.emotion, ":~:")

    @property
    def zone_heat_value(self) -> float:
        """NRNLANG-Ω: ZONE_HEAT — numeric heat value for scoring."""
        if self.is_anchor:
            return 1.0
        return ZONE_HEAT_VALUES.get(self.zone, 0.0)

    @property
    def bond_centrality(self) -> float:
        """
        NRNLANG-Ω: BOND_CENTRALITY = log₁₀(1 + len(bonds)) / 3.0
        """
        return math.log10(1 + len(self.bonds)) / 3.0

    @property
    def decay_debt(self) -> float:
        """
        NRNLANG-Ω: DECAY_DEBT = min(2.0, days_since_born × λ × 0.1)
        """
        return min(2.0, self.age_days * self.get_decay_rate() * 0.1)

    @property
    def clash_penalty(self) -> float:
        """
        NRNLANG-Ω: CLASH_PENALTY = (0.5 if superseded) + (0.1 × len(contradicts))
        """
        penalty = 0.0
        if self.superseded_by is not None:
            penalty += 0.5
        penalty += len(self.contradicts) * 0.1
        return penalty

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Mutation Methods
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def strengthen(self, amount: float = 0.15) -> None:
        """NRNLANG-Ω: +++ GROW — weight increasing."""
        self.weight = min(MAX_WEIGHT, self.weight + amount)
        self.last_seen = time.time()
        self.access_count += 1

    def weaken(self, amount: float = 0.05) -> None:
        """NRNLANG-Ω: --- SHRINK — weight decreasing."""
        self.weight = max(MIN_WEIGHT, self.weight - amount)

    def confirm(self, amount: float = 0.05) -> None:
        """Confidence grows when confirmed."""
        self.confidence = min(1.0, self.confidence + amount)

    def doubt(self, amount: float = 0.10) -> None:
        """Confidence shrinks when contradicted."""
        self.confidence = max(0.1, self.confidence - amount)

    def expire(self, superseded_by_id: Optional[str] = None) -> None:
        """
        NRNLANG-Ω: ⊖ ENGRAM_EXPIRE → mark as historical
        """
        self.truth = TRUTH_EXPIRED
        self.valid_until = time.time()
        if superseded_by_id:
            self.superseded_by = superseded_by_id
        self.confidence = max(0.1, self.confidence - 0.30)

    def crystallize(self) -> None:
        """
        NRNLANG-Ω: CRYSTALLIZE → lock as ANCHOR
        Sets is_anchor = True, zone = "HOT". Never moves to SILENT.
        """
        self.is_anchor = True
        self.zone = ZONE_HOT

    def touch(self) -> None:
        """Update last_seen and access_count on retrieval."""
        self.last_seen = time.time()
        self.access_count += 1

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Serialization
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def to_dict(self) -> dict:
        """Serialize engram to dictionary for SOMA-DB storage."""
        return {
            "id": self.id,
            "raw": self.raw,
            "born": self.born,
            "last_seen": self.last_seen,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "heat": self.heat,
            "surprise_score": self.surprise_score,
            "weight": self.weight,
            "confidence": self.confidence,
            "decay_class": self.decay_class,
            "emotion": self.emotion,
            "tags": list(self.tags),
            "zone": self.zone,
            "truth": self.truth,
            "superseded_by": self.superseded_by,
            "contradicts": list(self.contradicts),
            "bonds": dict(self.bonds),
            "access_count": self.access_count,
            "source": self.source,
            "is_anchor": self.is_anchor,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EngramNode":
        """Deserialize engram from dictionary."""
        return cls(
            id=data.get("id", ""),
            raw=data.get("raw", ""),
            born=data.get("born", 0.0),
            last_seen=data.get("last_seen", 0.0),
            valid_from=data.get("valid_from", 0.0),
            valid_until=data.get("valid_until"),
            heat=data.get("heat", 0.5),
            surprise_score=data.get("surprise_score", data.get("spark", 0.0)),
            weight=data.get("weight", 1.0),
            confidence=data.get("confidence", 0.80),
            decay_class=data.get("decay_class", "fact"),
            emotion=data.get("emotion", "neutral"),
            tags=list(data.get("tags", [])),
            zone=data.get("zone", ZONE_WARM),
            truth=data.get("truth", TRUTH_ACTIVE),
            superseded_by=data.get("superseded_by"),
            contradicts=list(data.get("contradicts", [])),
            bonds=dict(data.get("bonds", data.get("axons", {}))),
            access_count=data.get("access_count", 0),
            source=data.get("source", "user"),
            is_anchor=data.get("is_anchor", False),
        )

    def __repr__(self) -> str:
        zone_sym = f"[{self.zone[0]}]" if self.zone else "[?]"
        anchor_sym = "◆" if self.is_anchor else ""
        return (
            f"ENGRAM {zone_sym}{anchor_sym} {self.truth} {self.emotion_symbol} "
            f"id={self.id[:8]}… "
            f"conf={self.confidence:.2f} "
            f"wt={self.weight:.2f} "
            f"heat={self.heat:.2f} "
            f'"{self.raw[:50]}{"…" if len(self.raw) > 50 else ""}"'
        )
