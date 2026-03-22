"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — SIGMA Scoring Algorithm                  ║
║  CAULANG-Ω: SIGMA — the 9-component retrieval engine     ║
╚══════════════════════════════════════════════════════════╝

SIGMA = the causal equivalent of NEURON-X's WSRA-X.
9-component weighted scoring for ranking causal chains by relevance.

Formula:
  SIGMA = Σ(component_i × weight_i) / Σ(weight_i)

Components:
  1. CAUSAL_RESONANCE    × 3.0  — word overlap with cause+effect
  2. EVIDENCE_WEIGHT     × 2.5  — tanh(net_evidence / 5.0)
  3. PREDICTION_ACCURACY × 2.0  — correct / total predictions
  4. RECENCY_CURVE       × 1.8  — exp(-λ × age_days)
  5. ZONE_HEAT           × 1.5  — thermal zone value
  6. CHAIN_DEPTH         × 1.2  — log2(1 + chain_length) / 5.0
  7. CONFIDENCE          × 1.0  — node.confidence
  8. DECAY_DEBT          × 1.3  — 1.0 - current_decay
  9. FALSIFICATION_PEN   × 0.8  — penalty for false predictions
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from sigmax.config import (
    SIGMA_CAUSAL_RESONANCE,
    SIGMA_EVIDENCE_WEIGHT,
    SIGMA_PREDICTION_ACCURACY,
    SIGMA_RECENCY_CURVE,
    SIGMA_ZONE_HEAT,
    SIGMA_CHAIN_DEPTH,
    SIGMA_CONFIDENCE,
    SIGMA_DECAY_DEBT,
    SIGMA_FALSIFICATION_PENALTY,
    SIGMA_TOTAL_WEIGHT,
    ZONE_HEAT_VALUES,
    EVIDENCE_TANH_SCALE,
    DEFAULT_TOP_K,
)
from sigmax.core.causenode import CauseNode
from sigmax.core.tokenizer import causal_resonance


def sigma_score(
    node: CauseNode,
    query: str,
    chain_length: int = 1,
) -> float:
    """
    Compute the full 9-component SIGMA score for a CauseNode.

    Higher score = more relevant to the query.
    """
    # Component 1: Causal Resonance (word overlap with cause + effect)
    resonance = causal_resonance(query, node.cause, node.effect)

    # Component 2: Evidence Weight — tanh(net_evidence / scale)
    evidence_raw = math.tanh(node.evidence_net / EVIDENCE_TANH_SCALE)
    evidence_normalized = (evidence_raw + 1.0) / 2.0  # map [-1,1] → [0,1]

    # Component 3: Prediction Accuracy
    pred_accuracy = node.prediction_accuracy

    # Component 4: Recency Curve — exp(-λ × age_days)
    recency = node.get_recency()

    # Component 5: Zone Heat
    zone_heat = ZONE_HEAT_VALUES.get(node.zone, 0.0)

    # Component 6: Chain Depth — log2(1 + length) / 5.0, capped at 1.0
    chain_depth = min(1.0, math.log2(1 + max(1, chain_length)) / 5.0)

    # Component 7: Confidence
    confidence = node.confidence

    # Component 8: Decay Debt — 1.0 - current_decay (higher = less decayed)
    decay_debt = 1.0 - node.current_decay

    # Component 9: Falsification Penalty
    falsification = 0.0
    if node.predictions_made > 0:
        false_ratio = node.predictions_failed / node.predictions_made
        falsification = 1.0 - false_ratio  # 1.0 = no failures, 0.0 = all failed

    # Weighted sum
    score = (
        SIGMA_CAUSAL_RESONANCE * resonance +
        SIGMA_EVIDENCE_WEIGHT * evidence_normalized +
        SIGMA_PREDICTION_ACCURACY * pred_accuracy +
        SIGMA_RECENCY_CURVE * recency +
        SIGMA_ZONE_HEAT * zone_heat +
        SIGMA_CHAIN_DEPTH * chain_depth +
        SIGMA_CONFIDENCE * confidence +
        SIGMA_DECAY_DEBT * decay_debt +
        SIGMA_FALSIFICATION_PENALTY * falsification
    ) / SIGMA_TOTAL_WEIGHT

    return max(0.0, min(1.0, score))


