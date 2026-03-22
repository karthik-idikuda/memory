"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Wisdom Crystallizer                        ║
║  Multi-criteria promotion to permanent axioms                ║
╚══════════════════════════════════════════════════════════════╝

Promotes confirmed insights into permanent wisdom.
Wisdom = crystallized knowledge that never decays.

Criteria for crystallization:
  1. Confirmed ≥ 5 times across different sessions
  2. Confidence ≥ 0.85
  3. Age ≥ 7 days
  4. Never contradicted by strong evidence
  5. Used successfully in ≥ 3 predictions (optional)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from cortex.config import (
    WISDOM_CONFIRMATION_THRESHOLD,
    WISDOM_MIN_CONFIDENCE,
    WISDOM_MIN_AGE_DAYS,
    WISDOM_MAX_PER_DOMAIN,
    WISDOM_OVERRIDE_REQUIRED,
)


@dataclass
class WisdomCandidate:
    """An insight being considered for crystallization."""
    content: str
    domain: str
    confirmations: int = 0
    confidence: float = 0.0
    first_seen: float = 0.0
    last_confirmed: float = 0.0
    contradictions: int = 0
    successful_predictions: int = 0
    session_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.first_seen == 0.0:
            self.first_seen = time.time()
        if self.last_confirmed == 0.0:
            self.last_confirmed = time.time()

    @property
    def age_days(self) -> float:
        return (time.time() - self.first_seen) / 86400.0

    @property
    def unique_sessions(self) -> int:
        return len(set(self.session_ids))

    @property
    def meets_criteria(self) -> bool:
        """Check if all crystallization criteria are met."""
        return (
            self.confirmations >= WISDOM_CONFIRMATION_THRESHOLD
            and self.confidence >= WISDOM_MIN_CONFIDENCE
            and self.age_days >= WISDOM_MIN_AGE_DAYS
            and self.contradictions == 0
        )


@dataclass
class WisdomAxiom:
    """A crystallized permanent wisdom axiom."""
    axiom_id: str
    content: str
    domain: str
    confidence: float
    confirmations: int
    crystallized_at: float
    source_sessions: List[str]
    override_count: int = 0
    active: bool = True

    @property
    def age_days(self) -> float:
        return (time.time() - self.crystallized_at) / 86400.0


