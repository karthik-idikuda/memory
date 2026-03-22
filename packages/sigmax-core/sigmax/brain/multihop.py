"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Multi-Hop Chain Builder                  ║
║  CAULANG-Ω: MULTIHOP — follow the chain of WHY            ║
╚══════════════════════════════════════════════════════════╝

Builds N-hop causal chains: A→B→C→D
Uses weakest-link confidence: chain_conf = min(node confidences)
Detects cycles and enforces depth limits.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from sigmax.config import (
    MULTIHOP_MAX_DEPTH,
    MULTIHOP_MIN_CONFIDENCE,
)
from sigmax.core.causenode import CauseNode
from sigmax.core.tokenizer import word_overlap
from sigmax.exceptions import ChainCycleError, ChainDepthError


class CausalPath:
    """A multi-hop causal path: A → B → C → D."""

    __slots__ = ('nodes', 'confidence', 'depth')

    def __init__(self, nodes: List[CauseNode]):
        self.nodes = nodes
        self.depth = len(nodes)
        # Weakest-link: chain confidence = min(node confidences)
        self.confidence = min(n.confidence for n in nodes) if nodes else 0.0

    @property
    def cause(self) -> str:
        """Root cause (first node's cause)."""
        return self.nodes[0].cause if self.nodes else ""

    @property
    def effect(self) -> str:
        """Final effect (last node's effect)."""
        return self.nodes[-1].effect if self.nodes else ""

    @property
    def node_ids(self) -> List[str]:
        return [n.id for n in self.nodes]

    def to_caulang(self) -> str:
        """CAULANG-Ω notation for the full path."""
        if not self.nodes:
            return ""
        parts = [f'"{self.nodes[0].cause}"']
        for node in self.nodes:
            parts.append(f'~>~ "{node.effect}"')
        return f'>>> {" ".join(parts)} (conf={self.confidence:.2f}, hops={self.depth})'

    def to_dict(self) -> dict:
        return {
            'node_ids': self.node_ids,
            'cause': self.cause,
            'effect': self.effect,
            'confidence': self.confidence,
            'depth': self.depth,
            'steps': [
                {'cause': n.cause, 'effect': n.effect,
                 'confidence': n.confidence, 'type': n.cause_type}
                for n in self.nodes
            ],
        }

    def __repr__(self) -> str:
        return f"CausalPath(hops={self.depth}, conf={self.confidence:.2f})"


