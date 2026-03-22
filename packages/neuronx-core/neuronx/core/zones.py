"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Thermal Zone Manager                   ║
║  NRNLANG-Ω: TEMPER — move engram to correct zone         ║
║  [H] HOT / [W] WARM / [C] COLD / [S] SILENT            ║
╚══════════════════════════════════════════════════════════╝

FORMULA G — HEAT SCORE:
  w = min(weight / 3.0, 1.0) × 0.4
  r = exp(-λ × days_since_last_seen) × 0.4
  c = log(1 + len(bonds)) / log(21) × 0.2
  HEAT = min(1.0, w + r + c)

ZONE ASSIGNMENT:
  if is_anchor: return "HOT"
  if heat >= 0.70: HOT
  if heat >= 0.30: WARM
  if heat >= 0.05: COLD
  if age >= 90d: SILENT
  else: COLD

BUG-007 FIX: Reawakening runs at session start.
"""

import math
import time
import logging
from typing import Dict, Set, List, Optional

from neuronx.config import (
    ZONE_HOT, ZONE_WARM, ZONE_COLD, ZONE_SILENT,
    HEAT_HOT_THRESHOLD, HEAT_WARM_THRESHOLD, HEAT_COLD_THRESHOLD,
    SILENCE_AGE_DAYS, FOSSIL_AGE_DAYS,
    ANCHOR_CONFIDENCE_THRESHOLD, ANCHOR_ACCESS_THRESHOLD,
    REAWAKEN_HOT_THRESHOLD, REAWAKEN_WARM_THRESHOLD,
)
from neuronx.core.node import EngramNode
from neuronx.utils.tokenizer import tokenize, jaccard

logger = logging.getLogger("NEURONX.THERMAL")


class ThermalManager:
    """
    NRNLANG-Ω: THERMAL MANAGER — governs zone migration.

    AUDIT phases:
      Phase 1 — TEMPERATURE (compute heat, assign zones)
      Phase 2 — GHOST CHECK (reawaken dormant memories)
      Phase 3 — FOSSIL MARKING (mark old cold memories)
      Phase 4 — ANCHOR PROTECTION (crystallize strong memories)
    """

    @staticmethod
    def compute_heat(engram: EngramNode) -> float:
        """
        NRNLANG-Ω: FORMULA G — HEAT SCORE
          w = min(weight / 3.0, 1.0) × 0.4
          r = exp(-λ × days_since_last_seen) × 0.4
          c = log(1 + len(bonds)) / log(21) × 0.2
          HEAT = min(1.0, w + r + c)
        """
        w = min(engram.weight / 3.0, 1.0) * 0.4
        r = engram.recency_score * 0.4
        bond_count = len(engram.bonds)
        c = (math.log(1 + bond_count) / math.log(21)) * 0.2 if bond_count > 0 else 0.0
        return min(1.0, max(0.0, w + r + c))

    @staticmethod
    def assign_zone(engram: EngramNode) -> str:
        """
        NRNLANG-Ω: TEMPER — assign zone based on heat and rules.
        """
        if engram.is_anchor:
            return ZONE_HOT

        heat = ThermalManager.compute_heat(engram)
        engram.heat = heat

        if heat >= HEAT_HOT_THRESHOLD:
            return ZONE_HOT
        elif heat >= HEAT_WARM_THRESHOLD:
            return ZONE_WARM
        elif heat >= HEAT_COLD_THRESHOLD:
            return ZONE_COLD
        else:
            if engram.age_days >= SILENCE_AGE_DAYS:
                return ZONE_SILENT
            return ZONE_COLD

    @staticmethod
    def should_crystallize(engram: EngramNode) -> bool:
        """Check if engram qualifies for crystallization."""
        return (
            engram.confidence > ANCHOR_CONFIDENCE_THRESHOLD
            and engram.access_count > ANCHOR_ACCESS_THRESHOLD
        )

    @staticmethod
    def compute_reawaken_score(
        engram: EngramNode,
        session_tokens: frozenset,
        memory_bank: Dict[str, EngramNode],
    ) -> float:
        """
        NRNLANG-Ω: FORMULA J — REAWAKENING SCORE

        REAWAKEN_SCORE = {
          (session_word_overlap × 3.0) +
          (hot_bond_strength   × 2.0) +
          (spark_legacy        × 1.5)
        } / 6.5
        """
        engram_tokens = tokenize(engram.raw)
        overlap = jaccard(session_tokens, engram_tokens)

        hot_bonds = 0.0
        for bond_id, synapse in engram.bonds.items():
            bonded = memory_bank.get(bond_id)
            if bonded and bonded.zone == ZONE_HOT:
                hot_bonds += synapse
        hot_bonds = min(1.0, hot_bonds)

        score = (overlap * 3.0 + hot_bonds * 2.0 + engram.surprise_score * 1.5) / 6.5
        return max(0.0, min(1.0, score))

    def check_reawakenings(
        self,
        engrams: Dict[str, EngramNode],
        session_tokens: frozenset = frozenset(),
    ) -> List[str]:
        """
        BUG-007 FIX: Run reawakening checks.
        Called at session start AND after first user message.
        Returns list of reawakened engram IDs.
        """
        reawakened = []
        for eid, engram in engrams.items():
            if engram.zone == ZONE_SILENT and engram.is_active_engram():
                score = self.compute_reawaken_score(engram, session_tokens, engrams)
                if score > REAWAKEN_HOT_THRESHOLD:
                    engram.zone = ZONE_HOT
                    engram.last_seen = time.time()
                    reawakened.append(eid)
                    logger.info(f"^^ REAWAKEN → [H] {eid[:8]}… score={score:.2f}")
                elif score > REAWAKEN_WARM_THRESHOLD:
                    engram.zone = ZONE_WARM
                    engram.last_seen = time.time()
                    reawakened.append(eid)
                    logger.info(f"^^ REAWAKEN → [W] {eid[:8]}… score={score:.2f}")
        return reawakened

    def audit(
        self,
        engrams: Dict[str, EngramNode],
        session_tokens: frozenset = frozenset(),
    ) -> dict:
        """
        NRNLANG-Ω: AUDIT — Full thermal check on all memories.
        """
        stats = {
            "promoted": 0, "demoted": 0, "reawakened": 0,
            "fossilized": 0, "crystallized": 0,
            "zone_counts": {ZONE_HOT: 0, ZONE_WARM: 0, ZONE_COLD: 0, ZONE_SILENT: 0},
            "reawakened_ids": [],
            "crystallized_ids": [],
        }

        zone_order = {ZONE_HOT: 4, ZONE_WARM: 3, ZONE_COLD: 2, ZONE_SILENT: 1}

        # Phase 1: Temperature
        for engram in engrams.values():
            old_zone = engram.zone
            new_zone = self.assign_zone(engram)
            if old_zone != new_zone:
                old_rank = zone_order.get(old_zone, 0)
                new_rank = zone_order.get(new_zone, 0)
                if new_rank > old_rank:
                    stats["promoted"] += 1
                else:
                    stats["demoted"] += 1
                engram.zone = new_zone

        # Phase 2: Ghost Check
        reawakened = self.check_reawakenings(engrams, session_tokens)
        stats["reawakened"] = len(reawakened)
        stats["reawakened_ids"] = reawakened

        # Phase 3: Fossil Marking
        for engram in engrams.values():
            if engram.zone == ZONE_COLD and engram.age_days > FOSSIL_AGE_DAYS:
                if "fossil" not in engram.tags:
                    engram.tags.append("fossil")
                    stats["fossilized"] += 1

        # Phase 4: Anchor Protection
        for engram in engrams.values():
            if self.should_crystallize(engram) and not engram.is_anchor:
                engram.crystallize()
                stats["crystallized"] += 1
                stats["crystallized_ids"].append(engram.id)
                logger.info(f"◆ CRYSTALLIZE → [A] {engram.id[:8]}…")

        # Count zones
        for engram in engrams.values():
            z = engram.zone
            if z in stats["zone_counts"]:
                stats["zone_counts"][z] += 1

        logger.info(
            f"AUDIT — promoted:{stats['promoted']} demoted:{stats['demoted']} "
            f"reawakened:{stats['reawakened']} crystallized:{stats['crystallized']}"
        )
        return stats
