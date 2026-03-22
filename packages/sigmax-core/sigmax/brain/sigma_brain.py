"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — SigmaBrain Orchestrator                  ║
║  CAULANG-Ω: BRAIN — the master controller                ║
╚══════════════════════════════════════════════════════════╝

SigmaBrain is to SIGMA-X what NeuronBrain is to NEURON-X.
It orchestrates all components into a single, coherent API.

Usage:
    brain = SigmaBrain("my_brain.sigma")
    brain.think("rain causes wet roads")
    results = brain.reason("why is the road wet?")
"""

from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from sigmax.config import (
    AUTO_SAVE_INTERVAL,
    DEFAULT_TOP_K,
    ZONE_AXIOM,
)
from sigmax.core.causenode import CauseNode
from sigmax.core.causadb import CausaDB
from sigmax.core.sigma import sigma_rank, sigma_score, sigma_score_breakdown
from sigmax.core.evidence import EvidenceEngine
from sigmax.core.zones import ZoneManager
from sigmax.core.tokenizer import word_overlap, normalize_text
from sigmax.core.integrity import generate_brain_id
from sigmax.brain.chain_builder import ChainBuilder
from sigmax.brain.predictor import PredictionEngine
from sigmax.brain.counterfactual import CounterfactualEngine
from sigmax.brain.multihop import MultiHopBuilder
from sigmax.brain.axiom_engine import AxiomEngine
from sigmax.brain.neuronx_bridge import NeuronXBridge
from sigmax.brain.injector import ContextInjector
from sigmax.brain.scheduler import Scheduler
from sigmax.exceptions import (
    BrainError,
    BrainNotLoadedError,
    CauseNodeNotFoundError,
    CauseNodeDuplicateError,
)


class SigmaBrain:
    """
    The master orchestrator for SIGMA-X causal reasoning.

    Coordinates: CausaDB, ChainBuilder, PredictionEngine,
    CounterfactualEngine, MultiHopBuilder, AxiomEngine,
    EvidenceEngine, ZoneManager, NeuronXBridge, Scheduler.
    """

    def __init__(self, path: str = "brain.sigma"):
        self.path = CausaDB.ensure_path(path)
        self.brain_id = generate_brain_id()

        # Core stores
        self._nodes: Dict[str, CauseNode] = {}
        self._edges: List[Dict] = []

        # Engines
        self.chain_builder = ChainBuilder()
        self.prediction_engine = PredictionEngine()
        self.counterfactual_engine = CounterfactualEngine()
        self.multihop_builder = MultiHopBuilder()
        self.axiom_engine = AxiomEngine()
        self.evidence_engine = EvidenceEngine()
        self.zone_manager = ZoneManager()
        self.bridge = NeuronXBridge()
        self.injector = ContextInjector()
        self.scheduler = Scheduler()

        # State
        self._loaded = False
        self._operation_count = 0
        self._created_at = time.time()

        # Auto-load if file exists
        if CausaDB.exists(self.path):
            self.load()
        else:
            self._loaded = True

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CORE OPERATIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def think(
        self,
        text: str,
        llm_fn: Optional[Callable[[str], str]] = None,
    ) -> List[CauseNode]:
        """
        Process input text: extract causal chains and store them.

        This is the primary ingestion method.

        Args:
            text: Natural language text containing causal relationships
            llm_fn: Optional LLM function for AI-assisted extraction

        Returns:
            List of newly created CauseNodes.
        """
        # Extract chains
        if llm_fn:
            nodes = self.chain_builder.extract_with_ai(text, llm_fn)
        else:
            nodes = self.chain_builder.extract(text)

        if not nodes:
            return []

        # De-duplicate against existing nodes
        new_nodes = []
        for node in nodes:
            duplicate = self._find_duplicate(node)
            if duplicate:
                # Strengthen existing instead of adding duplicate
                duplicate.touch()
                duplicate.strengthen()
                duplicate.add_evidence(is_support=True)
            else:
                self._nodes[node.id] = node
                new_nodes.append(node)

        # Auto-save
        self._operation_count += len(new_nodes)
        if self._operation_count % AUTO_SAVE_INTERVAL == 0 and new_nodes:
            self.save()

        # Run scheduler
        if self.scheduler.tick():
            self.scheduler.run_audit(
                list(self._nodes.values()),
                self.zone_manager,
                self.prediction_engine,
                self.axiom_engine,
                self.bridge,
            )

        return new_nodes

    def reason(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> List[Tuple[CauseNode, float]]:
        """
        Retrieve and rank causal chains relevant to a query.

        This is the primary retrieval method.
        Uses the 9-component SIGMA scoring algorithm.
        """
        if not self._nodes:
            return []

        nodes = list(self._nodes.values())

        # Compute chain lengths for multi-hop scoring
        chain_lengths = {}
        for node in nodes:
            chain_lengths[node.id] = self.multihop_builder.get_chain_length(
                node, nodes
            )

        return sigma_rank(nodes, query, top_k=top_k, chain_lengths=chain_lengths)

    def reason_with_context(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> str:
        """
        Retrieve chains and format as injectable context.
        Returns formatted string for LLM system prompt.
        """
        ranked = self.reason(query, top_k=top_k)
        return self.injector.build_system_prompt(ranked)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CHAIN MANAGEMENT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def add_chain(
        self,
        cause: str,
        effect: str,
        cause_type: str = "direct",
        confidence: float = 0.50,
        tags: Optional[List[str]] = None,
        subject: str = "",
        decay_class: str = "medium",
    ) -> CauseNode:
        """Manually add a causal chain."""
        node = CauseNode(
            cause=cause,
            effect=effect,
            cause_type=cause_type,
            confidence=confidence,
            tags=tags or [],
            subject=subject,
            source="manual",
            decay_class=decay_class,
        )

        # Check for duplicates
        duplicate = self._find_duplicate(node)
        if duplicate:
            raise CauseNodeDuplicateError(
                f"Similar chain already exists: {duplicate.id[:8]}"
            )

        self._nodes[node.id] = node
        self._operation_count += 1

        if self._operation_count % AUTO_SAVE_INTERVAL == 0:
            self.save()

        return node

    def get_chain(self, chain_id: str) -> CauseNode:
        """Get a chain by ID."""
        node = self._nodes.get(chain_id)
        if not node:
            raise CauseNodeNotFoundError(f"Chain {chain_id} not found")
        node.touch()
        return node

    def delete_chain(self, chain_id: str) -> bool:
        """Delete a chain by ID."""
        if chain_id in self._nodes:
            del self._nodes[chain_id]
            return True
        return False

    def search_chains(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> List[Tuple[CauseNode, float]]:
        """Alias for reason()."""
        return self.reason(query, top_k=top_k)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # EVIDENCE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def add_evidence(
        self,
        chain_id: str,
        text: str,
        is_support: bool = True,
    ) -> dict:
        """Add evidence for or against a chain."""
        node = self.get_chain(chain_id)
        if is_support:
            record = self.evidence_engine.add_support(node, text)
        else:
            record = self.evidence_engine.add_contradiction(node, text)
        return record.to_dict()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PREDICTIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def predict(
        self,
        chain_id: str,
        prediction_text: str,
        confidence: float = 0.50,
        horizon: str = "medium",
    ) -> dict:
        """Create a prediction from a chain."""
        node = self.get_chain(chain_id)
        pred = self.prediction_engine.generate(
            node, prediction_text, confidence, horizon
        )
        return pred.to_dict()

    def verify_prediction(
        self,
        prediction_id: str,
        is_correct: bool,
        evidence: str = "",
    ) -> dict:
        """Verify a prediction as correct or incorrect."""
        pred = self.prediction_engine.get_prediction(prediction_id)
        if not pred:
            from sigmax.exceptions import PredictionNotFoundError
            raise PredictionNotFoundError(f"Prediction {prediction_id} not found")

        source_node = self._nodes.get(pred.chain_id)
        result = self.prediction_engine.verify(
            prediction_id, is_correct, evidence, source_node
        )
        return result.to_dict()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # COUNTERFACTUALS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def counterfactual(
        self,
        chain_id: str,
        cf_cause: str = "",
        cf_effect: str = "",
        plausibility: float = 0.50,
    ) -> dict:
        """Generate a counterfactual for a chain."""
        node = self.get_chain(chain_id)
        cf = self.counterfactual_engine.generate(
            node, cf_cause, cf_effect, plausibility
        )
        return cf.to_dict()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MULTI-HOP
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def find_paths(self, max_depth: int = 5) -> List[dict]:
        """Find all multi-hop paths in the brain."""
        nodes = list(self._nodes.values())
        paths = self.multihop_builder.find_paths(nodes, max_depth=max_depth)
        return [p.to_dict() for p in paths]

    def find_path_between(self, start: str, end: str) -> Optional[dict]:
        """Find a path between two concepts."""
        nodes = list(self._nodes.values())
        path = self.multihop_builder.find_path_between(nodes, start, end)
        return path.to_dict() if path else None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PERSISTENCE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def save(self) -> None:
        """Save brain state to .sigma file using NMP protocol."""
        nodes = list(self._nodes.values())
        predictions = self.prediction_engine.to_dict_list()

        CausaDB.save(
            self.path,
            nodes,
            self._edges,
            predictions,
            brain_id=self.brain_id,
        )

    def load(self) -> None:
        """Load brain state from .sigma file."""
        nodes, edges, predictions = CausaDB.load(self.path)

        self._nodes = {n.id: n for n in nodes}
        self._edges = edges
        self.prediction_engine.load_from_list(predictions)
        self._loaded = True

    def verify_integrity(self) -> bool:
        """Verify .sigma file integrity without loading."""
        return CausaDB.verify(self.path)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STATS & INFO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def stats(self) -> dict:
        nodes = list(self._nodes.values())
        zone_dist = self.zone_manager.get_zone_distribution(nodes)

        return {
            'brain_id': self.brain_id,
            'path': self.path,
            'node_count': len(self._nodes),
            'edge_count': len(self._edges),
            'operation_count': self._operation_count,
            'zones': zone_dist,
            'predictions': self.prediction_engine.get_stats(),
            'counterfactuals': self.counterfactual_engine.total_count,
            'evidence': self.evidence_engine.total_evidence_count,
            'axiom_count': sum(1 for n in nodes if n.zone == ZONE_AXIOM),
            'chain_builder': self.chain_builder.stats,
            'bridge': self.bridge.stats,
            'scheduler': self.scheduler.stats,
        }

    @property
    def all_nodes(self) -> List[CauseNode]:
        return list(self._nodes.values())

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # INTERNAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _find_duplicate(self, node: CauseNode, threshold: float = 0.70) -> Optional[CauseNode]:
        """Find an existing node that's similar enough to be a duplicate."""
        for existing in self._nodes.values():
            cause_sim = word_overlap(node.cause, existing.cause)
            effect_sim = word_overlap(node.effect, existing.effect)
            if (cause_sim + effect_sim) / 2.0 >= threshold:
                return existing
        return None

    def __repr__(self) -> str:
        return (
            f"SigmaBrain(id={self.brain_id}, "
            f"nodes={len(self._nodes)}, "
            f"path='{self.path}')"
        )

    def __len__(self) -> int:
        return len(self._nodes)
