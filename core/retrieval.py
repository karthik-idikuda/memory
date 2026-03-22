"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — WSRA-X Retrieval Engine                ║
║  NRNLANG-Ω: CORTEX — The retrieval engine                ║
║  @7 TOP_SEVEN → inject 7 most relevant memories          ║
╚══════════════════════════════════════════════════════════╝

FORMULA F — THE WSRA-X RETRIEVAL SCORE (Master Formula):

  RESONANCE(engram, query) = {
    (WORD_RESONANCE  × 2.5)
  + (ZONE_HEAT       × 2.0)
  + (SPARK_LEGACY    × 1.8)
  + (BOND_CENTRALITY × 1.2)
  + (RECENCY_CURVE   × 1.5)
  + (CONFIDENCE      × 1.0)
  - (DECAY_DEBT      × 1.3)
  - (CLASH_PENALTY   × 0.8)
  }
  × engram.weight
  → RANKED top[7] @> AI
"""

import logging
from typing import Optional

from core.node import Engram
from core.surprise import Amygdala

logger = logging.getLogger("NEURONX.CORTEX")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WSRA-X WEIGHT COEFFICIENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_WEIGHTS = {
    "word_resonance":   2.5,  # Direct relevance — matters most
    "zone_heat":        2.0,  # Hot memories are hot for a reason
    "spark_legacy":     1.8,  # Surprising memories stay important
    "recency_curve":    1.5,  # Recent matters a lot
    "bond_centrality":  1.2,  # Connected = important
    "confidence":       1.0,  # Trust matters
    "decay_debt":       1.3,  # Old unused = less relevant (penalty)
    "clash_penalty":    0.8,  # Conflicted memories still have value (softer)
}


class RetrievalEngine:
    """
    NRNLANG-Ω: CORTEX — The retrieval engine.

    Finds the most relevant memories for any query using
    the WSRA-X multi-component scoring formula.
    """

    def __init__(self, weights: Optional[dict] = None):
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self.amygdala = Amygdala()

    def compute_word_resonance(
        self, query_tokens: set, engram_tokens: set
    ) -> float:
        """
        WORD_RESONANCE = |query ∩ engram| / |query ∪ engram|
        Range: 0.0 to 1.0
        """
        return self.amygdala.jaccard_similarity(query_tokens, engram_tokens)

    def score_engram(
        self,
        engram: Engram,
        query_tokens: set,
    ) -> float:
        """
        NRNLANG-Ω: FORMULA F — Compute WSRA-X resonance score.

        RESONANCE = {
          (WORD_RESONANCE  × W1) +
          (ZONE_HEAT       × W2) +
          (SPARK_LEGACY    × W3) +
          (BOND_CENTRALITY × W4) +
          (RECENCY_CURVE   × W5) +
          (CONFIDENCE      × W6) -
          (DECAY_DEBT      × W7) -
          (CLASH_PENALTY   × W8)
        } × weight
        """
        engram_tokens = self.amygdala.tokenize(engram.raw)

        # ── 8 Components ──
        word_resonance = self.compute_word_resonance(query_tokens, engram_tokens)
        zone_heat = engram.zone_heat_value
        spark_legacy = engram.spark
        bond_centrality = engram.bond_centrality
        recency_curve = engram.recency_score
        confidence = engram.confidence
        decay_debt = engram.decay_debt
        clash_penalty = engram.clash_penalty

        # ── Compute Raw Score ──
        raw_score = (
            (word_resonance   * self.weights["word_resonance"])
            + (zone_heat      * self.weights["zone_heat"])
            + (spark_legacy   * self.weights["spark_legacy"])
            + (bond_centrality * self.weights["bond_centrality"])
            + (recency_curve  * self.weights["recency_curve"])
            + (confidence     * self.weights["confidence"])
            - (decay_debt     * self.weights["decay_debt"])
            - (clash_penalty  * self.weights["clash_penalty"])
        )

        # ── Apply Weight Multiplier ──
        final_score = max(0.0, raw_score * engram.weight)

        return final_score

    def query(
        self,
        query_text: str,
        engrams: list[Engram],
        top_k: int = 7,
        min_score: float = 0.0,
    ) -> list[tuple[Engram, float]]:
        """
        NRNLANG-Ω: CORTEX ?? query → RANKED top[K] @> AI

        Score all engrams against the query and return the top K.

        Returns:
            List of (engram, score) tuples, sorted by score descending.
        """
        query_tokens = self.amygdala.tokenize(query_text)

        if not query_tokens:
            # Empty query — return hottest engrams
            scored = [(e, e.heat * e.weight) for e in engrams if e.is_active]
        else:
            scored = []
            for engram in engrams:
                if not engram.is_active and not engram.truth == "|!|":
                    continue  # Skip expired, keep conflicted

                score = self.score_engram(engram, query_tokens)
                if score >= min_score:
                    scored.append((engram, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Update access tracking on selected engrams
        for engram, score in scored[:top_k]:
            engram.touch()

        return scored[:top_k]

    def find_related(
        self,
        engram: Engram,
        all_engrams: list[Engram],
        top_k: int = 5,
    ) -> list[tuple[Engram, float]]:
        """
        Find engrams most related to a given engram.
        Uses the engram's raw text as the query.
        """
        others = [e for e in all_engrams if e.id != engram.id]
        return self.query(engram.raw, others, top_k=top_k)

    def format_for_injection(
        self,
        results: list[tuple[Engram, float]],
    ) -> str:
        """
        NRNLANG-Ω: @> PUSH_TO_AI — format results for AI context.
        """
        from interface.prompts import format_memory_for_injection

        lines = []
        for i, (engram, score) in enumerate(results, 1):
            lines.append(format_memory_for_injection(engram, i))

        return "\n".join(lines) if lines else "(No relevant memories found)"
