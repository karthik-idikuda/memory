"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Contradiction Engine                   ║
║  NRNLANG-Ω: ## CLASH — truth conflict detected          ║
╚══════════════════════════════════════════════════════════╝

FORMULA — CONTRADICTION RESOLUTION:

  OLD_SCORE(engram):
    days = (now - last_seen) / 86400
    rec = exp(-λ × days)
    return confidence × rec

  NEW_SCORE(engram):
    return confidence × 1.0

  RESOLVE(old, new):
    if ns > os × SUPERSEDE_MARGIN  → SUPERSEDE (new wins)
    elif os > ns × SUPERSEDE_MARGIN → CONTESTED (old stronger)
    else → TIE_CONTESTED (both uncertain)
"""

import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict, List

from neuronx.config import (
    SUPERSEDE_MARGIN, CONFIDENCE_SUPERSEDE_HIT, CONFIDENCE_CLASH_HIT,
    TRUTH_ACTIVE, TRUTH_EXPIRED, TRUTH_CONTESTED, ZONE_COLD,
    CLASH_JACCARD_GATE,
)
from neuronx.core.node import EngramNode
from neuronx.utils.tokenizer import tokenize, jaccard

logger = logging.getLogger("NEURONX.CLASH")


@dataclass
class ContradictionResult:
    """Result of heuristic contradiction detection."""
    is_contradiction: bool = False
    newer_wins: bool = True
    confidence: float = 0.5
    reason: str = ""


# Negation and update patterns
NEGATION_PATTERNS = [
    ("love", "hate"), ("like", "dislike"), ("yes", "no"),
    ("true", "false"), ("always", "never"), ("good", "bad"),
    ("happy", "sad"), ("hot", "cold"), ("loves", "hates"),
    ("likes", "dislikes"), ("enjoy", "despise"),
]

UPDATE_PHRASES = [
    "no longer", "not anymore", "stopped", "quit", "changed",
    "used to", "switched", "moved from", "moved to",
    "now prefer", "now live", "now work",
]


class ContradictionEngine:
    """
    NRNLANG-Ω: CLASH ENGINE — detects and resolves truth conflicts.

    Uses heuristic detection + temporal scoring for resolution.
    """

    @staticmethod
    def detect_contradiction_heuristic(
        new_text: str,
        old_engram: EngramNode,
    ) -> ContradictionResult:
        """
        Heuristic contradiction detection using:
        1. Negation pattern matching
        2. Update phrase detection
        3. Sentiment opposition with topic overlap
        """
        new_lower = new_text.lower()
        old_lower = old_engram.raw.lower()

        # Check Jaccard similarity first — need topic overlap
        new_tokens = tokenize(new_text)
        old_tokens = tokenize(old_engram.raw)
        sim = jaccard(new_tokens, old_tokens)

        if sim < CLASH_JACCARD_GATE:
            return ContradictionResult(is_contradiction=False, reason="No topic overlap")

        # Check update phrases
        for phrase in UPDATE_PHRASES:
            if phrase in new_lower:
                # Check if topics overlap
                if sim >= 0.15:
                    return ContradictionResult(
                        is_contradiction=True,
                        newer_wins=True,
                        confidence=0.85,
                        reason=f"Update phrase '{phrase}' with topic overlap",
                    )

        # Check negation patterns
        for pos, neg in NEGATION_PATTERNS:
            if (pos in old_lower and neg in new_lower) or \
               (neg in old_lower and pos in new_lower):
                return ContradictionResult(
                    is_contradiction=True,
                    newer_wins=True,
                    confidence=0.80,
                    reason=f"Negation: {pos}↔{neg}",
                )

        # High similarity with different content could be an update
        if sim > 0.5:
            # Substantial overlap but not identical — possible update
            shared = new_tokens & old_tokens
            diff_new = new_tokens - old_tokens
            diff_old = old_tokens - new_tokens
            if diff_new and diff_old:
                return ContradictionResult(
                    is_contradiction=True,
                    newer_wins=True,
                    confidence=0.60,
                    reason="High similarity with content differences",
                )

        return ContradictionResult(is_contradiction=False, reason="No contradiction detected")

    @staticmethod
    def compute_old_score(engram: EngramNode) -> float:
        """OLD_SCORE = confidence × recency"""
        return engram.confidence * engram.recency_score

    @staticmethod
    def compute_new_score(engram: EngramNode) -> float:
        """NEW_SCORE = confidence × 1.0"""
        return engram.confidence

    def resolve(
        self,
        new_engram: EngramNode,
        old_engram: EngramNode,
        detection: ContradictionResult,
    ) -> str:
        """
        NRNLANG-Ω: RESOLVE contradiction.

        Returns: "SUPERSEDED" | "CONTESTED" | "TIE_CONTESTED"
        """
        os_score = self.compute_old_score(old_engram)
        ns_score = self.compute_new_score(new_engram)

        if ns_score > os_score * SUPERSEDE_MARGIN:
            # New wins → old gets expired
            old_engram.valid_until = time.time()
            old_engram.superseded_by = new_engram.id
            old_engram.confidence = max(0.1, old_engram.confidence - CONFIDENCE_SUPERSEDE_HIT)
            old_engram.zone = ZONE_COLD
            old_engram.truth = TRUTH_EXPIRED
            new_engram.truth = TRUTH_ACTIVE
            logger.info(
                f"!!= SUPERSEDE {old_engram.id[:8]}… → {new_engram.id[:8]}…"
            )
            return "SUPERSEDED"

        elif os_score > ns_score * SUPERSEDE_MARGIN:
            # Old wins → new is contested
            new_engram.confidence = max(0.1, new_engram.confidence - CONFIDENCE_CLASH_HIT)
            new_engram.truth = TRUTH_CONTESTED
            old_engram.truth = TRUTH_CONTESTED
            old_engram.contradicts.append(new_engram.id)
            new_engram.contradicts.append(old_engram.id)
            logger.info(
                f"|?| CONTESTED (old wins) {old_engram.id[:8]}… vs {new_engram.id[:8]}…"
            )
            return "CONTESTED"

        else:
            # Tie — both contested
            old_engram.confidence = max(0.1, old_engram.confidence - CONFIDENCE_CLASH_HIT)
            new_engram.confidence = max(0.1, new_engram.confidence - CONFIDENCE_CLASH_HIT)
            old_engram.truth = TRUTH_CONTESTED
            new_engram.truth = TRUTH_CONTESTED
            old_engram.contradicts.append(new_engram.id)
            new_engram.contradicts.append(old_engram.id)
            logger.info(
                f"|?| TIE_CONTESTED {old_engram.id[:8]}… vs {new_engram.id[:8]}…"
            )
            return "TIE_CONTESTED"

    def check_and_resolve(
        self,
        new_engram: EngramNode,
        candidates: Dict[str, EngramNode],
    ) -> Optional[dict]:
        """
        Check new_engram against candidate engrams for contradiction.
        Returns conflict info dict if a contradiction is found.
        """
        for eid, old_engram in candidates.items():
            if eid == new_engram.id:
                continue
            if not old_engram.is_active_engram():
                continue

            detection = self.detect_contradiction_heuristic(new_engram.raw, old_engram)
            if detection.is_contradiction:
                resolution = self.resolve(new_engram, old_engram, detection)
                return {
                    "old_id": old_engram.id,
                    "new_id": new_engram.id,
                    "resolution": resolution,
                    "reason": detection.reason,
                    "confidence": detection.confidence,
                }
        return None
