"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — WSRA-X Retrieval Engine                ║
║  NRNLANG-Ω: CORTEX — @7 TOP_SEVEN                       ║
╚══════════════════════════════════════════════════════════╝

FORMULA F — WSRA-X (Weighted Surprise-Resonance Algorithm Extended):

  RESONANCE(engram, query) = {
    (WORD_RESONANCE  × 2.5)  ← Direct content relevance
  + (ZONE_HEAT       × 2.0)  ← Hot memories are hot for a reason
  + (SPARK_LEGACY    × 1.8)  ← Surprising memories stay important
  + (BOND_CENTRALITY × 1.2)  ← Connected = important
  + (RECENCY_CURVE   × 1.5)  ← Recent matters
  + (CONFIDENCE      × 1.0)  ← Trust level
  - (DECAY_DEBT      × 1.3)  ← Penalty for old unused
  - (CLASH_PENALTY   × 0.8)  ← Conflicted but still has value
  } × engram.weight
  → max(0.0, result)

BUG-002 FIX: All 8 components fully implemented with exact weights.
BUG-015 FIX: Pagination support (page, page_size).
"""

import logging
from typing import Optional, List, Tuple, Dict

from neuronx.config import (
    WSRAX_WORD_RESONANCE, WSRAX_ZONE_HEAT, WSRAX_SPARK_LEGACY,
    WSRAX_BOND_CENTRALITY, WSRAX_RECENCY_CURVE, WSRAX_CONFIDENCE,
    WSRAX_DECAY_DEBT, WSRAX_CLASH_PENALTY, DEFAULT_TOP_K,
    DEFAULT_PAGE_SIZE,
)
from neuronx.core.node import EngramNode
from neuronx.utils.tokenizer import tokenize, jaccard

logger = logging.getLogger("NEURONX.CORTEX")


class RetrievalEngine:
    """
    NRNLANG-Ω: CORTEX — The WSRA-X retrieval engine.

    Scores every active engram against a query using
    all 8 weighted components, then returns top-K results.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            "word_resonance": WSRAX_WORD_RESONANCE,
            "zone_heat": WSRAX_ZONE_HEAT,
            "spark_legacy": WSRAX_SPARK_LEGACY,
            "bond_centrality": WSRAX_BOND_CENTRALITY,
            "recency_curve": WSRAX_RECENCY_CURVE,
            "confidence": WSRAX_CONFIDENCE,
            "decay_debt": WSRAX_DECAY_DEBT,
            "clash_penalty": WSRAX_CLASH_PENALTY,
        }

    def score_engram(
        self,
        engram: EngramNode,
        query_tokens: frozenset,
    ) -> Tuple[float, Dict[str, float]]:
        """
        NRNLANG-Ω: FORMULA F — Compute WSRA-X resonance score.

        BUG-002 FIX: All 8 components computed and returned.
        Returns (final_score, component_breakdown).
        """
        engram_tokens = tokenize(engram.raw)

        # ── All 8 Components (BUG-002 FIX) ──
        word_resonance = jaccard(query_tokens, engram_tokens)
        zone_heat = engram.zone_heat_value
        spark_legacy = engram.surprise_score
        bond_centrality = engram.bond_centrality
        recency_curve = engram.recency_score
        confidence = engram.confidence
        decay_debt = engram.decay_debt
        clash_penalty = engram.clash_penalty

        # ── Raw Score: sum of all 8 weighted components ──
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

        # ── Final Score ──
        final_score = max(0.0, raw_score * engram.weight)

        components = {
            "word_resonance": word_resonance * self.weights["word_resonance"],
            "zone_heat": zone_heat * self.weights["zone_heat"],
            "spark_legacy": spark_legacy * self.weights["spark_legacy"],
            "bond_centrality": bond_centrality * self.weights["bond_centrality"],
            "recency_curve": recency_curve * self.weights["recency_curve"],
            "confidence": confidence * self.weights["confidence"],
            "decay_debt": -(decay_debt * self.weights["decay_debt"]),
            "clash_penalty": -(clash_penalty * self.weights["clash_penalty"]),
            "raw_score": raw_score,
            "weight_multiplier": engram.weight,
            "final_score": final_score,
        }

        return final_score, components

    def retrieve(
        self,
        query: str,
        memory_bank: Dict[str, EngramNode],
        top_k: int = DEFAULT_TOP_K,
        page: int = 0,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> List[Tuple[EngramNode, float]]:
        """
        NRNLANG-Ω: CORTEX ?? query → RANKED top[K] @> AI

        BUG-015 FIX: Pagination support.
        Scores all active engrams, returns top_k.
        Updates last_seen and access_count on returned engrams.
        """
        query_tokens = tokenize(query)

        scored = []
        for engram in memory_bank.values():
            if not engram.is_active_engram():
                continue

            score, _ = self.score_engram(engram, query_tokens)
            if score > 0:
                scored.append((engram, score))

        # Sort descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Apply pagination if needed
        if page > 0 or page_size < len(scored):
            start = page * page_size
            end = start + page_size
            scored = scored[start:end]

        # Limit to top_k
        results = scored[:top_k]

        # Update access tracking
        for engram, score in results:
            engram.touch()

        return results

    def find_related(
        self,
        engram: EngramNode,
        memory_bank: Dict[str, EngramNode],
        top_k: int = 5,
    ) -> List[Tuple[EngramNode, float]]:
        """Find engrams most related to a given engram."""
        others = {eid: e for eid, e in memory_bank.items() if eid != engram.id}
        return self.retrieve(engram.raw, others, top_k=top_k)