class MultiHopBuilder:
    """
    Builds multi-hop causal chains by linking cause-effect nodes.

    Node A (effect="rain") + Node B (cause="rain") → A→B chain
    Uses word overlap to detect linkable nodes.
    """

    def __init__(self, link_threshold: float = 0.50):
        """
        Args:
            link_threshold: Minimum word overlap between effect/cause to link.
        """
        self.link_threshold = link_threshold

    def build_graph(self, nodes: List[CauseNode]) -> Dict[str, List[str]]:
        """
        Build an adjacency graph: node_id → [connected_node_ids].
        An edge exists from A to B if A.effect overlaps with B.cause.
        """
        graph: Dict[str, List[str]] = {n.id: [] for n in nodes}
        node_map = {n.id: n for n in nodes}

        for a in nodes:
            for b in nodes:
                if a.id == b.id:
                    continue
                overlap = word_overlap(a.effect, b.cause)
                if overlap >= self.link_threshold:
                    graph[a.id].append(b.id)

        return graph

    def find_paths(
        self,
        nodes: List[CauseNode],
        max_depth: int = MULTIHOP_MAX_DEPTH,
        min_confidence: float = MULTIHOP_MIN_CONFIDENCE,
    ) -> List[CausalPath]:
        """
        Find all multi-hop paths in the causal graph.
        Uses DFS with cycle detection and depth limiting.
        """
        node_map = {n.id: n for n in nodes}
        graph = self.build_graph(nodes)
        all_paths = []

        for start_id in graph:
            visited: Set[str] = set()
            self._dfs(
                current_id=start_id,
                graph=graph,
                node_map=node_map,
                visited=visited,
                current_path=[],
                all_paths=all_paths,
                max_depth=max_depth,
                min_confidence=min_confidence,
            )

        # Sort by depth (longer chains first), then confidence
        all_paths.sort(key=lambda p: (p.depth, p.confidence), reverse=True)
        return all_paths

    def find_path_between(
        self,
        nodes: List[CauseNode],
        start_text: str,
        end_text: str,
        max_depth: int = MULTIHOP_MAX_DEPTH,
    ) -> Optional[CausalPath]:
        """Find a path from a cause containing start_text to an effect containing end_text."""
        node_map = {n.id: n for n in nodes}
        graph = self.build_graph(nodes)

        # Find start nodes (cause matches start_text)
        start_nodes = [
            n for n in nodes
            if word_overlap(start_text, n.cause) >= self.link_threshold
        ]

        for start in start_nodes:
            visited: Set[str] = set()
            path = self._find_target(
                current_id=start.id,
                target_text=end_text,
                graph=graph,
                node_map=node_map,
                visited=visited,
                current_path=[],
                max_depth=max_depth,
            )
            if path:
                return path

        return None

    def get_chain_length(self, node: CauseNode, nodes: List[CauseNode]) -> int:
        """Get the longest chain length starting from a given node."""
        node_map = {n.id: n for n in nodes}
        graph = self.build_graph(nodes)
        visited: Set[str] = set()
        return self._max_depth(node.id, graph, visited)

    def detect_cycles(self, nodes: List[CauseNode]) -> List[List[str]]:
        """Detect all cycles in the causal graph."""
        graph = self.build_graph(nodes)
        cycles = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        for node_id in graph:
            if node_id not in visited:
                self._detect_cycle_dfs(
                    node_id, graph, visited, rec_stack, [], cycles
                )
        return cycles

    # ── Internal methods ──

    def _dfs(
        self,
        current_id: str,
        graph: Dict[str, List[str]],
        node_map: Dict[str, CauseNode],
        visited: Set[str],
        current_path: List[CauseNode],
        all_paths: List[CausalPath],
        max_depth: int,
        min_confidence: float,
    ) -> None:
        if current_id in visited:
            return
        if len(current_path) >= max_depth:
            return

        node = node_map.get(current_id)
        if not node:
            return

        visited.add(current_id)
        current_path.append(node)

        # Record path if length >= 2 (multi-hop)
        if len(current_path) >= 2:
            path = CausalPath(list(current_path))
            if path.confidence >= min_confidence:
                all_paths.append(path)

        # Continue DFS
        for neighbor_id in graph.get(current_id, []):
            self._dfs(
                neighbor_id, graph, node_map, visited,
                current_path, all_paths, max_depth, min_confidence
            )

        current_path.pop()
        visited.discard(current_id)

    def _find_target(
        self,
        current_id: str,
        target_text: str,
        graph: Dict[str, List[str]],
        node_map: Dict[str, CauseNode],
        visited: Set[str],
        current_path: List[CauseNode],
        max_depth: int,
    ) -> Optional[CausalPath]:
        if current_id in visited or len(current_path) >= max_depth:
            return None

        node = node_map.get(current_id)
        if not node:
            return None

        visited.add(current_id)
        current_path.append(node)

        # Check if we reached target
        if (len(current_path) >= 2 and
                word_overlap(target_text, node.effect) >= self.link_threshold):
            return CausalPath(list(current_path))

        for neighbor_id in graph.get(current_id, []):
            result = self._find_target(
                neighbor_id, target_text, graph, node_map,
                visited, current_path, max_depth
            )
            if result:
                return result

        current_path.pop()
        visited.discard(current_id)
        return None

    def _max_depth(
        self, node_id: str, graph: Dict[str, List[str]], visited: Set[str]
    ) -> int:
        if node_id in visited:
            return 0
        visited.add(node_id)
        max_d = 1
        for neighbor in graph.get(node_id, []):
            max_d = max(max_d, 1 + self._max_depth(neighbor, graph, visited))
        visited.discard(node_id)
        return max_d

    def _detect_cycle_dfs(
        self,
        node_id: str,
        graph: Dict[str, List[str]],
        visited: Set[str],
        rec_stack: Set[str],
        path: List[str],
        cycles: List[List[str]],
    ) -> None:
        visited.add(node_id)
        rec_stack.add(node_id)
        path.append(node_id)

        for neighbor in graph.get(node_id, []):
            if neighbor not in visited:
                self._detect_cycle_dfs(
                    neighbor, graph, visited, rec_stack, path, cycles
                )
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])

        path.pop()
        rec_stack.discard(node_id)
