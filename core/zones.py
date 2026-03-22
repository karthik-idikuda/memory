"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Thermal Zone Manager                   ║
║  NRNLANG-Ω: TEMPER — move engram to correct zone         ║
║  [H] HOT / [W] WARM / [C] COLD / [S] SILENT / [A] ANCHOR║
╚══════════════════════════════════════════════════════════╝

FORMULA G — HEAT SCORE (Zone Assignment):
  HEAT = (weight_comp × 0.4) + (recency_comp × 0.4) + (connectivity × 0.2)

  HEAT >= 0.70  → [H] HOT
  HEAT >= 0.30  → [W] WARM
  HEAT >= 0.05  → [C] COLD
  HEAT <  0.05  AND age > 90d → [S] SILENT

FORMULA J — REAWAKENING SCORE:
  Dormant memories can reawaken when context matches.
"""

import math
import logging

from core.node import (
    Engram, ZONE_HOT, ZONE_WARM, ZONE_COLD, ZONE_SILENT, ZONE_ANCHOR,
)
from core.surprise import Amygdala

logger = logging.getLogger("NEURONX.THERMAL")


class ThermalManager:
    """
    NRNLANG-Ω: THERMAL MANAGER — governs zone migration.

    AUDIT every 100 interactions OR every 24 hours:
      Phase 1 — TEMPERATURE (compute heat, assign zones)
      Phase 2 — GHOST CHECK (reawaken dormant memories)
      Phase 3 — FOSSIL MARKING (mark old cold memories)
      Phase 4 — ANCHOR PROTECTION (crystallize strong memories)
    """

    def __init__(self):
        self.amygdala = Amygdala()

    def compute_heat(self, engram: Engram) -> float:
        """
        NRNLANG-Ω: FORMULA G — HEAT SCORE

        HEAT = {
          (weight_component  × 0.4) +
          (recency_component × 0.4) +
          (connectivity      × 0.2)
        }

        weight_component  = min(weight / 3.0, 1.0)
        recency_component = exp(-decay_rate × days_since_last_seen)
        connectivity      = log(1 + axon_count) / log(21)
        """
        weight_comp = min(engram.weight / 3.0, 1.0)
        recency_comp = engram.recency_score

        axon_count = len(engram.axons)
        if axon_count > 0:
            connectivity = math.log(1 + axon_count) / math.log(21)
        else:
            connectivity = 0.0

        heat = (weight_comp * 0.4) + (recency_comp * 0.4) + (connectivity * 0.2)
        return max(0.0, min(1.0, heat))

    def assign_zone(self, engram: Engram) -> str:
        """
        NRNLANG-Ω: TEMPER — assign engram to correct zone.

        HEAT >= 0.70  → [H] HOT
        HEAT >= 0.30  → [W] WARM
        HEAT >= 0.05  → [C] COLD
        HEAT <  0.05  AND age > 90d → [S] SILENT
        HEAT <  0.05  AND age < 90d → [C] COLD (too new to silence)

        ANCHOR exception:
          IF confidence > 0.95 AND access_count > 20 → [A] ANCHOR
        """
        # Anchor check first — anchors never move
        if engram.zone == ZONE_ANCHOR:
            return ZONE_ANCHOR

        heat = self.compute_heat(engram)
        engram.heat = heat

        # ANCHOR crystallization check
        if engram.confidence > 0.95 and engram.access_count > 20:
            return ZONE_ANCHOR

        if heat >= 0.70:
            return ZONE_HOT
        elif heat >= 0.30:
            return ZONE_WARM
        elif heat >= 0.05:
            return ZONE_COLD
        elif engram.age_days > 90:
            return ZONE_SILENT
        else:
            return ZONE_COLD  # Too new to silence

    def compute_reawaken_score(
        self,
        engram: Engram,
        session_tokens: set,
        hot_engram_ids: set,
    ) -> float:
        """
        NRNLANG-Ω: FORMULA J — REAWAKENING SCORE

        FOR every GHOST engram:
          REAWAKEN_SCORE = {
            (session_word_overlap × 3.0) +
            (hot_bond_strength   × 2.0) +
            (spark_legacy        × 1.5)
          } / 6.5

        session_word_overlap = |session ∩ engram| / |session ∪ engram|
        hot_bond_strength = Σ synapse of axons to HOT zone (capped at 1.0)
        """
        engram_tokens = self.amygdala.tokenize(engram.raw)

        # Session word overlap
        session_overlap = self.amygdala.jaccard_similarity(
            session_tokens, engram_tokens
        )

        # Hot bond strength
        hot_bond_total = 0.0
        for axon_id, synapse in engram.axons.items():
            if axon_id in hot_engram_ids:
                hot_bond_total += synapse
        hot_bond_strength = min(1.0, hot_bond_total)

        # Spark legacy
        spark_legacy = engram.spark

        # Weighted sum
        score = (
            (session_overlap * 3.0) +
            (hot_bond_strength * 2.0) +
            (spark_legacy * 1.5)
        ) / 6.5

        return max(0.0, min(1.0, score))

    def audit(
        self,
        engrams: dict[str, Engram],
        session_tokens: set = None,
    ) -> dict:
        """
        NRNLANG-Ω: AUDIT — Full thermal check on all memories.

        Phase 1 — TEMPERATURE: Compute heat, assign zones
        Phase 2 — GHOST CHECK: Reawaken dormant memories
        Phase 3 — FOSSIL MARKING: Mark old cold memories
        Phase 4 — ANCHOR PROTECTION: Crystallize strong memories

        Returns audit statistics.
        """
        if session_tokens is None:
            session_tokens = set()

        stats = {
            "promoted": 0,    # Moved to hotter zone
            "demoted": 0,     # Moved to colder zone
            "reawakened": 0,  # Ghost → Warm/Hot
            "fossilized": 0,  # Marked as fossil
            "crystallized": 0, # Became anchor
            "zone_counts": {"H": 0, "W": 0, "C": 0, "S": 0, "A": 0},
        }

        # ── Phase 1: Temperature ──
        for engram in engrams.values():
            old_zone = engram.zone
            new_zone = self.assign_zone(engram)

            if old_zone != new_zone:
                zone_order = {ZONE_HOT: 4, ZONE_ANCHOR: 4, ZONE_WARM: 3, ZONE_COLD: 2, ZONE_SILENT: 1}
                old_rank = zone_order.get(old_zone, 0)
                new_rank = zone_order.get(new_zone, 0)

                if new_rank > old_rank:
                    stats["promoted"] += 1
                else:
                    stats["demoted"] += 1

                engram.zone = new_zone
                logger.debug(f"TEMPER [{old_zone}]→[{new_zone}] {engram.id[:8]}…")

        # ── Phase 2: Ghost Check ──
        hot_ids = {e.id for e in engrams.values() if e.zone in (ZONE_HOT, ZONE_ANCHOR)}

        for engram in list(engrams.values()):
            if engram.zone == ZONE_SILENT and engram.is_active:
                score = self.compute_reawaken_score(
                    engram, session_tokens, hot_ids
                )

                if score > 0.80:
                    engram.zone = ZONE_HOT
                    engram.last_seen = __import__("time").time()
                    stats["reawakened"] += 1
                    logger.info(f"^^ REAWAKEN → [H] {engram.id[:8]}… score={score:.2f}")

                elif score > 0.50:
                    engram.zone = ZONE_WARM
                    engram.last_seen = __import__("time").time()
                    stats["reawakened"] += 1
                    logger.info(f"^^ REAWAKEN → [W] {engram.id[:8]}… score={score:.2f}")

        # ── Phase 3: Fossil Marking ──
        for engram in engrams.values():
            if engram.zone == ZONE_COLD and engram.age_days > 180:
                if "fossil" not in engram.tags:
                    engram.tags.append("fossil")
                    stats["fossilized"] += 1

        # ── Phase 4: Anchor Protection ──
        for engram in engrams.values():
            if (engram.confidence > 0.95 and
                    engram.access_count > 20 and
                    engram.zone != ZONE_ANCHOR):
                engram.crystallize()
                stats["crystallized"] += 1
                logger.info(f"◆ CRYSTALLIZE → [A] {engram.id[:8]}…")

        # Count final zones
        for engram in engrams.values():
            z = engram.zone
            if z in stats["zone_counts"]:
                stats["zone_counts"][z] += 1

        logger.info(
            f"AUDIT complete — promoted:{stats['promoted']} "
            f"demoted:{stats['demoted']} reawakened:{stats['reawakened']} "
            f"fossilized:{stats['fossilized']} crystallized:{stats['crystallized']}"
        )

        return stats
