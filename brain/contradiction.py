"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Contradiction Engine                   ║
║  NRNLANG-Ω: ## CLASH — direct contradiction detected     ║
╚══════════════════════════════════════════════════════════╝

Detects and resolves contradictions between engrams.
Uses AI when available, falls back to heuristic scoring.

Resolution outcomes:
  SUPERSEDE  → new truth replaces old truth (new wins by >10%)
  CONTESTED  → both kept as competing truths
  NOT_CLASH  → not actually a contradiction
"""

import json
import time
import logging
from typing import Optional

from core.node import (
    Engram, TRUTH_ACTIVE, TRUTH_EXPIRED, TRUTH_CONFLICT,
)
from core.surprise import Amygdala

logger = logging.getLogger("NEURONX.CLASH")


class ContradictionResult:
    """Result of a contradiction check."""

    def __init__(
        self,
        is_contradiction: bool = False,
        contradiction_type: str = "unrelated",
        newer_wins: Optional[bool] = None,
        confidence: float = 0.5,
        reason: str = "",
    ):
        self.is_contradiction = is_contradiction
        self.contradiction_type = contradiction_type
        self.newer_wins = newer_wins
        self.confidence = confidence
        self.reason = reason


class ContradictionEngine:
    """
    NRNLANG-Ω: CONTRADICTION_ENGINE — resolves ## CLASH between engrams.

    FORMULA I — CONTRADICTION RESOLUTION:
      SCORE_OLD = old.confidence × RECENCY(old.last_seen, old.decay_rate)
      SCORE_NEW = new.confidence × 1.0

      IF SCORE_NEW > SCORE_OLD × 1.10  → SUPERSEDE (new wins)
      ELIF SCORE_OLD > SCORE_NEW × 1.10 → CONTESTED (old wins)
      ELSE → BOTH_CONTESTED (too close to call)
    """

    def __init__(self, ai_client=None, model: str = "claude-sonnet-4-20250514"):
        self.ai_client = ai_client
        self.model = model
        self.amygdala = Amygdala()

    def detect_contradiction_heuristic(
        self,
        new_text: str,
        existing: Engram,
    ) -> ContradictionResult:
        """
        Heuristic contradiction detection (no AI needed).
        Uses token overlap and negation pattern matching.
        """
        new_tokens = self.amygdala.tokenize(new_text)
        old_tokens = self.amygdala.tokenize(existing.raw)

        similarity = self.amygdala.jaccard_similarity(new_tokens, old_tokens)

        # Check for negation patterns
        new_lower = new_text.lower()
        old_lower = existing.raw.lower()

        negation_pairs = [
            ("love", "hate"), ("like", "dislike"), ("enjoy", "hate"),
            ("live in", "moved from"), ("work at", "left"),
            ("am", "am not"), ("is", "isn't"), ("can", "can't"),
            ("do", "don't"), ("will", "won't"), ("yes", "no"),
            ("true", "false"), ("right", "wrong"),
            ("always", "never"), ("everyone", "no one"),
            ("best", "worst"), ("prefer", "avoid"),
        ]

        negation_detected = False
        for pos, neg in negation_pairs:
            if (pos in new_lower and neg in old_lower) or \
               (neg in new_lower and pos in old_lower):
                negation_detected = True
                break

        # "used to" / "no longer" / "anymore" signals updates
        update_signals = ["used to", "no longer", "anymore", "stopped", "changed", "moved"]
        is_update = any(sig in new_lower for sig in update_signals)

        if similarity > 0.3 and negation_detected:
            return ContradictionResult(
                is_contradiction=True,
                contradiction_type="direct_opposite",
                newer_wins=True,
                confidence=0.75,
                reason="Negation pattern detected with high topic overlap",
            )

        if similarity > 0.3 and is_update:
            return ContradictionResult(
                is_contradiction=True,
                contradiction_type="update",
                newer_wins=True,
                confidence=0.80,
                reason="Update language detected (used to / no longer / moved)",
            )

        if similarity > 0.5:
            # High overlap but no negation — drift or refinement
            return ContradictionResult(
                is_contradiction=False,
                contradiction_type="unrelated",
                newer_wins=None,
                confidence=0.60,
                reason="High similarity but no contradiction detected",
            )

        return ContradictionResult(
            is_contradiction=False,
            contradiction_type="unrelated",
            newer_wins=None,
            confidence=0.70,
            reason="Low similarity — different topics",
        )

    def detect_contradiction_ai(
        self,
        new_text: str,
        existing: Engram,
    ) -> ContradictionResult:
        """
        AI-powered contradiction detection using Prompt 3.
        Falls back to heuristic if AI is unavailable.
        """
        if not self.ai_client:
            return self.detect_contradiction_heuristic(new_text, existing)

        try:
            from interface.prompts import CONTRADICTION_DETECTION_PROMPT

            old_date = time.strftime(
                "%Y-%m-%d", time.localtime(existing.born)
            )

            prompt = CONTRADICTION_DETECTION_PROMPT.format(
                old_date=old_date,
                old_memory_text=existing.raw,
                old_confidence=f"{existing.confidence:.2f}",
                new_statement=new_text,
            )

            response = self.ai_client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse JSON response
            response_text = response.content[0].text.strip()
            # Clean up possible markdown code fences
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]

            data = json.loads(response_text)

            newer_wins = data.get("newer_wins")
            if isinstance(newer_wins, str):
                newer_wins = True if newer_wins.lower() == "true" else (
                    False if newer_wins.lower() == "false" else None
                )

            return ContradictionResult(
                is_contradiction=data.get("is_contradiction", False),
                contradiction_type=data.get("contradiction_type", "unrelated"),
                newer_wins=newer_wins,
                confidence=data.get("confidence_in_decision", 0.5),
                reason=data.get("reason", ""),
            )

        except Exception as e:
            logger.warning(f"AI contradiction check failed, using heuristic: {e}")
            return self.detect_contradiction_heuristic(new_text, existing)

    def resolve(
        self,
        new_engram: Engram,
        old_engram: Engram,
        result: ContradictionResult,
    ) -> str:
        """
        NRNLANG-Ω: FORMULA I — CONTRADICTION RESOLUTION

        Applies the resolution based on scoring.
        Returns: "SUPERSEDED", "CONTESTED", "NOT_CLASH"
        """
        if not result.is_contradiction:
            return "NOT_CLASH"

        # Compute scores
        score_old = old_engram.confidence * old_engram.recency_score
        score_new = new_engram.confidence * 1.0  # New = full recency

        if result.newer_wins is True or score_new > score_old * 1.10:
            # ── SUPERSEDE — New truth replaces old ──
            logger.info(
                f"## SUPERSEDE: '{old_engram.raw[:40]}…' "
                f"⊖ -| EXPIRED → '{new_engram.raw[:40]}…' ◈ |-"
            )

            old_engram.expire(superseded_by_id=new_engram.id)
            new_engram.truth = TRUTH_ACTIVE

            # Cross-reference
            old_engram.contradicts.append(new_engram.id)
            new_engram.contradicts.append(old_engram.id)

            return "SUPERSEDED"

        elif result.newer_wins is False or score_old > score_new * 1.10:
            # ── Old wins — mark new as contested ──
            logger.info(
                f"## CONTESTED (old wins): '{new_engram.raw[:40]}…' |?|"
            )

            new_engram.truth = TRUTH_CONFLICT
            old_engram.truth = TRUTH_CONFLICT
            new_engram.doubt(0.10)
            old_engram.doubt(0.10)

            # Cross-reference
            old_engram.contradicts.append(new_engram.id)
            new_engram.contradicts.append(old_engram.id)

            return "CONTESTED"

        else:
            # ── Too close to call — both contested ──
            logger.info(
                f"## CONTESTED (unclear): both '{old_engram.raw[:30]}…' "
                f"and '{new_engram.raw[:30]}…' |?|"
            )

            old_engram.truth = TRUTH_CONFLICT
            new_engram.truth = TRUTH_CONFLICT
            old_engram.doubt(0.10)
            new_engram.doubt(0.10)

            old_engram.contradicts.append(new_engram.id)
            new_engram.contradicts.append(old_engram.id)

            return "CONTESTED"
