"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Prediction Engine                        ║
║  CAULANG-Ω: PREDICT — foresee what will happen            ║
╚══════════════════════════════════════════════════════════╝

Generates, stores, and verifies predictions based on causal chains.
Each prediction has a horizon and confidence.
Verification updates the source chain's confidence.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from sigmax.config import (
    PREDICTION_STATUS_PENDING,
    PREDICTION_STATUS_VERIFIED,
    PREDICTION_STATUS_FALSIFIED,
    PREDICTION_STATUS_EXPIRED,
    PREDICTION_HORIZONS,
    PREDICTION_CONFIDENCE_BOOST,
    PREDICTION_CONFIDENCE_HIT,
    PROMPT_PREDICT,
    PROMPT_VERIFY_PREDICTION,
    CAULANG_PREDICTION_SYMBOLS,
)
from sigmax.core.causenode import CauseNode
from sigmax.core.integrity import generate_prediction_id
from sigmax.exceptions import PredictionError, PredictionNotFoundError, PredictionExpiredError


@dataclass
class Prediction:
    """A single prediction derived from a causal chain."""
    id: str = field(default_factory=generate_prediction_id)
    chain_id: str = ""
    prediction_text: str = ""
    confidence: float = 0.50
    horizon: str = "medium"
    horizon_days: int = 30
    reasoning: str = ""
    conditions: list = field(default_factory=list)
    status: str = PREDICTION_STATUS_PENDING
    created_at: float = field(default_factory=time.time)
    verified_at: Optional[float] = None
    verification_evidence: str = ""
    accuracy: float = 0.0

    @property
    def is_expired(self) -> bool:
        """Check if the prediction horizon has passed."""
        age_days = (time.time() - self.created_at) / 86400.0
        return age_days > self.horizon_days and self.status == PREDICTION_STATUS_PENDING

    @property
    def age_days(self) -> float:
        return (time.time() - self.created_at) / 86400.0

    @property
    def days_remaining(self) -> float:
        """Days until horizon expires. Negative if expired."""
        return self.horizon_days - self.age_days

    @property
    def status_symbol(self) -> str:
        return CAULANG_PREDICTION_SYMBOLS.get(self.status, "→?")

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'chain_id': self.chain_id,
            'prediction_text': self.prediction_text,
            'confidence': self.confidence,
            'horizon': self.horizon,
            'horizon_days': self.horizon_days,
            'reasoning': self.reasoning,
            'conditions': self.conditions,
            'status': self.status,
            'created_at': self.created_at,
            'verified_at': self.verified_at,
            'verification_evidence': self.verification_evidence,
            'accuracy': self.accuracy,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Prediction':
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    def to_caulang(self) -> str:
        sym = self.status_symbol
        return (
            f'{sym} "{self.prediction_text}" '
            f'(conf={self.confidence:.2f}, horizon={self.horizon}, '
            f'days_left={self.days_remaining:.0f})'
        )


