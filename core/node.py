"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — ENGRAM Node                           ║
║  The fundamental memory particle of the brain            ║
║  NRNLANG-Ω: ⊕ ENGRAM_FORGE → the act of creation       ║
╚══════════════════════════════════════════════════════════╝

An ENGRAM is a single stored memory unit — the atom of NEURON-X.
Every piece of knowledge, preference, fact, emotion, or event
is stored as one ENGRAM node with 20+ fields tracking its
entire lifecycle from birth to potential expiration.
"""

import math
import time
from dataclasses import dataclass, field
from typing import Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NRNLANG-Ω DECAY CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Exponential decay rates derived from Ebbinghaus forgetting curve
# half_life_days = ln(2) / decay_rate

DECAY_RATES = {
    "emotion":  0.010,   # half-life ≈ 69 days
    "opinion":  0.005,   # half-life ≈ 139 days
    "event":    0.003,   # half-life ≈ 231 days
    "fact":     0.001,   # half-life ≈ 693 days
    "identity": 0.0001,  # half-life ≈ 6931 days (~19 years)
}

HALF_LIVES = {k: math.log(2) / v for k, v in DECAY_RATES.items()}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NRNLANG-Ω ZONE CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

ZONE_HOT = "H"       # [H] constantly used, always loaded
ZONE_WARM = "W"      # [W] recently used, fast access
ZONE_COLD = "C"      # [C] rarely used, compressed storage
ZONE_SILENT = "S"    # [S] dormant, invisible until reawakened
ZONE_ANCHOR = "A"    # [A] permanent zone, never moves to silent

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NRNLANG-Ω TRUTH STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

TRUTH_ACTIVE = "|-"       # |- TRUE_NOW — currently true
TRUTH_EXPIRED = "-|"      # -| TRUE_WAS — was true, now expired
TRUTH_MAYBE = "|~|"       # |~| TRUE_MAYBE — uncertain
TRUTH_CONFLICT = "|!|"    # |!| TRUE_CONFLICT — conflicted

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NRNLANG-Ω EMOTION TAGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

EMOTIONS = {
    "happy":   ":+:",
    "sad":     ":-:",
    "excited": ":!:",
    "curious": ":?:",
    "angry":   ":x:",
    "neutral": ":~:",
    "love":    ":*:",
    "fear":    ":/:",
}

# Zone heat values for scoring
ZONE_HEAT_VALUES = {
    ZONE_HOT: 1.0,
    ZONE_WARM: 0.6,
    ZONE_COLD: 0.2,
    ZONE_SILENT: 0.0,
    ZONE_ANCHOR: 1.0,  # Anchors are always hot
}


@dataclass
class Engram:
    """
    NRNLANG-Ω: ENGRAM — One stored memory unit (the fundamental particle)

    ╔══╗ ENGRAM_BORN → a new memory comes into existence
    Every field maps to the NRNLANG-Ω ENGRAM NODE SYNTAX:
      id, raw, born, last_seen, heat, spark, weight, halflife,
      axons, truth, emotion, confidence, decay, tags,
      superseded_by, contradicts, access_count, valid_from, valid_until
    """

    # ── Core Identity ──
    id: str = ""                          # 16-char SHA-256 fingerprint
    raw: str = ""                         # The actual memory text (never modified)

    # ── Temporal Fields ──
    born: float = 0.0                     # T[birth] — unix timestamp
    last_seen: float = 0.0                # T[last_access] — unix timestamp
    valid_from: float = 0.0               # When this truth became active
    valid_until: Optional[float] = None   # When this truth expired (None = still active)

    # ── Scoring Fields ──
    heat: float = 0.5                     # 0.0–1.0 → determines zone
    spark: float = 0.0                    # 0.0–1.0 → surprise at birth (immutable)
    weight: float = 1.0                   # 0.1–3.0 → grows with use, shrinks with neglect
    confidence: float = 0.80              # 0.0–1.0 → trust level

    # ── Classification ──
    decay_class: str = "fact"             # fact/opinion/emotion/event/identity
    emotion: str = "neutral"              # happy/sad/excited/curious/angry/neutral/love/fear
    tags: list = field(default_factory=list)        # [person, place, preference, ...]
    zone: str = ZONE_WARM                 # H/W/C/S/A

    # ── Truth State ──
    truth: str = TRUTH_ACTIVE             # |- / -| / |~| / |!|
    superseded_by: Optional[str] = None   # engram_id that replaced this truth
    contradicts: list = field(default_factory=list)  # [engram_id, ...]

    # ── Source Tracking ──
    source: str = "user"                  # user/observation/inference

    # ── Connection Graph ──
    axons: dict = field(default_factory=dict)  # {engram_id: synapse_strength}

    # ── Usage Tracking ──
    access_count: int = 0                 # How many times retrieved
    session_count: int = 0                # How many PULSEs seen this engram

    @property
    def decay_rate(self) -> float:
        """NRNLANG-Ω: ~~ DECAY — get the exponential decay rate for this class."""
        return DECAY_RATES.get(self.decay_class, 0.001)

    @property
    def half_life(self) -> float:
        """NRNLANG-Ω: HALFLIFE — days for recency score to halve."""
        return HALF_LIVES.get(self.decay_class, 693.0)

    @property
    def age_days(self) -> float:
        """Days since this engram was born."""
        if self.born <= 0:
            return 0.0
        return max(0.0, (time.time() - self.born) / 86400.0)

    @property
    def days_since_seen(self) -> float:
        """Days since this engram was last accessed."""
        if self.last_seen <= 0:
            return self.age_days
        return max(0.0, (time.time() - self.last_seen) / 86400.0)

    @property
    def recency_score(self) -> float:
        """
        NRNLANG-Ω: RECENCY(engram) = exp(-(λ × Δt))
        WHERE λ = ln(2) / half_life_days
        """
        lam = math.log(2) / self.half_life
        return math.exp(-lam * self.days_since_seen)

    @property
    def is_active(self) -> bool:
        """NRNLANG-Ω: ◈ ENGRAM_LIVE — this memory is currently active."""
        return self.truth == TRUTH_ACTIVE

    @property
    def is_expired(self) -> bool:
        """NRNLANG-Ω: ╚══╝ ENGRAM_DIED — this memory expired."""
        return self.truth == TRUTH_EXPIRED

    @property
    def is_anchor(self) -> bool:
        """NRNLANG-Ω: ◆ ENGRAM_ANCHOR — permanent core memory."""
        return self.zone == ZONE_ANCHOR

    @property
    def is_ghost(self) -> bool:
        """NRNLANG-Ω: ○ ENGRAM_GHOST — silent but capable of reawakening."""
        return self.zone == ZONE_SILENT and self.truth == TRUTH_ACTIVE

    @property
    def is_fossil(self) -> bool:
        """Memory in COLD zone, age above 180 days."""
        return self.zone == ZONE_COLD and self.age_days > 180

    @property
    def emotion_symbol(self) -> str:
        """NRNLANG-Ω: Get the NRNLANG emotion symbol."""
        return EMOTIONS.get(self.emotion, ":~:")

    @property
    def zone_heat_value(self) -> float:
        """NRNLANG-Ω: ZONE_HEAT — numeric heat value for scoring."""
        return ZONE_HEAT_VALUES.get(self.zone, 0.0)

    @property
    def bond_centrality(self) -> float:
        """
        NRNLANG-Ω: BOND_CENTRALITY = log(1 + number_of_axons) / 10.0
        """
        return math.log(1 + len(self.axons)) / 10.0

    @property
    def decay_debt(self) -> float:
        """
        NRNLANG-Ω: DECAYDEBT = days_since_born × decay_rate × 0.1
        Capped at 2.0 in practice.
        """
        return min(2.0, self.age_days * self.decay_rate * 0.1)

    @property
    def clash_penalty(self) -> float:
        """
        NRNLANG-Ω: CLASH_PENALTY
        0.5 if superseded_by is not null + (contradicts count × 0.1)
        """
        penalty = 0.0
        if self.superseded_by is not None:
            penalty += 0.5
        penalty += len(self.contradicts) * 0.1
        return min(2.0, penalty)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Mutation Methods
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def strengthen(self, amount: float = 0.15):
        """NRNLANG-Ω: +++ GROW — weight increasing."""
        self.weight = min(3.0, self.weight + amount)
        self.last_seen = time.time()
        self.access_count += 1

    def weaken(self, amount: float = 0.05):
        """NRNLANG-Ω: --- SHRINK — weight decreasing."""
        self.weight = max(0.1, self.weight - amount)

    def confirm(self, amount: float = 0.05):
        """Confidence grows when confirmed."""
        self.confidence = min(1.0, self.confidence + amount)

    def doubt(self, amount: float = 0.10):
        """Confidence shrinks when contradicted."""
        self.confidence = max(0.1, self.confidence - amount)

    def expire(self, superseded_by_id: Optional[str] = None):
        """
        NRNLANG-Ω: ⊖ ENGRAM_EXPIRE → mark as historical
        engram ⊖ -| EXPIRED
        """
        self.truth = TRUTH_EXPIRED
        self.valid_until = time.time()
        if superseded_by_id:
            self.superseded_by = superseded_by_id
        self.confidence = max(0.1, self.confidence - 0.30)

    def crystallize(self):
        """
        NRNLANG-Ω: CRYSTALLIZE → lock as ANCHOR
        Permanent zone, never moves to silent.
        """
        self.zone = ZONE_ANCHOR

    def touch(self):
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
            "spark": self.spark,
            "weight": self.weight,
            "confidence": self.confidence,
            "decay_class": self.decay_class,
            "emotion": self.emotion,
            "tags": self.tags,
            "zone": self.zone,
            "truth": self.truth,
            "superseded_by": self.superseded_by,
            "contradicts": self.contradicts,
            "axons": self.axons,
            "access_count": self.access_count,
            "session_count": self.session_count,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Engram":
        """Deserialize engram from dictionary."""
        return cls(
            id=data.get("id", ""),
            raw=data.get("raw", ""),
            born=data.get("born", 0.0),
            last_seen=data.get("last_seen", 0.0),
            valid_from=data.get("valid_from", 0.0),
            valid_until=data.get("valid_until"),
            heat=data.get("heat", 0.5),
            spark=data.get("spark", 0.0),
            weight=data.get("weight", 1.0),
            confidence=data.get("confidence", 0.80),
            decay_class=data.get("decay_class", "fact"),
            emotion=data.get("emotion", "neutral"),
            tags=data.get("tags", []),
            zone=data.get("zone", ZONE_WARM),
            truth=data.get("truth", TRUTH_ACTIVE),
            superseded_by=data.get("superseded_by"),
            contradicts=data.get("contradicts", []),
            axons=data.get("axons", {}),
            access_count=data.get("access_count", 0),
            session_count=data.get("session_count", 0),
            source=data.get("source", "user"),
        )

    def to_nrnlang(self) -> str:
        """
        NRNLANG-Ω: ENGRAM ~> NRNLANG notation string

        Converts this engram to full NRNLANG-Ω notation.
        """
        from utils.nrnlang import NRNLangInterpreter
        nrn = NRNLangInterpreter()
        return nrn.engram_to_nrnlang(self)

    def __repr__(self) -> str:
        zone_sym = f"[{self.zone}]"
        truth_sym = self.truth
        emo_sym = self.emotion_symbol
        return (
            f"ENGRAM {zone_sym} {truth_sym} {emo_sym} "
            f"id={self.id[:8]}… "
            f"conf={self.confidence:.2f} "
            f"wt={self.weight:.2f} "
            f"heat={self.heat:.2f} "
            f'"{self.raw[:50]}{"…" if len(self.raw) > 50 else ""}"'
        )