class WisdomCrystallizer:
    """Manages insight maturation and wisdom crystallization.

    Tracks candidates, evaluates criteria, and promotes to
    permanent axioms when ready.
    """

    def __init__(self):
        self.candidates: Dict[str, WisdomCandidate] = {}  # key → candidate
        self.axioms: Dict[str, WisdomAxiom] = {}           # axiom_id → axiom
        self._domain_counts: Dict[str, int] = {}

    def observe(
        self,
        content: str,
        domain: str = "general",
        confidence: float = 0.5,
        session_id: str = "",
    ) -> Optional[WisdomAxiom]:
        """Observe a potential insight.

        If it's seen enough times under the right conditions,
        it gets crystallized into permanent wisdom.

        Returns:
            WisdomAxiom if crystallization happened, None otherwise
        """
        key = self._make_key(content, domain)

        if key not in self.candidates:
            self.candidates[key] = WisdomCandidate(
                content=content,
                domain=domain,
                confidence=confidence,
            )

        candidate = self.candidates[key]
        candidate.confirmations += 1
        candidate.last_confirmed = time.time()
        candidate.confidence = max(candidate.confidence, confidence)
        if session_id and session_id not in candidate.session_ids:
            candidate.session_ids.append(session_id)

        # Check crystallization
        if candidate.meets_criteria:
            return self._crystallize(key, candidate)

        return None

    def contradict(self, content: str, domain: str = "general") -> None:
        """Record a contradiction against a candidate or axiom."""
        key = self._make_key(content, domain)

        # Check candidates
        if key in self.candidates:
            self.candidates[key].contradictions += 1

        # Check axioms — override if enough contradictions
        for axiom in self.axioms.values():
            if self._make_key(axiom.content, axiom.domain) == key:
                axiom.override_count += 1
                if axiom.override_count >= WISDOM_OVERRIDE_REQUIRED:
                    axiom.active = False

    def _crystallize(self, key: str, candidate: WisdomCandidate) -> WisdomAxiom:
        """Promote a candidate to permanent wisdom."""
        # Check domain limit
        domain_count = self._domain_counts.get(candidate.domain, 0)
        if domain_count >= WISDOM_MAX_PER_DOMAIN:
            # Remove oldest axiom in domain
            oldest = self._oldest_axiom_in_domain(candidate.domain)
            if oldest:
                oldest.active = False

        from cortex.core.integrity import wisdom_id
        axiom = WisdomAxiom(
            axiom_id=wisdom_id(candidate.content, candidate.domain),
            content=candidate.content,
            domain=candidate.domain,
            confidence=candidate.confidence,
            confirmations=candidate.confirmations,
            crystallized_at=time.time(),
            source_sessions=candidate.session_ids[:],
        )

        self.axioms[axiom.axiom_id] = axiom
        self._domain_counts[candidate.domain] = domain_count + 1

        # Remove from candidates
        del self.candidates[key]

        return axiom

    def _oldest_axiom_in_domain(self, domain: str) -> Optional[WisdomAxiom]:
        """Find the oldest active axiom in a domain."""
        domain_axioms = [
            a for a in self.axioms.values()
            if a.domain == domain and a.active
        ]
        if not domain_axioms:
            return None
        return min(domain_axioms, key=lambda a: a.crystallized_at)

    def _make_key(self, content: str, domain: str) -> str:
        """Create a deterministic key for content+domain."""
        from cortex.core.tokenizer import token_fingerprint
        return f"{domain}:{token_fingerprint(content)}"

    def get_axioms(self, domain: Optional[str] = None) -> List[WisdomAxiom]:
        """Get active axioms, optionally filtered by domain."""
        axioms = [a for a in self.axioms.values() if a.active]
        if domain:
            axioms = [a for a in axioms if a.domain == domain]
        return sorted(axioms, key=lambda a: a.confidence, reverse=True)

    def search_axioms(self, query: str) -> List[WisdomAxiom]:
        """Search axioms by content overlap."""
        from cortex.core.tokenizer import semantic_overlap
        scored = []
        for axiom in self.get_axioms():
            score = semantic_overlap(query, axiom.content)
            if score > 0.2:
                scored.append((score, axiom))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored]

    @property
    def axiom_count(self) -> int:
        return sum(1 for a in self.axioms.values() if a.active)

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    @property
    def wisdom_ratio(self) -> float:
        """For METACOG-X: normalized wisdom accumulation score."""
        total = self.axiom_count + self.candidate_count
        if total == 0:
            return 0.0
        return min(1.0, self.axiom_count / max(total, 1))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "axiom_count": self.axiom_count,
            "candidate_count": self.candidate_count,
            "wisdom_ratio": round(self.wisdom_ratio, 4),
            "axioms": {
                aid: {
                    "content": a.content,
                    "domain": a.domain,
                    "confidence": a.confidence,
                    "confirmations": a.confirmations,
                    "crystallized_at": a.crystallized_at,
                    "active": a.active,
                }
                for aid, a in self.axioms.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WisdomCrystallizer":
        crystallizer = cls()
        for aid, a_data in data.get("axioms", {}).items():
            axiom = WisdomAxiom(
                axiom_id=aid,
                content=a_data["content"],
                domain=a_data["domain"],
                confidence=a_data["confidence"],
                confirmations=a_data["confirmations"],
                crystallized_at=a_data["crystallized_at"],
                source_sessions=[],
                active=a_data.get("active", True),
            )
            crystallizer.axioms[aid] = axiom
        return crystallizer