class PredictionEngine:
    """
    Generates, stores, and verifies predictions.

    Operations:
    - generate: create predictions from chains (rule-based or AI)
    - verify: check if predictions came true
    - check_horizons: expire overdue predictions
    - get_accuracy: compute overall prediction accuracy
    """

    def __init__(self):
        self._predictions: Dict[str, Prediction] = {}  # id → Prediction
        self._chain_predictions: Dict[str, List[str]] = {}  # chain_id → [pred_ids]

    @property
    def total_predictions(self) -> int:
        return len(self._predictions)

    @property
    def pending_count(self) -> int:
        return sum(1 for p in self._predictions.values()
                   if p.status == PREDICTION_STATUS_PENDING)

    @property
    def verified_count(self) -> int:
        return sum(1 for p in self._predictions.values()
                   if p.status == PREDICTION_STATUS_VERIFIED)

    @property
    def falsified_count(self) -> int:
        return sum(1 for p in self._predictions.values()
                   if p.status == PREDICTION_STATUS_FALSIFIED)

    def generate(
        self,
        node: CauseNode,
        prediction_text: str,
        confidence: float = 0.50,
        horizon: str = "medium",
        reasoning: str = "",
        conditions: Optional[List[str]] = None,
    ) -> Prediction:
        """
        Create a prediction from a causal chain.
        """
        horizon_days = PREDICTION_HORIZONS.get(horizon, 30)

        pred = Prediction(
            chain_id=node.id,
            prediction_text=prediction_text,
            confidence=confidence,
            horizon=horizon,
            horizon_days=horizon_days,
            reasoning=reasoning,
            conditions=conditions or [],
        )

        self._predictions[pred.id] = pred
        if node.id not in self._chain_predictions:
            self._chain_predictions[node.id] = []
        self._chain_predictions[node.id].append(pred.id)

        return pred

    def generate_with_ai(
        self,
        node: CauseNode,
        context: str,
        llm_fn: Callable[[str], str],
    ) -> Optional[Prediction]:
        """Generate a prediction using AI/LLM."""
        prompt = PROMPT_PREDICT.format(
            chain=f"{node.cause} → {node.effect}",
            context=context,
        )

        try:
            response = llm_fn(prompt)
            data = self._parse_json_response(response)

            if not data or 'prediction' not in data:
                return None

            return self.generate(
                node=node,
                prediction_text=data['prediction'],
                confidence=float(data.get('confidence', 0.50)),
                horizon=data.get('horizon', 'medium'),
                reasoning=data.get('reasoning', ''),
                conditions=data.get('conditions', []),
            )
        except Exception:
            return None

    def verify(
        self,
        prediction_id: str,
        is_correct: bool,
        evidence: str = "",
        source_node: Optional[CauseNode] = None,
    ) -> Prediction:
        """
        Verify a prediction as correct or incorrect.
        Updates the source chain's confidence accordingly.
        """
        pred = self._predictions.get(prediction_id)
        if not pred:
            raise PredictionNotFoundError(f"Prediction {prediction_id} not found")

        if pred.status != PREDICTION_STATUS_PENDING:
            raise PredictionError(
                f"Prediction {prediction_id} already {pred.status}"
            )

        pred.verified_at = time.time()
        pred.verification_evidence = evidence

        if is_correct:
            pred.status = PREDICTION_STATUS_VERIFIED
            pred.accuracy = 1.0
        else:
            pred.status = PREDICTION_STATUS_FALSIFIED
            pred.accuracy = 0.0

        # Update source chain if provided
        if source_node:
            source_node.record_prediction(correct=is_correct)

        return pred

    def verify_with_ai(
        self,
        prediction_id: str,
        context: str,
        source_node: CauseNode,
        llm_fn: Callable[[str], str],
    ) -> Optional[Prediction]:
        """Verify a prediction using AI/LLM."""
        pred = self._predictions.get(prediction_id)
        if not pred:
            raise PredictionNotFoundError(f"Prediction {prediction_id} not found")

        prompt = PROMPT_VERIFY_PREDICTION.format(
            prediction=pred.prediction_text,
            days_ago=f"{pred.age_days:.0f}",
            context=context,
            cause=source_node.cause,
            effect=source_node.effect,
        )

        try:
            response = llm_fn(prompt)
            data = self._parse_json_response(response)

            if not data:
                return None

            is_verified = data.get('is_verified', False)
            evidence = data.get('evidence', '')

            return self.verify(
                prediction_id=prediction_id,
                is_correct=is_verified,
                evidence=evidence,
                source_node=source_node,
            )
        except Exception:
            return None

    def check_horizons(self) -> List[Prediction]:
        """
        Check all pending predictions for horizon expiry.
        Returns list of newly expired predictions.
        """
        expired = []
        for pred in self._predictions.values():
            if pred.is_expired:
                pred.status = PREDICTION_STATUS_EXPIRED
                expired.append(pred)
        return expired

    def get_prediction(self, prediction_id: str) -> Optional[Prediction]:
        return self._predictions.get(prediction_id)

    def get_chain_predictions(self, chain_id: str) -> List[Prediction]:
        """Get all predictions for a specific chain."""
        pred_ids = self._chain_predictions.get(chain_id, [])
        return [self._predictions[pid] for pid in pred_ids
                if pid in self._predictions]

    def get_pending_predictions(self) -> List[Prediction]:
        return [p for p in self._predictions.values()
                if p.status == PREDICTION_STATUS_PENDING]

    def get_accuracy(self) -> float:
        """Compute overall prediction accuracy."""
        decided = [p for p in self._predictions.values()
                   if p.status in (PREDICTION_STATUS_VERIFIED, PREDICTION_STATUS_FALSIFIED)]
        if not decided:
            return 0.0
        correct = sum(1 for p in decided if p.status == PREDICTION_STATUS_VERIFIED)
        return correct / len(decided)

    def get_stats(self) -> dict:
        return {
            'total': self.total_predictions,
            'pending': self.pending_count,
            'verified': self.verified_count,
            'falsified': self.falsified_count,
            'expired': sum(1 for p in self._predictions.values()
                          if p.status == PREDICTION_STATUS_EXPIRED),
            'accuracy': self.get_accuracy(),
        }

    def to_dict_list(self) -> List[dict]:
        return [p.to_dict() for p in self._predictions.values()]

    def load_from_list(self, pred_list: List[dict]) -> int:
        count = 0
        for data in pred_list:
            try:
                pred = Prediction.from_dict(data)
                self._predictions[pred.id] = pred
                if pred.chain_id not in self._chain_predictions:
                    self._chain_predictions[pred.chain_id] = []
                self._chain_predictions[pred.chain_id].append(pred.id)
                count += 1
            except Exception:
                continue
        return count

    def _parse_json_response(self, response: str) -> Optional[dict]:
        import re
        response = response.strip()
        if '```' in response:
            match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response, re.DOTALL)
            if match:
                response = match.group(1).strip()
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return None