def sigma_score_breakdown(
    node: CauseNode,
    query: str,
    chain_length: int = 1,
) -> dict:
    """
    Compute SIGMA score with detailed component breakdown.
    Useful for debugging and transparency.
    """
    resonance = causal_resonance(query, node.cause, node.effect)
    evidence_raw = math.tanh(node.evidence_net / EVIDENCE_TANH_SCALE)
    evidence_normalized = (evidence_raw + 1.0) / 2.0
    pred_accuracy = node.prediction_accuracy
    recency = node.get_recency()
    zone_heat = ZONE_HEAT_VALUES.get(node.zone, 0.0)
    chain_depth = min(1.0, math.log2(1 + max(1, chain_length)) / 5.0)
    confidence = node.confidence
    decay_debt = 1.0 - node.current_decay

    falsification = 0.0
    if node.predictions_made > 0:
        false_ratio = node.predictions_failed / node.predictions_made
        falsification = 1.0 - false_ratio

    total = (
        SIGMA_CAUSAL_RESONANCE * resonance +
        SIGMA_EVIDENCE_WEIGHT * evidence_normalized +
        SIGMA_PREDICTION_ACCURACY * pred_accuracy +
        SIGMA_RECENCY_CURVE * recency +
        SIGMA_ZONE_HEAT * zone_heat +
        SIGMA_CHAIN_DEPTH * chain_depth +
        SIGMA_CONFIDENCE * confidence +
        SIGMA_DECAY_DEBT * decay_debt +
        SIGMA_FALSIFICATION_PENALTY * falsification
    ) / SIGMA_TOTAL_WEIGHT

    return {
        'total_score': max(0.0, min(1.0, total)),
        'components': {
            'causal_resonance': {
                'value': resonance,
                'weight': SIGMA_CAUSAL_RESONANCE,
                'weighted': SIGMA_CAUSAL_RESONANCE * resonance,
            },
            'evidence_weight': {
                'value': evidence_normalized,
                'weight': SIGMA_EVIDENCE_WEIGHT,
                'weighted': SIGMA_EVIDENCE_WEIGHT * evidence_normalized,
            },
            'prediction_accuracy': {
                'value': pred_accuracy,
                'weight': SIGMA_PREDICTION_ACCURACY,
                'weighted': SIGMA_PREDICTION_ACCURACY * pred_accuracy,
            },
            'recency_curve': {
                'value': recency,
                'weight': SIGMA_RECENCY_CURVE,
                'weighted': SIGMA_RECENCY_CURVE * recency,
            },
            'zone_heat': {
                'value': zone_heat,
                'weight': SIGMA_ZONE_HEAT,
                'weighted': SIGMA_ZONE_HEAT * zone_heat,
            },
            'chain_depth': {
                'value': chain_depth,
                'weight': SIGMA_CHAIN_DEPTH,
                'weighted': SIGMA_CHAIN_DEPTH * chain_depth,
            },
            'confidence': {
                'value': confidence,
                'weight': SIGMA_CONFIDENCE,
                'weighted': SIGMA_CONFIDENCE * confidence,
            },
            'decay_debt': {
                'value': decay_debt,
                'weight': SIGMA_DECAY_DEBT,
                'weighted': SIGMA_DECAY_DEBT * decay_debt,
            },
            'falsification_penalty': {
                'value': falsification,
                'weight': SIGMA_FALSIFICATION_PENALTY,
                'weighted': SIGMA_FALSIFICATION_PENALTY * falsification,
            },
        },
        'node_id': node.id,
        'cause': node.cause,
        'effect': node.effect,
    }


def sigma_rank(
    nodes: List[CauseNode],
    query: str,
    top_k: int = DEFAULT_TOP_K,
    chain_lengths: Optional[dict] = None,
) -> List[Tuple[CauseNode, float]]:
    """
    Rank a list of CauseNodes by SIGMA score against a query.

    Args:
        nodes: List of CauseNodes to rank
        query: Search query string
        top_k: Number of top results to return
        chain_lengths: Optional dict mapping node.id → chain length

    Returns:
        List of (node, score) tuples, sorted by score descending.
    """
    if not nodes or not query:
        return []

    if chain_lengths is None:
        chain_lengths = {}

    scored = []
    for node in nodes:
        length = chain_lengths.get(node.id, 1)
        score = sigma_score(node, query, chain_length=length)
        scored.append((node, score))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Touch accessed nodes (record the access)
    for node, _ in scored[:top_k]:
        node.touch()

    return scored[:top_k]


def sigma_filter(
    nodes: List[CauseNode],
    query: str,
    min_score: float = 0.1,
    chain_lengths: Optional[dict] = None,
) -> List[Tuple[CauseNode, float]]:
    """
    Filter nodes by minimum SIGMA score threshold.
    Returns all nodes above the threshold, sorted by score.
    """
    if not nodes or not query:
        return []

    if chain_lengths is None:
        chain_lengths = {}

    results = []
    for node in nodes:
        length = chain_lengths.get(node.id, 1)
        score = sigma_score(node, query, chain_length=length)
        if score >= min_score:
            results.append((node, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
