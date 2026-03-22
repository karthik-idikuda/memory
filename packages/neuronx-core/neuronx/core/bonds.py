"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — AXON Bond Engine                       ║
║  NRNLANG-Ω: WEAVE engram_A <=> engram_B :::             ║
╚══════════════════════════════════════════════════════════╝

FORMULA H — BOND STRENGTH:
  SYNAPSE(a, b) = min(1.0, TIME_BOND + WORD_BOND + EMOTION_BOND)

  TIME_BOND(a, b):   |born_A − born_B| <= 180s → 0.30 × (1 - delta/180)
  WORD_BOND(a, b):   3+ shared tokens → (shared/union) × 0.50
  EMOTION_BOND(a, b): same non-neutral emotion → 0.10

  REINFORCE: +0.05 per co-retrieval
  PRUNE_THRESHOLD: 0.05
  HERALD_DECAY_FACTOR: 0.5

BUG-008 FIX: prune_weak_bonds removes from BOTH sides of each bond pair.
"""

import time
import logging
from typing import List, Dict, Set

from neuronx.config import (
    BOND_PRUNE_THRESHOLD, BOND_REINFORCE_AMOUNT, BOND_TIME_WINDOW,
    BOND_TIME_MAX, BOND_WORD_MIN_SHARED, BOND_WORD_MAX,
    BOND_EMOTION_VALUE, MAX_SYNAPSE, HERALD_DECAY_FACTOR,
    AXON_TYPE_TIME, AXON_TYPE_WORD, AXON_TYPE_EMOTION,
    AXON_TYPE_HERALD,
)
from neuronx.core.node import EngramNode
from neuronx.core.soma import SomaDB, AxonRecord
from neuronx.utils.tokenizer import tokenize

logger = logging.getLogger("NEURONX.AXON")


class BondEngine:
    """
    NRNLANG-Ω: AXON ENGINE — Creates and manages bonds between engrams.

    After each PULSE (conversation session), the AXON ENGINE
    processes all session engrams and creates/reinforces bonds.
    """

    @staticmethod
    def compute_time_bond(a: EngramNode, b: EngramNode) -> float:
        """
        NRNLANG-Ω: TIME_BOND(a, b)
          delta = abs(a.born - b.born)
          if delta <= 180: return 0.30 × (1.0 - delta/180)
          return 0.0
        """
        delta = abs(a.born - b.born)
        if delta <= BOND_TIME_WINDOW:
            return BOND_TIME_MAX * (1.0 - delta / BOND_TIME_WINDOW)
        return 0.0

    @staticmethod
    def compute_word_bond(a: EngramNode, b: EngramNode) -> float:
        """
        NRNLANG-Ω: WORD_BOND(a, b)
          shared = |tokens_A ∩ tokens_B|
          if shared >= 3: return (shared / union) × 0.50
          return 0.0
        """
        ta = tokenize(a.raw)
        tb = tokenize(b.raw)
        shared = ta & tb
        union = ta | tb
        if len(shared) >= BOND_WORD_MIN_SHARED and len(union) > 0:
            return (len(shared) / len(union)) * BOND_WORD_MAX
        return 0.0

    @staticmethod
    def compute_emotion_bond(a: EngramNode, b: EngramNode) -> float:
        """
        NRNLANG-Ω: EMOTION_BOND(a, b)
          if same non-neutral emotion: 0.10
        """
        if a.emotion == b.emotion and a.emotion != "neutral":
            return BOND_EMOTION_VALUE
        return 0.0

    def compute_synapse(self, a: EngramNode, b: EngramNode) -> float:
        """
        NRNLANG-Ω: SYNAPSE(a, b) = min(1.0, TIME + WORD + EMOTION)
        """
        return min(
            MAX_SYNAPSE,
            self.compute_time_bond(a, b)
            + self.compute_word_bond(a, b)
            + self.compute_emotion_bond(a, b),
        )

    def determine_primary_type(self, a: EngramNode, b: EngramNode) -> int:
        """Determine the primary bond type based on strongest component."""
        scores = {
            AXON_TYPE_TIME: self.compute_time_bond(a, b),
            AXON_TYPE_WORD: self.compute_word_bond(a, b),
            AXON_TYPE_EMOTION: self.compute_emotion_bond(a, b),
        }
        return max(scores, key=scores.get)

    def process_session(
        self,
        session_engrams: List[EngramNode],
        soma: SomaDB,
    ) -> Dict[str, int]:
        """
        NRNLANG-Ω: PULSE ends → AXON_ENGINE processes session.

        FOR every pair (A, B) in session:
          synapse = TIME_BOND + WORD_BOND + EMOTION_BOND
          IF synapse >= 0.05: WEAVE A <=> B {synapse} :::
        Then: auto-prune (BUG-008 FIX).
        """
        stats = {"created": 0, "reinforced": 0, "pruned": 0}

        if len(session_engrams) < 2:
            return stats

        for i in range(len(session_engrams)):
            for j in range(i + 1, len(session_engrams)):
                a = session_engrams[i]
                b = session_engrams[j]
                synapse = self.compute_synapse(a, b)

                if synapse >= BOND_PRUNE_THRESHOLD:
                    existing = None
                    for axon in soma.axons:
                        if (axon.from_id == a.id and axon.to_id == b.id) or \
                           (axon.from_id == b.id and axon.to_id == a.id):
                            existing = axon
                            break

                    if existing:
                        existing.synapse = min(MAX_SYNAPSE, existing.synapse + BOND_REINFORCE_AMOUNT)
                        existing.reinforced = time.time()
                        a.bonds[b.id] = existing.synapse
                        b.bonds[a.id] = existing.synapse
                        stats["reinforced"] += 1
                    else:
                        bond_type = self.determine_primary_type(a, b)
                        axon = AxonRecord(
                            from_id=a.id, to_id=b.id,
                            synapse=synapse, axon_type=bond_type,
                        )
                        soma.axons.append(axon)
                        a.bonds[b.id] = synapse
                        b.bonds[a.id] = synapse
                        stats["created"] += 1

        # BUG-008 FIX: Auto-prune + update both sides
        stats["pruned"] = self.prune_weak_bonds(soma)

        if stats["created"] or stats["reinforced"]:
            logger.info(
                f"AXON ENGINE — {stats['created']} new, "
                f"{stats['reinforced']} reinforced, "
                f"{stats['pruned']} pruned"
            )
        return stats

    def prune_weak_bonds(self, soma: SomaDB) -> int:
        """
        BUG-008 FIX: Prune weak bonds and update BOTH sides.
        If A has bond to B below threshold: remove from A.bonds AND B.bonds.
        """
        to_remove = []
        for axon in soma.axons:
            if axon.synapse < BOND_PRUNE_THRESHOLD:
                to_remove.append(axon)

        for axon in to_remove:
            soma.axons.remove(axon)
            # Update BOTH sides of the bond
            a = soma.get_engram(axon.from_id)
            b = soma.get_engram(axon.to_id)
            if a and axon.to_id in a.bonds:
                del a.bonds[axon.to_id]
            if b and axon.from_id in b.bonds:
                del b.bonds[axon.from_id]

        return len(to_remove)

    def create_herald_bond(
        self,
        trigger: EngramNode,
        reawakened: EngramNode,
        soma: SomaDB,
    ) -> None:
        """
        NRNLANG-Ω: HERALD BOND — one memory triggered reawakening of another.
        Herald bonds decay twice as slowly (HERALD_DECAY_FACTOR = 0.5).
        """
        axon = AxonRecord(
            from_id=trigger.id, to_id=reawakened.id,
            synapse=0.50, axon_type=AXON_TYPE_HERALD,
        )
        soma.axons.append(axon)
        trigger.bonds[reawakened.id] = 0.50
        reawakened.bonds[trigger.id] = 0.50
        logger.info(f"HERALD BOND ^^ {trigger.id[:8]}… → {reawakened.id[:8]}…")
