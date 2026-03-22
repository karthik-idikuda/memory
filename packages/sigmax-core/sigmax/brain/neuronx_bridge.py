"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — NEURON-X Bridge                          ║
║  CAULANG-Ω: BRIDGE — memories feed reasoning              ║
╚══════════════════════════════════════════════════════════╝

Syncs SIGMA-X with NEURON-X:
- Pull memories from NEURON-X → extract causal chains
- Push verified conclusions → store as NEURON-X memories
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from sigmax.config import (
    BRIDGE_SYNC_INTERVAL,
    BRIDGE_MIN_CONFIDENCE,
    BRIDGE_MAX_CONCLUSIONS,
)
from sigmax.core.causenode import CauseNode
from sigmax.exceptions import BridgeError, BridgeSyncError, BridgeNotConnectedError


class NeuronXBridge:
    """
    Bridge between SIGMA-X (reasoning) and NEURON-X (memory).

    Direction 1: NEURON-X → SIGMA-X
      Pull memories, extract causal chains from memory context

    Direction 2: SIGMA-X → NEURON-X
      Push verified causal conclusions as new memories
    """

    def __init__(self):
        self._connected = False
        self._neuronx_brain = None
        self._sync_count = 0
        self._pulled_count = 0
        self._pushed_count = 0
        self._last_sync_time = 0.0

    def connect(self, neuronx_brain: Any) -> None:
        """Connect to a NEURON-X brain instance."""
        self._neuronx_brain = neuronx_brain
        self._connected = True

    def disconnect(self) -> None:
        """Disconnect from NEURON-X."""
        self._neuronx_brain = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._neuronx_brain is not None

    def pull_memories(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[dict]:
        """
        Pull relevant memories from NEURON-X.
        Returns list of memory dicts with text, confidence, tags, etc.
        """
        if not self.is_connected:
            raise BridgeNotConnectedError("NEURON-X bridge not connected")

        try:
            brain = self._neuronx_brain
            # Try standard NEURON-X API: brain.recall(query, top_k)
            if hasattr(brain, 'recall'):
                results = brain.recall(query, top_k=top_k)
                self._pulled_count += len(results) if results else 0
                return results if results else []
            # Try alternative: brain.search(query)
            elif hasattr(brain, 'search'):
                results = brain.search(query, top_k=top_k)
                self._pulled_count += len(results) if results else 0
                return results if results else []
            else:
                return []
        except Exception as e:
            raise BridgeSyncError(f"Failed to pull memories: {e}")

    def push_conclusion(
        self,
        node: CauseNode,
        conclusion_text: Optional[str] = None,
    ) -> bool:
        """
        Push a verified causal conclusion to NEURON-X as a new memory.
        Only pushes if confidence >= BRIDGE_MIN_CONFIDENCE.
        """
        if not self.is_connected:
            raise BridgeNotConnectedError("NEURON-X bridge not connected")

        if node.confidence < BRIDGE_MIN_CONFIDENCE:
            return False

        if not conclusion_text:
            conclusion_text = (
                f"{node.cause} causes {node.effect} "
                f"(confidence: {node.confidence:.0%}, "
                f"evidence: +{node.evidence_for}/-{node.evidence_against})"
            )

        try:
            brain = self._neuronx_brain
            if hasattr(brain, 'memorize'):
                brain.memorize(conclusion_text)
                self._pushed_count += 1
                node.neuronx_link_id = f"bridge_{node.id[:8]}_{int(time.time())}"
                return True
            elif hasattr(brain, 'store'):
                brain.store(conclusion_text)
                self._pushed_count += 1
                node.neuronx_link_id = f"bridge_{node.id[:8]}_{int(time.time())}"
                return True
            return False
        except Exception as e:
            raise BridgeSyncError(f"Failed to push conclusion: {e}")

    def push_conclusions_bulk(
        self,
        nodes: List[CauseNode],
        max_push: int = BRIDGE_MAX_CONCLUSIONS,
    ) -> int:
        """
        Push multiple high-confidence conclusions to NEURON-X.
        Returns count of successfully pushed conclusions.
        """
        # Sort by confidence, highest first
        eligible = [
            n for n in nodes
            if n.confidence >= BRIDGE_MIN_CONFIDENCE
            and n.neuronx_link_id is None  # not already pushed
        ]
        eligible.sort(key=lambda n: n.confidence, reverse=True)

        pushed = 0
        for node in eligible[:max_push]:
            try:
                if self.push_conclusion(node):
                    pushed += 1
            except BridgeSyncError:
                continue

        self._sync_count += 1
        self._last_sync_time = time.time()
        return pushed

    def should_sync(self, operation_count: int) -> bool:
        """Check if it's time for a sync based on operation count."""
        return operation_count % BRIDGE_SYNC_INTERVAL == 0

    @property
    def stats(self) -> dict:
        return {
            'connected': self.is_connected,
            'sync_count': self._sync_count,
            'pulled_memories': self._pulled_count,
            'pushed_conclusions': self._pushed_count,
            'last_sync_time': self._last_sync_time,
        }
