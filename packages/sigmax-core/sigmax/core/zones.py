"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Thermal Zone Manager                     ║
║  CAULANG-Ω: ZONE — heat determines attention             ║
╚══════════════════════════════════════════════════════════╝

5-zone thermal system for causal chains:
  ACTIVE   — frequently accessed, high confidence, recent
  WARM     — moderately active
  DORMANT  — low activity but not archived
  AXIOM    — crystallized truth, permanent
  ARCHIVED — inactive, low confidence, old

Zone determines retrieval priority and decay behavior.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from sigmax.config import (
    ZONE_ACTIVE, ZONE_WARM, ZONE_DORMANT, ZONE_AXIOM, ZONE_ARCHIVED,
    ZONE_HEAT_THRESHOLDS,
    ZONE_HEAT_VALUES,
    CAULANG_ZONE_SYMBOLS,
)
from sigmax.core.causenode import CauseNode


class ZoneManager:
    """
    Manages thermal zone assignment and transitions for CauseNodes.

    Zones:
      ACTIVE   (heat >= 0.70)  — hot chains, frequent access
      WARM     (heat >= 0.40)  — moderate activity
      DORMANT  (heat >= 0.10)  — low activity
      AXIOM    (special)       — crystallized, confidence >= 0.95
      ARCHIVED (heat < 0.10)   — inactive
    """

    def __init__(self):
        self._zone_counts: Dict[str, int] = {
            ZONE_ACTIVE: 0,
            ZONE_WARM: 0,
            ZONE_DORMANT: 0,
            ZONE_AXIOM: 0,
            ZONE_ARCHIVED: 0,
        }

    def assign_zone(self, node: CauseNode) -> str:
        """
        Compute and assign the thermal zone for a node.
        Returns the new zone name.
        """
        old_zone = node.zone
        new_zone = node.update_zone()

        # Update counts
        if old_zone != new_zone:
            if old_zone in self._zone_counts:
                self._zone_counts[old_zone] = max(0, self._zone_counts[old_zone] - 1)
            if new_zone in self._zone_counts:
                self._zone_counts[new_zone] += 1

        return new_zone

    def assign_zones_bulk(self, nodes: List[CauseNode]) -> Dict[str, int]:
        """
        Assign zones to all nodes and return zone distribution.
        """
        self._zone_counts = {z: 0 for z in self._zone_counts}

        for node in nodes:
            node.update_zone()
            zone = node.zone
            if zone in self._zone_counts:
                self._zone_counts[zone] += 1

        return dict(self._zone_counts)

    def get_zone_distribution(self, nodes: List[CauseNode]) -> Dict[str, int]:
        """Get current zone distribution without modifying nodes."""
        dist: Dict[str, int] = {
            ZONE_ACTIVE: 0,
            ZONE_WARM: 0,
            ZONE_DORMANT: 0,
            ZONE_AXIOM: 0,
            ZONE_ARCHIVED: 0,
        }
        for node in nodes:
            z = node.zone
            if z in dist:
                dist[z] += 1
        return dist

    def get_nodes_by_zone(
        self, nodes: List[CauseNode], zone: str
    ) -> List[CauseNode]:
        """Get all nodes in a specific zone."""
        return [n for n in nodes if n.zone == zone]

    def get_active_nodes(self, nodes: List[CauseNode]) -> List[CauseNode]:
        """Get all ACTIVE zone nodes."""
        return self.get_nodes_by_zone(nodes, ZONE_ACTIVE)

    def get_axiom_nodes(self, nodes: List[CauseNode]) -> List[CauseNode]:
        """Get all AXIOM zone nodes."""
        return self.get_nodes_by_zone(nodes, ZONE_AXIOM)

    def get_dormant_nodes(self, nodes: List[CauseNode]) -> List[CauseNode]:
        """Get all DORMANT zone nodes."""
        return self.get_nodes_by_zone(nodes, ZONE_DORMANT)

    def get_archived_nodes(self, nodes: List[CauseNode]) -> List[CauseNode]:
        """Get all ARCHIVED zone nodes."""
        return self.get_nodes_by_zone(nodes, ZONE_ARCHIVED)

    def get_zone_heat_value(self, zone: str) -> float:
        """Get the heat value for a zone."""
        return ZONE_HEAT_VALUES.get(zone, 0.0)

    def get_zone_symbol(self, zone: str) -> str:
        """Get the CAULANG-Ω symbol for a zone."""
        return CAULANG_ZONE_SYMBOLS.get(zone, "◈")

    def get_transition_candidates(
        self, nodes: List[CauseNode]
    ) -> List[Tuple[CauseNode, str, str]]:
        """
        Find nodes whose current zone doesn't match their computed zone.
        Returns list of (node, current_zone, computed_zone) tuples.
        """
        candidates = []
        for node in nodes:
            computed = node.compute_zone()
            if computed != node.zone:
                candidates.append((node, node.zone, computed))
        return candidates

    def run_zone_audit(self, nodes: List[CauseNode]) -> dict:
        """
        Run a full zone audit — reassign all zones and report changes.
        """
        transitions = []
        for node in nodes:
            old = node.zone
            new = node.update_zone()
            if old != new:
                transitions.append({
                    'node_id': node.id,
                    'cause': node.cause[:40],
                    'old_zone': old,
                    'new_zone': new,
                    'heat': node.get_heat(),
                })

        distribution = self.assign_zones_bulk(nodes)

        return {
            'total_nodes': len(nodes),
            'transitions': len(transitions),
            'transition_details': transitions,
            'distribution': distribution,
        }

    def get_zone_summary(self, nodes: List[CauseNode]) -> str:
        """Human-readable zone summary in CAULANG-Ω notation."""
        dist = self.get_zone_distribution(nodes)
        lines = []
        for zone in [ZONE_ACTIVE, ZONE_WARM, ZONE_DORMANT, ZONE_AXIOM, ZONE_ARCHIVED]:
            sym = self.get_zone_symbol(zone)
            count = dist.get(zone, 0)
            lines.append(f"  {sym} {zone}: {count}")
        return "ZONE DISTRIBUTION:\n" + "\n".join(lines)
