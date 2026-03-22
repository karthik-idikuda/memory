"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Hallucination Shield                       ║
║  Memory-based evidence grounding for AI responses            ║
╚══════════════════════════════════════════════════════════════╝

Verifies that AI responses are grounded in actual memory evidence.
No external tools or APIs — purely memory-based grounding.

Algorithm: Evidence Grounding Score (EGS)
  For each claim: evidence_ratio = supporting_memories / total_claims
  HallucinationScore = 1.0 - evidence_ratio
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from cortex.config import (
    HALLUCINATION_EVIDENCE_THRESHOLD,
    HALLUCINATION_MEMORY_SCAN_DEPTH,
    HALLUCINATION_ALERT_LEVELS,
)
from cortex.core.tokenizer import (
    extract_claims, tokenize_filtered, semantic_overlap,
)


@dataclass
class EvidenceResult:
    """Result of evidence grounding check for a single claim."""
    claim: str
    evidence_count: int
    best_match_score: float
    best_match_content: str = ""
    best_match_id: str = ""
    is_grounded: bool = False


@dataclass
class ShieldReport:
    """Full hallucination shield analysis for a response."""
    claims: List[EvidenceResult] = field(default_factory=list)
    evidence_ratio: float = 1.0
    hallucination_score: float = 0.0
    alert_level: str = "safe"
    blocked: bool = False
    total_claims: int = 0
    grounded_claims: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_ratio": round(self.evidence_ratio, 4),
            "hallucination_score": round(self.hallucination_score, 4),
            "alert_level": self.alert_level,
            "blocked": self.blocked,
            "total_claims": self.total_claims,
            "grounded_claims": self.grounded_claims,
        }


class HallucinationShield:
    """Memory-based hallucination detection and blocking.

    Scans AI responses against stored memories to verify
    that claims are grounded in evidence.

    Algorithm:
      1. Extract individual claims from response
      2. For each claim, search memories for supporting evidence
      3. Compute evidence ratio = grounded_claims / total_claims
      4. Set alert level based on evidence ratio
      5. Block if evidence ratio < critical threshold
    """

    def __init__(
        self,
        evidence_threshold: float = HALLUCINATION_EVIDENCE_THRESHOLD,
        scan_depth: int = HALLUCINATION_MEMORY_SCAN_DEPTH,
        grounding_threshold: float = 0.35,
    ):
        self.evidence_threshold = evidence_threshold
        self.scan_depth = scan_depth
        self.grounding_threshold = grounding_threshold
        self.history: List[ShieldReport] = []
        self.total_scans: int = 0
        self.total_blocks: int = 0

    def scan(
        self,
        response_content: str,
        memories: List[Dict[str, str]],
        causal_chains: Optional[List[Dict[str, str]]] = None,
    ) -> ShieldReport:
        """Scan a response for hallucinations against available evidence.

        Args:
            response_content: The AI's response text
            memories: List of dicts with 'id' and 'content' keys (from NEURON-X)
            causal_chains: Optional list of causal chain dicts (from SIGMA-X)

        Returns:
            ShieldReport with evidence analysis
        """
        self.total_scans += 1
        claims = extract_claims(response_content)

        if not claims:
            return ShieldReport(evidence_ratio=1.0, alert_level="safe")

        # Combine evidence sources
        evidence_pool: List[Dict[str, str]] = list(memories[:self.scan_depth])
        if causal_chains:
            evidence_pool.extend(causal_chains[:self.scan_depth // 2])

        # Check each claim against evidence
        results: List[EvidenceResult] = []
        grounded = 0

        for claim in claims:
            result = self._check_claim(claim, evidence_pool)
            results.append(result)
            if result.is_grounded:
                grounded += 1

        # Compute scores
        evidence_ratio = grounded / len(claims)
        hallucination_score = 1.0 - evidence_ratio
        alert_level = self._determine_alert_level(evidence_ratio)
        blocked = alert_level == "critical"

        if blocked:
            self.total_blocks += 1

        report = ShieldReport(
            claims=results,
            evidence_ratio=evidence_ratio,
            hallucination_score=hallucination_score,
            alert_level=alert_level,
            blocked=blocked,
            total_claims=len(claims),
            grounded_claims=grounded,
        )

        self.history.append(report)
        return report

    def _check_claim(
        self,
        claim: str,
        evidence_pool: List[Dict[str, str]],
    ) -> EvidenceResult:
        """Check a single claim against the evidence pool."""
        best_score = 0.0
        best_content = ""
        best_id = ""
        evidence_count = 0

        for evidence in evidence_pool:
            content = evidence.get("content", "")
            eid = evidence.get("id", "")
            score = semantic_overlap(claim, content)

            if score > best_score:
                best_score = score
                best_content = content[:200]
                best_id = eid

            if score >= self.grounding_threshold:
                evidence_count += 1

        is_grounded = best_score >= self.grounding_threshold

        return EvidenceResult(
            claim=claim,
            evidence_count=evidence_count,
            best_match_score=best_score,
            best_match_content=best_content,
            best_match_id=best_id,
            is_grounded=is_grounded,
        )

    def _determine_alert_level(self, evidence_ratio: float) -> str:
        """Determine alert level from evidence ratio."""
        for level, (low, high) in HALLUCINATION_ALERT_LEVELS.items():
            if low <= evidence_ratio < high:
                return level
        if evidence_ratio >= 0.7:
            return "safe"
        return "critical"

    @property
    def hallucination_rate(self) -> float:
        """Proportion of responses flagged as hallucinating (warning or worse)."""
        if not self.history:
            return 0.0
        flagged = sum(1 for r in self.history if r.alert_level in ("warning", "critical"))
        return flagged / len(self.history)

    @property
    def hallucination_score(self) -> float:
        """Score for METACOG-X: 1.0 = no hallucinations, 0.0 = all hallucinations."""
        return 1.0 - self.hallucination_rate

    @property
    def block_rate(self) -> float:
        """Proportion of responses blocked."""
        if self.total_scans == 0:
            return 0.0
        return self.total_blocks / self.total_scans

    def recent_reports(self, count: int = 5) -> List[ShieldReport]:
        """Get most recent shield reports."""
        return self.history[-count:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_scans": self.total_scans,
            "total_blocks": self.total_blocks,
            "hallucination_rate": round(self.hallucination_rate, 4),
            "hallucination_score": round(self.hallucination_score, 4),
            "block_rate": round(self.block_rate, 4),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HallucinationShield":
        shield = cls()
        shield.total_scans = data.get("total_scans", 0)
        shield.total_blocks = data.get("total_blocks", 0)
        return shield
