"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Contradiction Detector                     ║
║  Real-time self-contradiction detection engine               ║
╚══════════════════════════════════════════════════════════════╝

Detects when the AI contradicts its own past statements.
Uses memory cross-referencing and semantic overlap analysis.

Contradiction = high semantic overlap + opposite sentiment/direction.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from cortex.core.tokenizer import (
    tokenize_filtered, semantic_overlap, extract_claims,
)


@dataclass
class Contradiction:
    """A detected self-contradiction."""
    claim: str
    past_content: str
    past_thought_id: str
    overlap_score: float
    detected_at: float = 0.0
    domain: str = "general"
    resolved: bool = False

    def __post_init__(self):
        if self.detected_at == 0.0:
            self.detected_at = time.time()


class ContradictionDetector:
    """Detects self-contradictions by cross-referencing new claims
    against stored thought history.

    Algorithm:
      1. Extract claims from new response
      2. For each claim, search past thoughts for high semantic overlap
      3. If overlap > threshold AND direction differs → CONTRADICTION
      4. Track contradiction density over time
    """

    def __init__(self, overlap_threshold: float = 0.6):
        self.overlap_threshold = overlap_threshold
        self.contradictions: List[Contradiction] = []
        self.scan_count: int = 0
        self.total_claims_checked: int = 0

    def scan(
        self,
        new_content: str,
        past_thoughts: List[Dict[str, str]],
        domain: str = "general",
    ) -> List[Contradiction]:
        """Scan new content against past thoughts for contradictions.

        Args:
            new_content: The new response text
            past_thoughts: List of dicts with 'id' and 'content' keys
            domain: Topic domain

        Returns:
            List of detected Contradiction objects
        """
        self.scan_count += 1
        claims = extract_claims(new_content)
        found: List[Contradiction] = []

        for claim in claims:
            self.total_claims_checked += 1
            claim_tokens = tokenize_filtered(claim)
            if len(claim_tokens) < 3:
                continue

            for past in past_thoughts:
                past_content = past.get("content", "")
                past_id = past.get("id", "")

                overlap = semantic_overlap(claim, past_content)
                if overlap >= self.overlap_threshold:
                    # Check for negation/opposition signals
                    if self._detect_opposition(claim, past_content):
                        contradiction = Contradiction(
                            claim=claim,
                            past_content=past_content[:200],
                            past_thought_id=past_id,
                            overlap_score=overlap,
                            domain=domain,
                        )
                        found.append(contradiction)
                        self.contradictions.append(contradiction)

        return found

    def _detect_opposition(self, text_a: str, text_b: str) -> bool:
        """Detect if two semantically similar texts say OPPOSITE things.

        Uses negation pattern and antonym heuristics.
        """
        tokens_a = set(tokenize_filtered(text_a))
        tokens_b = set(tokenize_filtered(text_b))

        # Negation keywords
        negation_words = {
            "not", "never", "no", "dont", "doesnt", "didnt", "wont",
            "cant", "shouldnt", "wouldnt", "isnt", "arent", "wasnt",
            "without", "none", "nothing", "neither", "nor", "hardly",
            "barely", "rarely", "impossible", "incorrect", "wrong",
            "false", "untrue", "invalid", "bad", "fail", "failed",
            "avoid", "stop", "remove", "delete", "disable",
        }

        # Antonym pairs
        antonym_pairs = [
            ("good", "bad"), ("right", "wrong"), ("true", "false"),
            ("yes", "no"), ("should", "shouldnt"), ("always", "never"),
            ("increase", "decrease"), ("add", "remove"), ("enable", "disable"),
            ("start", "stop"), ("open", "close"), ("fast", "slow"),
            ("better", "worse"), ("correct", "incorrect"), ("safe", "unsafe"),
            ("use", "avoid"), ("recommended", "deprecated"),
            ("include", "exclude"), ("allow", "deny"),
        ]

        # Check negation asymmetry: one text has negation, other doesn't
        neg_a = len(tokens_a & negation_words)
        neg_b = len(tokens_b & negation_words)
        if abs(neg_a - neg_b) >= 1:
            # Shared non-negation content suggests contradiction
            shared_content = (tokens_a - negation_words) & (tokens_b - negation_words)
            if len(shared_content) >= 2:
                return True

        # Check antonym presence
        for word_a, word_b in antonym_pairs:
            if (word_a in tokens_a and word_b in tokens_b) or \
               (word_b in tokens_a and word_a in tokens_b):
                return True

        return False

    @property
    def contradiction_count(self) -> int:
        return len(self.contradictions)

    @property
    def unresolved_count(self) -> int:
        return sum(1 for c in self.contradictions if not c.resolved)

    @property
    def density(self) -> float:
        """Contradictions per 100 claims checked."""
        if self.total_claims_checked == 0:
            return 0.0
        return (self.contradiction_count / self.total_claims_checked) * 100

    @property
    def contradiction_score(self) -> float:
        """Score for METACOG-X: 1.0 = no contradictions, 0.0 = all contradictions.

        Formula: 1.0 - min(density / 10.0, 1.0)
        """
        return max(0.0, 1.0 - min(self.density / 10.0, 1.0))

    def resolve(self, index: int) -> bool:
        """Mark a contradiction as resolved."""
        if 0 <= index < len(self.contradictions):
            self.contradictions[index].resolved = True
            return True
        return False

    def recent(self, count: int = 5) -> List[Contradiction]:
        """Get most recent contradictions."""
        return self.contradictions[-count:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contradiction_count": self.contradiction_count,
            "unresolved_count": self.unresolved_count,
            "density": round(self.density, 2),
            "score": round(self.contradiction_score, 4),
            "scan_count": self.scan_count,
            "total_claims_checked": self.total_claims_checked,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContradictionDetector":
        detector = cls()
        detector.scan_count = data.get("scan_count", 0)
        detector.total_claims_checked = data.get("total_claims_checked", 0)
        return detector
