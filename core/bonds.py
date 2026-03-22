"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — AXON Bond Engine                       ║
║  NRNLANG-Ω: WEAVE engram_A :: engram_B                   ║
║  <=> LINKS — bidirectional relationship                   ║
╚══════════════════════════════════════════════════════════╝

FORMULA H — BOND STRENGTH:
  synapse = TIME_BOND + WORD_BOND + EMOTION_BOND

  TIME_BOND:   created within 180s → up to 0.30
  WORD_BOND:   3+ shared tokens    → up to 0.50
  EMOTION_BOND: same emotion       → 0.10

  REINFORCEMENT: +0.05 per co-retrieval
  PRUNING: remove if synapse < 0.05
"""

import time
import logging

from core.node import Engram
from core.surprise import Amygdala
from core.soma import AxonRecord, AXON_TYPE_TIME, AXON_TYPE_WORD, AXON_TYPE_EMOTION, AXON_TYPE_HERALD, AXON_TYPE_REINFORCE, SomaDB

logger = logging.getLogger("NEURONX.AXON")


class BondEngine:
    """
    NRNLANG-Ω: AXON ENGINE — Creates and manages bonds between engrams.

    After each PULSE (conversation session), the AXON ENGINE
    processes all session engrams and creates/reinforces bonds.
    """

    def __init__(self):
        self.amygdala = Amygdala()

    def compute_time_bond(self, engram_a: Engram, engram_b: Engram) -> float:
        """
        NRNLANG-Ω: TIME_BOND

        IF |born_A − born_B| <= 180 seconds:
          time_factor = 1.0 − (|born_A − born_B| / 180)
          TIME_BOND = 0.30 × time_factor
        ELSE:
          TIME_BOND = 0.0
        """
        time_diff = abs(engram_a.born - engram_b.born)

        if time_diff <= 180:
            time_factor = 1.0 - (time_diff / 180.0)
            return 0.30 * time_factor
        return 0.0

    def compute_word_bond(self, engram_a: Engram, engram_b: Engram) -> float:
        """
        NRNLANG-Ω: WORD_BOND

        tokens_A = meaningful tokens from engram_A.raw
        tokens_B = meaningful tokens from engram_B.raw
        shared = |tokens_A ∩ tokens_B|
        IF shared >= 3:
          WORD_BOND = (shared / |tokens_A ∪ tokens_B|) × 0.50
        ELSE:
          WORD_BOND = 0.0
        """
        tokens_a = self.amygdala.tokenize(engram_a.raw)
        tokens_b = self.amygdala.tokenize(engram_b.raw)

        shared = len(tokens_a & tokens_b)

        if shared >= 3:
            union = len(tokens_a | tokens_b)
            if union == 0:
                return 0.0
            return (shared / union) * 0.50
        return 0.0

    def compute_emotion_bond(self, engram_a: Engram, engram_b: Engram) -> float:
        """
        NRNLANG-Ω: EMOTION_BOND

        IF engram_A.emotion == engram_B.emotion AND emotion ≠ neutral:
          EMOTION_BOND = 0.10
        ELSE:
          EMOTION_BOND = 0.0
        """
        if (engram_a.emotion == engram_b.emotion and
                engram_a.emotion != "neutral"):
            return 0.10
        return 0.0

    def compute_synapse(self, engram_a: Engram, engram_b: Engram) -> float:
        """
        NRNLANG-Ω: WEAVE — compute total bond strength.
        FINAL_SYNAPSE = min(1.0, TIME_BOND + WORD_BOND + EMOTION_BOND)
        """
        time_bond = self.compute_time_bond(engram_a, engram_b)
        word_bond = self.compute_word_bond(engram_a, engram_b)
        emotion_bond = self.compute_emotion_bond(engram_a, engram_b)

        return min(1.0, time_bond + word_bond + emotion_bond)

    def determine_primary_type(
        self, engram_a: Engram, engram_b: Engram
    ) -> int:
        """Determine the primary bond type based on strongest component."""
        time_bond = self.compute_time_bond(engram_a, engram_b)
        word_bond = self.compute_word_bond(engram_a, engram_b)
        emotion_bond = self.compute_emotion_bond(engram_a, engram_b)

        scores = {
            AXON_TYPE_TIME: time_bond,
            AXON_TYPE_WORD: word_bond,
            AXON_TYPE_EMOTION: emotion_bond,
        }

        return max(scores, key=scores.get)

    def process_session(
        self,
        session_engrams: list[Engram],
        soma: SomaDB,
    ):
        """
        NRNLANG-Ω: PULSE ends → AXON_ENGINE processes session.

        FOR every pair (A, B) in session_engram_list:
          synapse = TIME_BOND + WORD_BOND + EMOTION_BOND
          IF synapse >= 0.05:
            WEAVE A :: B {synapse}

        Also prunes weak axons.
        """
        if len(session_engrams) < 2:
            return

        bonds_created = 0
        bonds_reinforced = 0

        for i in range(len(session_engrams)):
            for j in range(i + 1, len(session_engrams)):
                a = session_engrams[i]
                b = session_engrams[j]

                synapse = self.compute_synapse(a, b)

                if synapse >= 0.05:
                    # Check if axon already exists
                    existing = None
                    for axon in soma.axons:
                        if (axon.from_id == a.id and axon.to_id == b.id) or \
                           (axon.from_id == b.id and axon.to_id == a.id):
                            existing = axon
                            break

                    if existing:
                        # Reinforce existing bond
                        existing.synapse = min(1.0, existing.synapse + 0.05)
                        existing.reinforced = time.time()
                        bonds_reinforced += 1

                        # Update engram axon maps
                        a.axons[b.id] = existing.synapse
                        b.axons[a.id] = existing.synapse
                    else:
                        # Create new bond
                        bond_type = self.determine_primary_type(a, b)
                        axon = AxonRecord(
                            from_id=a.id,
                            to_id=b.id,
                            synapse=synapse,
                            born=time.time(),
                            reinforced=time.time(),
                            axon_type=bond_type,
                        )
                        soma.axons.append(axon)
                        bonds_created += 1

                        # Update engram axon maps
                        a.axons[b.id] = synapse
                        b.axons[a.id] = synapse

        # Prune weak axons
        soma.prune_weak_axons(threshold=0.05)

        if bonds_created or bonds_reinforced:
            logger.info(
                f"AXON ENGINE — {bonds_created} new bonds, "
                f"{bonds_reinforced} reinforced"
            )

    def create_herald_bond(
        self,
        trigger: Engram,
        reawakened: Engram,
        soma: SomaDB,
    ):
        """
        NRNLANG-Ω: HERALD BOND — one memory triggered reawakening of another.
        These bonds decay twice as slowly as normal bonds.
        """
        axon = AxonRecord(
            from_id=trigger.id,
            to_id=reawakened.id,
            synapse=0.50,
            born=time.time(),
            reinforced=time.time(),
            axon_type=AXON_TYPE_HERALD,
        )
        soma.axons.append(axon)

        trigger.axons[reawakened.id] = 0.50
        reawakened.axons[trigger.id] = 0.50

        logger.info(
            f"HERALD BOND ^^  {trigger.id[:8]}… → {reawakened.id[:8]}…"
        )
