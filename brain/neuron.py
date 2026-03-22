"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Main Brain Orchestrator                ║
║  NRNLANG-Ω: ENGRAMMAP — The complete memory network      ║
╚══════════════════════════════════════════════════════════╝

The NeuronBrain is the central orchestrator connecting all layers:
  INPUT_PROCESSOR → AMYGDALA → HIPPOCAMPUS → CONTRADICTION_ENGINE
  → AXON_ENGINE → THERMAL_MANAGER → SOMA

It manages the full memory lifecycle through every PULSE (session).
"""

import json
import time
import logging
import os

from core.node import (
    Engram, ZONE_WARM, ZONE_HOT, ZONE_COLD, ZONE_SILENT,
    TRUTH_ACTIVE, TRUTH_CONFLICT,
)
from core.integrity import generate_engram_id
from core.soma import SomaDB
from core.surprise import Amygdala
from core.retrieval import RetrievalEngine
from core.bonds import BondEngine
from core.zones import ThermalManager
from brain.contradiction import ContradictionEngine

logger = logging.getLogger("NEURONX.BRAIN")


class NeuronBrain:
    """
    NRNLANG-Ω: The Brain — connects everything.

    LIVECORE: The HOT zone — active conscious memory
    THOUGHTFIELD: All currently HOT memories
    ENGRAMMAP: Complete network of all memories + connections

    Methods:
      process_input()   → INPUT ~> AMYGDALA ~> HIPPOCAMPUS ~> SOMA
      query()           → CORTEX ?? query ~> @7 TOP_SEVEN
      audit()           → THERMAL AUDIT of all zones
      get_brain_stats() → BRAIN STATUS report
    """

    def __init__(
        self,
        soma_path: str,
        ai_client=None,
        model: str = "claude-sonnet-4-20250514",
    ):
        # ── Initialize all layers ──
        self.soma = SomaDB(soma_path)
        self.amygdala = Amygdala()
        self.retrieval = RetrievalEngine()
        self.bonds = BondEngine()
        self.thermal = ThermalManager()
        self.contradiction = ContradictionEngine(ai_client, model)

        # AI client for memory extraction + conversation
        self.ai_client = ai_client
        self.model = model

        # Session (PULSE) tracking
        self.session_engrams: list[Engram] = []
        self.session_tokens: set = set()
        self.session_log: list[dict] = []  # NRNLANG-Ω operation log
        self.pulse_count: int = 0
        self.interaction_count: int = 0

        # Load brain from SOMA file
        self.soma.load()
        logger.info(f"BRAIN initialized — {self.soma}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PULSE (Session) Management
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def start_pulse(self):
        """
        NRNLANG-Ω: PULSE begins — start a new conversation session.
        """
        self.pulse_count += 1
        self.session_engrams = []
        self.session_tokens = set()
        self.session_log = []  # NRNLANG-Ω: reset session log
        logger.info(f"━━━ PULSE #{self.pulse_count} begins ━━━")

    def end_pulse(self):
        """
        NRNLANG-Ω: PULSE ends — process bonds and save.

        After each conversation session:
        1. AXON_ENGINE processes session pairs → create bonds
        2. THERMAL_MANAGER runs if threshold reached
        3. SOMA saves to file
        """
        # Process bonds for this session
        if len(self.session_engrams) >= 2:
            self.bonds.process_session(self.session_engrams, self.soma)

        # Run audit if threshold reached
        if self.interaction_count % 100 == 0 and self.interaction_count > 0:
            self.audit()

        # Save to SOMA
        self.soma.save()
        logger.info(f"━━━ PULSE #{self.pulse_count} ends ━━━")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # INPUT PROCESSING (Layer 1 → Layer 3)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def process_input(self, user_message: str) -> list[dict]:
        """
        NRNLANG-Ω: USER_INPUT ~> INPUT_PROCESSOR ~> AMYGDALA ~> HIPPOCAMPUS

        Full pipeline:
        1. INPUT_PROCESSOR splits and classifies
        2. AMYGDALA scores surprise for each idea
        3. HIPPOCAMPUS routes to ECHO / FORGE / CLASH
        4. Results stored in SOMA

        Returns list of processing results.
        """
        self.interaction_count += 1

        # Accumulate session tokens
        new_tokens = self.amygdala.tokenize(user_message)
        self.session_tokens.update(new_tokens)

        # Process through AMYGDALA
        existing = list(self.soma.engrams.values())
        processed = self.amygdala.process_input(user_message, existing)

        results = []

        for idea in processed:
            text = idea["text"]
            emotion = idea["emotion"]
            decay_class = idea["decay_class"]
            surprise = idea["surprise"]
            best_match = idea["best_match"]
            action = idea["action"]

            result = {
                "text": text,
                "action": action,
                "surprise": surprise,
                "emotion": emotion,
                "decay_class": decay_class,
                "engram_id": None,
                "clash_result": None,
            }

            if action == "ECHO":
                # ── ECHO: strengthen existing memory ──
                if best_match:
                    best_match.strengthen(0.15)
                    best_match.confirm(0.05)
                    if best_match.zone in (ZONE_COLD, ZONE_SILENT):
                        best_match.zone = ZONE_WARM
                    self.soma.add_engram(best_match)  # update
                    result["engram_id"] = best_match.id
                    # NRNLANG-Ω: log ECHO operation
                    self.session_log.append({
                        "action": "ECHO",
                        "text": text,
                        "match_id": best_match.id,
                        "surprise": surprise,
                        "emotion": emotion,
                    })
                    logger.info(
                        f"● ECHO +++ {best_match.id[:8]}… "
                        f"'{text[:40]}…' surprise={surprise:.2f}"
                    )

            elif action == "FORGE":
                # ── FORGE: create new engram ──
                engram = self._create_engram(text, emotion, decay_class, surprise)
                self.soma.add_engram(engram)
                self.session_engrams.append(engram)
                result["engram_id"] = engram.id
                # NRNLANG-Ω: log FORGE operation
                self.session_log.append({
                    "action": "FORGE",
                    "text": text,
                    "surprise": surprise,
                    "emotion": emotion,
                    "decay_class": decay_class,
                    "confidence": engram.confidence,
                })
                logger.info(
                    f"⊕ FORGE [{engram.zone}] {engram.id[:8]}… "
                    f"'{text[:40]}…' surprise={surprise:.2f}"
                )

            elif action == "CLASH":
                # ── CLASH: potential contradiction ──
                if best_match:
                    # Create the new engram first
                    engram = self._create_engram(
                        text, emotion, decay_class, surprise
                    )

                    # Detect contradiction
                    clash = self.contradiction.detect_contradiction_heuristic(
                        text, best_match
                    )

                    if clash.is_contradiction:
                        # Try AI if available
                        if self.ai_client:
                            clash = self.contradiction.detect_contradiction_ai(
                                text, best_match
                            )

                        resolution = self.contradiction.resolve(
                            engram, best_match, clash
                        )
                        result["clash_result"] = resolution

                        if resolution == "NOT_CLASH":
                            # Not actually a clash — just forge it
                            action = "FORGE"
                    else:
                        # Not a real clash — forge normally
                        action = "FORGE"

                    self.soma.add_engram(engram)
                    self.soma.add_engram(best_match)  # update old
                    self.session_engrams.append(engram)
                    result["engram_id"] = engram.id
                    result["action"] = action

                    logger.info(
                        f"## CLASH {engram.id[:8]}… vs {best_match.id[:8]}… "
                        f"→ {result.get('clash_result', 'FORGE')}"
                    )
                else:
                    # No match to clash with — just forge
                    engram = self._create_engram(
                        text, emotion, decay_class, surprise
                    )
                    self.soma.add_engram(engram)
                    self.session_engrams.append(engram)
                    result["engram_id"] = engram.id
                    result["action"] = "FORGE"

            results.append(result)

        # Auto-save periodically
        if self.interaction_count % 5 == 0:
            self.soma.save()

        return results

    def _create_engram(
        self,
        text: str,
        emotion: str,
        decay_class: str,
        surprise: float,
    ) -> Engram:
        """Create a new ENGRAM with all fields initialized."""
        now = time.time()
        return Engram(
            id=generate_engram_id(text, now),
            raw=text,
            born=now,
            last_seen=now,
            valid_from=now,
            heat=0.5,
            spark=surprise,
            weight=1.0,
            confidence=0.80,
            decay_class=decay_class,
            emotion=emotion,
            tags=[],
            zone=ZONE_WARM,
            truth=TRUTH_ACTIVE,
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # RETRIEVAL (Layer 8)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def query(self, query_text: str, top_k: int = 7) -> list[tuple[Engram, float]]:
        """
        NRNLANG-Ω: CORTEX ?? query → @7 TOP_SEVEN @> AI

        Retrieve the most relevant memories for the query.
        """
        # Quick ghost scan first
        self._check_reawakenings(query_text)

        # WSRA-X retrieval
        engrams = list(self.soma.engrams.values())
        results = self.retrieval.query(query_text, engrams, top_k=top_k)

        return results

    def _check_reawakenings(self, context_text: str):
        """Quick ghost scan for potential reawakenings."""
        context_tokens = self.amygdala.tokenize(context_text)
        hot_ids = {e.id for e in self.soma.hot_engrams}

        for engram in self.soma.silent_engrams:
            if not engram.is_active:
                continue

            score = self.thermal.compute_reawaken_score(
                engram, context_tokens, hot_ids
            )

            if score > 0.50:
                new_zone = ZONE_HOT if score > 0.80 else ZONE_WARM
                engram.zone = new_zone
                engram.last_seen = time.time()
                logger.info(
                    f"^^ REAWAKEN [{new_zone}] {engram.id[:8]}… score={score:.2f}"
                )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AUDIT (Layer 6)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def audit(self) -> dict:
        """
        NRNLANG-Ω: AUDIT SOMA — full thermal check.
        """
        logger.info("━━━ AUDIT begins ━━━")
        stats = self.thermal.audit(self.soma.engrams, self.session_tokens)
        self.soma.save()
        logger.info("━━━ AUDIT complete ━━━")
        return stats

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AI CONVERSATION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def chat(self, user_message: str) -> str:
        """
        Full AI chat with memory injection.

        1. Process input → extract and store memories
        2. Query relevant memories
        3. Inject into AI context
        4. Get AI response
        5. Extract memories from AI response (future)
        """
        # Step 1: Process and store memories
        self.process_input(user_message)

        # Step 2: Query relevant memories
        results = self.query(user_message)

        # Step 3: Build memory context
        from interface.prompts import MASTER_SYSTEM_PROMPT, build_memory_context
        memory_context = build_memory_context([e for e, _ in results])
        system_prompt = MASTER_SYSTEM_PROMPT.format(memories=memory_context)

        # Step 4: Get AI response
        if not self.ai_client:
            return self._offline_response(user_message, results)

        try:
            response = self.ai_client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text

        except Exception as e:
            logger.error(f"AI call failed: {e}")
            return self._offline_response(user_message, results)

    def _offline_response(
        self,
        user_message: str,
        results: list[tuple[Engram, float]],
    ) -> str:
        """Generate a response when AI is unavailable."""
        if not results:
            return (
                "💾 Memory stored! I'm running in offline mode (no API key). "
                "Your memories are being saved locally. "
                "Add your ANTHROPIC_API_KEY to .env for full AI responses."
            )

        lines = ["💾 Memories stored! Here are your most relevant memories:\n"]
        for i, (engram, score) in enumerate(results[:5], 1):
            age = f"{engram.age_days:.0f}"
            lines.append(
                f"  {i}. [{engram.zone}] {engram.raw} "
                f"(conf: {engram.confidence:.2f}, age: {age}d)"
            )

        lines.append(
            "\n⚡ Running in offline mode — memories are being stored locally."
        )
        return "\n".join(lines)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BRAIN STATISTICS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_brain_stats(self) -> dict:
        """
        NRNLANG-Ω: PROMPT 7 — brain status report data.
        """
        stats = self.soma.get_stats()
        stats["pulse_count"] = self.pulse_count
        stats["interaction_count"] = self.interaction_count

        # Top 5 hottest memories
        hot_list = sorted(
            self.soma.engrams.values(),
            key=lambda e: e.heat,
            reverse=True,
        )[:5]
        stats["top_hot"] = [
            {"id": e.id[:8], "raw": e.raw[:60], "heat": e.heat}
            for e in hot_list
        ]

        # Top 5 strongest bonds
        strong_bonds = sorted(
            self.soma.axons,
            key=lambda a: a.synapse,
            reverse=True,
        )[:5]
        stats["top_bonds"] = [
            {
                "from": a.from_id[:8],
                "to": a.to_id[:8],
                "synapse": a.synapse,
            }
            for a in strong_bonds
        ]

        return stats

    def get_all_memories(
        self,
        zone: str = None,
        limit: int = 20,
    ) -> list[Engram]:
        """Get memories, optionally filtered by zone."""
        engrams = list(self.soma.engrams.values())

        if zone:
            engrams = [e for e in engrams if e.zone == zone]

        # Sort by last_seen descending
        engrams.sort(key=lambda e: e.last_seen, reverse=True)

        return engrams[:limit]

    def get_active_conflicts(self) -> list[tuple[Engram, Engram]]:
        """Get all pairs of contradicting engrams."""
        conflicts = []
        seen = set()

        for engram in self.soma.engrams.values():
            for contra_id in engram.contradicts:
                pair = tuple(sorted([engram.id, contra_id]))
                if pair not in seen:
                    seen.add(pair)
                    other = self.soma.get_engram(contra_id)
                    if other:
                        conflicts.append((engram, other))

        return conflicts
