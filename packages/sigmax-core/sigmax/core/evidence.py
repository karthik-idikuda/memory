"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Evidence Accumulation Engine             ║
║  CAULANG-Ω: EVIDENCE — truth strengthens, lies weaken    ║
╚══════════════════════════════════════════════════════════╝

Manages evidence for/against causal chains.
Each piece of evidence adjusts node confidence.

Evidence Score = tanh(net_evidence / TANH_SCALE)
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import List, Optional

from sigmax.config import (
    EVIDENCE_SUPPORT_BOOST,
    EVIDENCE_CONTRADICT_HIT,
    EVIDENCE_TANH_SCALE,
    CONFIDENCE_MIN,
    CONFIDENCE_MAX,
    CAULANG_EVIDENCE_SYMBOLS,
)
from sigmax.core.causenode import CauseNode
from sigmax.exceptions import EvidenceError, EvidenceConflictError


@dataclass
class EvidenceRecord:
    """
    A single piece of evidence for or against a causal chain.
    """
    id: str = ""
    chain_id: str = ""
    is_support: bool = True
    text: str = ""
    confidence: float = 1.0
    source: str = "inference"
    timestamp: float = field(default_factory=time.time)

    @property
    def evidence_type(self) -> str:
        return "support" if self.is_support else "contradict"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'chain_id': self.chain_id,
            'is_support': self.is_support,
            'text': self.text,
            'confidence': self.confidence,
            'source': self.source,
            'timestamp': self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EvidenceRecord':
        return cls(**{k: v for k, v in data.items()
                      if k in cls.__dataclass_fields__})

    def to_caulang(self) -> str:
        sym = CAULANG_EVIDENCE_SYMBOLS.get(
            "SUPPORT" if self.is_support else "CONTRADICT", "[~]"
        )
        return f'{sym} "{self.text}" (conf={self.confidence:.2f})'


class EvidenceEngine:
    """
    Manages evidence accumulation for CauseNodes.

    Operations:
    - add_support: add supporting evidence
    - add_contradiction: add contradicting evidence
    - compute_evidence_score: tanh-normalized net evidence
    - get_evidence_summary: human-readable summary
    """

    def __init__(self):
        # chain_id → list of EvidenceRecord
        self._evidence_store: dict[str, List[EvidenceRecord]] = {}

    @property
    def total_evidence_count(self) -> int:
        return sum(len(v) for v in self._evidence_store.values())

    def add_support(
        self,
        node: CauseNode,
        text: str,
        confidence: float = 1.0,
        source: str = "inference",
    ) -> EvidenceRecord:
        """
        Add supporting evidence for a causal chain.
        Increases node confidence by EVIDENCE_SUPPORT_BOOST.
        """
        record = EvidenceRecord(
            id=f"ev_{node.id[:8]}_{int(time.time())}",
            chain_id=node.id,
            is_support=True,
            text=text,
            confidence=confidence,
            source=source,
        )

        if node.id not in self._evidence_store:
            self._evidence_store[node.id] = []
        self._evidence_store[node.id].append(record)

        # Update node
        node.add_evidence(is_support=True)

        return record

    def add_contradiction(
        self,
        node: CauseNode,
        text: str,
        confidence: float = 1.0,
        source: str = "inference",
    ) -> EvidenceRecord:
        """
        Add contradicting evidence against a causal chain.
        Decreases node confidence by EVIDENCE_CONTRADICT_HIT.
        """
        record = EvidenceRecord(
            id=f"ev_{node.id[:8]}_{int(time.time())}",
            chain_id=node.id,
            is_support=False,
            text=text,
            confidence=confidence,
            source=source,
        )

        if node.id not in self._evidence_store:
            self._evidence_store[node.id] = []
        self._evidence_store[node.id].append(record)

        # Check for strong conflict
        if (node.confidence >= 0.80 and confidence >= 0.80):
            # Strong evidence against a strong chain — flag it
            pass  # Note: we still add it, but the brain can handle the conflict

        # Update node
        node.add_evidence(is_support=False)

        return record

    def compute_evidence_score(self, node: CauseNode) -> float:
        """
        Compute normalized evidence score.
        score = tanh(net_evidence / TANH_SCALE)
        Returns value in [-1, 1].
        """
        return math.tanh(node.evidence_net / EVIDENCE_TANH_SCALE)

    def compute_evidence_score_normalized(self, node: CauseNode) -> float:
        """
        Compute evidence score normalized to [0, 1].
        Used in SIGMA scoring.
        """
        raw = self.compute_evidence_score(node)
        return (raw + 1.0) / 2.0

    def get_evidence(self, chain_id: str) -> List[EvidenceRecord]:
        """Get all evidence records for a chain."""
        return self._evidence_store.get(chain_id, [])

    def get_support_evidence(self, chain_id: str) -> List[EvidenceRecord]:
        """Get only supporting evidence for a chain."""
        return [e for e in self.get_evidence(chain_id) if e.is_support]

    def get_contradiction_evidence(self, chain_id: str) -> List[EvidenceRecord]:
        """Get only contradicting evidence for a chain."""
        return [e for e in self.get_evidence(chain_id) if not e.is_support]

    def get_evidence_summary(self, node: CauseNode) -> dict:
        """
        Get a summary of evidence for a node.
        """
        records = self.get_evidence(node.id)
        support_count = sum(1 for r in records if r.is_support)
        contra_count = sum(1 for r in records if not r.is_support)

        return {
            'chain_id': node.id,
            'total_evidence': len(records),
            'support_count': support_count,
            'contradiction_count': contra_count,
            'net_evidence': support_count - contra_count,
            'evidence_score': self.compute_evidence_score(node),
            'evidence_score_normalized': self.compute_evidence_score_normalized(node),
            'node_evidence_for': node.evidence_for,
            'node_evidence_against': node.evidence_against,
        }

    def clear_evidence(self, chain_id: str) -> int:
        """Clear all evidence for a chain. Returns count removed."""
        records = self._evidence_store.pop(chain_id, [])
        return len(records)

    def to_dict_list(self) -> List[dict]:
        """Serialize all evidence records for persistence."""
        result = []
        for records in self._evidence_store.values():
            for r in records:
                result.append(r.to_dict())
        return result

    def load_from_list(self, evidence_list: List[dict]) -> int:
        """Load evidence records from serialized list. Returns count loaded."""
        count = 0
        for data in evidence_list:
            try:
                record = EvidenceRecord.from_dict(data)
                chain_id = record.chain_id
                if chain_id not in self._evidence_store:
                    self._evidence_store[chain_id] = []
                self._evidence_store[chain_id].append(record)
                count += 1
            except Exception:
                continue
        return count
