"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Counterfactual Engine                    ║
║  CAULANG-Ω: COUNTERFACT — what if it didn't happen?      ║
╚══════════════════════════════════════════════════════════╝

Generates "what if" scenarios for causal chains.
If A caused B, what would happen WITHOUT A?
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from sigmax.config import (
    COUNTERFACTUAL_MAX_PER_CHAIN,
    COUNTERFACTUAL_MIN_CONFIDENCE,
    PROMPT_COUNTERFACTUAL,
)
from sigmax.core.causenode import CauseNode
from sigmax.core.integrity import generate_prediction_id
from sigmax.exceptions import CounterfactualError, CounterfactualLimitError


@dataclass
class Counterfactual:
    """A single counterfactual scenario."""
    id: str = field(default_factory=generate_prediction_id)
    chain_id: str = ""
    original_cause: str = ""
    original_effect: str = ""
    counterfactual_cause: str = ""
    counterfactual_effect: str = ""
    plausibility: float = 0.50
    reasoning: str = ""
    implications: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'chain_id': self.chain_id,
            'original_cause': self.original_cause,
            'original_effect': self.original_effect,
            'counterfactual_cause': self.counterfactual_cause,
            'counterfactual_effect': self.counterfactual_effect,
            'plausibility': self.plausibility,
            'reasoning': self.reasoning,
            'implications': self.implications,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Counterfactual':
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in valid})

    def to_caulang(self) -> str:
        return (
            f'~!~ IF NOT "{self.original_cause}" '
            f'THEN NOT "{self.original_effect}" → '
            f'"{self.counterfactual_effect}" '
            f'(plausibility={self.plausibility:.2f})'
        )


class CounterfactualEngine:
    """Generates and manages counterfactual scenarios."""

    def __init__(self):
        self._counterfactuals: Dict[str, Counterfactual] = {}
        self._chain_counterfactuals: Dict[str, List[str]] = {}

    @property
    def total_count(self) -> int:
        return len(self._counterfactuals)

    def generate(
        self,
        node: CauseNode,
        counterfactual_cause: str = "",
        counterfactual_effect: str = "",
        plausibility: float = 0.50,
        reasoning: str = "",
        implications: Optional[List[str]] = None,
    ) -> Counterfactual:
        """Generate a counterfactual for a causal chain."""
        chain_cfs = self._chain_counterfactuals.get(node.id, [])
        if len(chain_cfs) >= COUNTERFACTUAL_MAX_PER_CHAIN:
            raise CounterfactualLimitError(
                f"Max counterfactuals ({COUNTERFACTUAL_MAX_PER_CHAIN}) "
                f"reached for chain {node.id[:8]}"
            )

        if node.confidence < COUNTERFACTUAL_MIN_CONFIDENCE:
            raise CounterfactualError(
                f"Chain confidence {node.confidence:.2f} below minimum "
                f"{COUNTERFACTUAL_MIN_CONFIDENCE} for counterfactual generation"
            )

        if not counterfactual_cause:
            counterfactual_cause = f"NOT {node.cause}"
        if not counterfactual_effect:
            counterfactual_effect = f"NOT {node.effect}"

        cf = Counterfactual(
            chain_id=node.id,
            original_cause=node.cause,
            original_effect=node.effect,
            counterfactual_cause=counterfactual_cause,
            counterfactual_effect=counterfactual_effect,
            plausibility=plausibility,
            reasoning=reasoning,
            implications=implications or [],
        )

        self._counterfactuals[cf.id] = cf
        if node.id not in self._chain_counterfactuals:
            self._chain_counterfactuals[node.id] = []
        self._chain_counterfactuals[node.id].append(cf.id)
        node.counterfactual_count += 1

        return cf

    def generate_with_ai(
        self,
        node: CauseNode,
        llm_fn: Callable[[str], str],
    ) -> Optional[Counterfactual]:
        """Generate a counterfactual using AI/LLM."""
        prompt = PROMPT_COUNTERFACTUAL.format(
            cause=node.cause,
            effect=node.effect,
            confidence=f"{node.confidence:.2f}",
        )
        try:
            response = llm_fn(prompt)
            data = self._parse_json(response)
            if not data:
                return None
            return self.generate(
                node=node,
                counterfactual_cause=data.get('counterfactual_cause', ''),
                counterfactual_effect=data.get('counterfactual_effect', ''),
                plausibility=float(data.get('plausibility', 0.50)),
                reasoning=data.get('reasoning', ''),
                implications=data.get('implications', []),
            )
        except (CounterfactualLimitError, CounterfactualError):
            raise
        except Exception:
            return None

    def get_counterfactual(self, cf_id: str) -> Optional[Counterfactual]:
        return self._counterfactuals.get(cf_id)

    def get_chain_counterfactuals(self, chain_id: str) -> List[Counterfactual]:
        cf_ids = self._chain_counterfactuals.get(chain_id, [])
        return [self._counterfactuals[cid] for cid in cf_ids
                if cid in self._counterfactuals]

    def to_dict_list(self) -> List[dict]:
        return [cf.to_dict() for cf in self._counterfactuals.values()]

    def load_from_list(self, cf_list: List[dict]) -> int:
        count = 0
        for data in cf_list:
            try:
                cf = Counterfactual.from_dict(data)
                self._counterfactuals[cf.id] = cf
                if cf.chain_id not in self._chain_counterfactuals:
                    self._chain_counterfactuals[cf.chain_id] = []
                self._chain_counterfactuals[cf.chain_id].append(cf.id)
                count += 1
            except Exception:
                continue
        return count

    def _parse_json(self, response: str) -> Optional[dict]:
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
