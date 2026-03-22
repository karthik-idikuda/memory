"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Axiom Crystallization Engine             ║
║  CAULANG-Ω: AXIOM — truth hardened into permanence        ║
╚══════════════════════════════════════════════════════════╝

When a causal chain has:
  - High confidence (>= 0.95)
  - Strong evidence (net >= 10)
  - Many accesses (>= 15)
  - Good prediction track record (>= 80%)
...it crystallizes into an AXIOM — permanent, undecaying truth.
"""

from __future__ import annotations

import time
from typing import Dict, List, Tuple

from sigmax.config import (
    AXIOM_CONFIDENCE_THRESHOLD,
    AXIOM_ACCESS_THRESHOLD,
    AXIOM_EVIDENCE_NET_THRESHOLD,
    AXIOM_PREDICTION_ACCURACY_THRESHOLD,
    ZONE_AXIOM,
)
from sigmax.core.causenode import CauseNode


class AxiomEngine:
    """Manages crystallization of causal chains into axioms."""

    def __init__(self):
        self._crystallization_count = 0
        self._crystallization_log: List[dict] = []

    def check_candidate(self, node: CauseNode) -> Tuple[bool, List[str]]:
        """
        Check if a node is eligible for axiom crystallization.
        Returns (eligible, list_of_unmet_criteria).
        """
        unmet = []

        if node.confidence < AXIOM_CONFIDENCE_THRESHOLD:
            unmet.append(
                f"confidence {node.confidence:.2f} < {AXIOM_CONFIDENCE_THRESHOLD}"
            )
        if node.access_count < AXIOM_ACCESS_THRESHOLD:
            unmet.append(
                f"access_count {node.access_count} < {AXIOM_ACCESS_THRESHOLD}"
            )
        if node.evidence_net < AXIOM_EVIDENCE_NET_THRESHOLD:
            unmet.append(
                f"evidence_net {node.evidence_net} < {AXIOM_EVIDENCE_NET_THRESHOLD}"
            )
        if (node.predictions_made > 0 and
                node.prediction_accuracy < AXIOM_PREDICTION_ACCURACY_THRESHOLD):
            unmet.append(
                f"prediction_accuracy {node.prediction_accuracy:.0%} < "
                f"{AXIOM_PREDICTION_ACCURACY_THRESHOLD:.0%}"
            )

        return len(unmet) == 0, unmet

    def crystallize(self, node: CauseNode) -> bool:
        """
        Attempt to crystallize a node into an AXIOM.
        Returns True if crystallization succeeded.
        """
        eligible, unmet = self.check_candidate(node)
        if not eligible:
            return False

        success = node.crystallize()
        if success:
            self._crystallization_count += 1
            self._crystallization_log.append({
                'node_id': node.id,
                'cause': node.cause,
                'effect': node.effect,
                'confidence': node.confidence,
                'evidence_net': node.evidence_net,
                'access_count': node.access_count,
                'crystallized_at': time.time(),
            })
        return success

    def scan_and_crystallize(self, nodes: List[CauseNode]) -> List[CauseNode]:
        """
        Scan all nodes and crystallize eligible ones.
        Returns list of newly crystallized nodes.
        """
        crystallized = []
        for node in nodes:
            if node.zone == ZONE_AXIOM:
                continue  # already axiom
            if self.crystallize(node):
                crystallized.append(node)
        return crystallized

    def get_axiom_candidates(self, nodes: List[CauseNode]) -> List[Tuple[CauseNode, List[str]]]:
        """
        Find nodes close to axiom status.
        Returns nodes with at most 1 unmet criterion.
        """
        candidates = []
        for node in nodes:
            if node.zone == ZONE_AXIOM:
                continue
            eligible, unmet = self.check_candidate(node)
            if len(unmet) <= 1:
                candidates.append((node, unmet))
        return candidates

    def decrystallize(self, node: CauseNode) -> bool:
        """
        Remove axiom status from a node.
        Used when evidence contradicts an axiom.
        """
        if node.zone != ZONE_AXIOM:
            return False

        node.zone = "ACTIVE"
        node.decay_class = "slow"
        node.caulang_notation = node.to_caulang()
        return True

    @property
    def stats(self) -> dict:
        return {
            'total_crystallizations': self._crystallization_count,
            'log_entries': len(self._crystallization_log),
        }

    @property
    def crystallization_log(self) -> List[dict]:
        return list(self._crystallization_log)
