"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — NeuronBrain Orchestrator               ║
║  NRNLANG-Ω: CORTEX BRAIN — the master controller        ║
╚══════════════════════════════════════════════════════════╝

NeuronBrain is the main entry point for the NEURON-X engine.
It orchestrates all subsystems:
  AMYGDALA  → surprise scoring + emotion detection
  SOMA-DB   → persistent binary storage
  CORTEX    → WSRA-X retrieval
  AXON      → bond engine
  THERMAL   → zone management
  CLASH     → contradiction detection
  EXTRACTOR → memory extraction from text
  INJECTOR  → context formatting for AI
  SCHEDULER → auto-audit at intervals
  INDEXER   → subject index for fast lookup

Public API:
  brain = NeuronBrain("my_brain")
  brain.remember("user loves coffee") → RememberResult
  brain.recall("what does user like?") → [(EngramNode, float)]
  brain.inject(memories) → str
  brain.get_context(msg, top_k=7, remember=True) → ContextResult
  brain.run_audit() → AuditResult
  brain.get_stats() → dict
  brain.export(format="json") → str
  brain.end_session() → None
"""

import time
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any

from neuronx.config import (
    ZONE_HOT, ZONE_WARM, DEFAULT_TOP_K, AUTO_SAVE_INTERVAL,
)
from neuronx.core.node import EngramNode
from neuronx.core.integrity import generate_engram_id
from neuronx.core.soma import SomaDB
from neuronx.core.surprise import Amygdala, SurpriseResult
from neuronx.core.retrieval import RetrievalEngine
from neuronx.core.bonds import BondEngine
from neuronx.core.zones import ThermalManager
from neuronx.brain.contradiction import ContradictionEngine
from neuronx.brain.extractor import MemoryExtractor
from neuronx.brain.injector import ContextInjector
from neuronx.brain.scheduler import AuditScheduler
from neuronx.brain.indexer import SubjectIndex
from neuronx.utils.tokenizer import tokenize

logger = logging.getLogger("NEURONX.BRAIN")


@dataclass
class RememberResult:
    """Result of a remember() call."""
    action: str               # ECHO / FORGE / CLASH
    engram_id: str            # ID of the stored/matched engram
    surprise_score: float     # Surprise score
    is_new: bool              # True if new engram was created
    conflict: Optional[dict] = None  # Conflict info if CLASH


@dataclass
class ContextResult:
    """Result of get_context() call."""
    system_prompt_addition: str
    memories_used: List[Tuple[EngramNode, float]]
    action: str
    nrnlang_log: List[str] = field(default_factory=list)


class NeuronBrain:
    """
    NRNLANG-Ω: NEURON BRAIN — The master orchestrator.

    PULSE begins T[timestamp]
      INPUT ~> AMYGDALA ~> HIPPOCAMPUS ~> SOMA
      CORTEX << SOMA @7 AI
    PULSE ends
      AXON_ENGINE WEAVE ::: THERMAL_AUDIT NMP_WRITE ✓
    """

    def __init__(
        self,
        name: str = "default",
        data_dir: str = "data",
        config: Optional[dict] = None,
    ):
        self.name = name
        self.data_dir = Path(data_dir)
        self.soma_path = str(self.data_dir / f"{name}.soma")

        # Core engines
        self.soma = SomaDB(self.soma_path, brain_name=name)
        self.amygdala = Amygdala()
        self.retrieval = RetrievalEngine()
        self.bonds = BondEngine()
        self.thermal = ThermalManager()
        self.contradiction = ContradictionEngine()
        self.extractor = MemoryExtractor()
        self.injector = ContextInjector()
        self.scheduler = AuditScheduler()
        self.indexer = SubjectIndex()

        # Session state
        self.session_engrams: List[EngramNode] = []
        self.session_tokens: frozenset = frozenset()
        self.interaction_count: int = 0

        # Load existing data
        self.soma.load()
        self.indexer.rebuild(self.soma.engrams)

        # BUG-007 FIX: Run reawakening at session start
        self.thermal.check_reawakenings(self.soma.engrams, frozenset())

        logger.info(f"BRAIN '{name}' initialized — {len(self.soma.engrams)} engrams loaded")

    def remember(
        self,
        text: str,
        source: str = "user",
        emotion: Optional[str] = None,
        decay_class: Optional[str] = None,
    ) -> RememberResult:
        """
        NRNLANG-Ω: FORGE engram("text") >> SOMA

        Process input through AMYGDALA, store/reinforce/clash,
        then return the result.
        """
        # Extract memories from text
        items = self.extractor.extract(text)
        if not items:
            items = [{"text": text, "emotion": "neutral", "decay_class": "fact"}]

        # Process first extracted item (primary)
        item = items[0]
        item_text = item["text"]
        item_emotion = emotion or item.get("emotion", "neutral")
        item_decay = decay_class or item.get("decay_class", "fact")

        # Surprise computation
        result = self.amygdala.compute(item_text, self.soma.engrams)

        # BUG-009 FIX: increment and check audit
        should_audit = self.scheduler.tick()

        if result.action == "ECHO":
            # Reinforce existing memory
            if result.best_match_id and result.best_match_id in self.soma.engrams:
                engram = self.soma.engrams[result.best_match_id]
                engram.strengthen()
                self.session_engrams.append(engram)
                self._update_session_tokens(item_text)
                self._auto_save()

                if should_audit:
                    self.run_audit()

                return RememberResult(
                    action="ECHO",
                    engram_id=engram.id,
                    surprise_score=result.surprise_score,
                    is_new=False,
                )

        # FORGE or CLASH — create new engram
        now = time.time()
        engram = EngramNode(
            id=generate_engram_id(item_text),
            raw=item_text,
            born=now,
            last_seen=now,
            valid_from=now,
            surprise_score=result.surprise_score,
            weight=1.0,
            confidence=0.80,
            decay_class=item_decay,
            emotion=item_emotion,
            source=source,
            zone=ZONE_HOT if result.surprise_score > 0.7 else ZONE_WARM,
        )

        self.soma.add_engram(engram)
        self.indexer.add(engram)
        self.session_engrams.append(engram)
        self._update_session_tokens(item_text)

        # Handle CLASH
        conflict = None
        if result.action == "CLASH" and result.best_match_id:
            # Use subject index for fast candidate lookup (BUG-014)
            candidate_ids = self.indexer.find_candidates(item_text)
            candidates = {
                eid: self.soma.engrams[eid]
                for eid in candidate_ids
                if eid in self.soma.engrams
            }
            conflict = self.contradiction.check_and_resolve(engram, candidates)

        # Process additional extracted items
        for extra in items[1:]:
            extra_result = self.amygdala.compute(extra["text"], self.soma.engrams)
            if extra_result.action != "ECHO":
                extra_engram = EngramNode(
                    id=generate_engram_id(extra["text"]),
                    raw=extra["text"],
                    born=now, last_seen=now, valid_from=now,
                    surprise_score=extra_result.surprise_score,
                    decay_class=extra.get("decay_class", "fact"),
                    emotion=extra.get("emotion", "neutral"),
                    source=source,
                    zone=ZONE_WARM,
                )
                self.soma.add_engram(extra_engram)
                self.indexer.add(extra_engram)
                self.session_engrams.append(extra_engram)

        self._auto_save()

        if should_audit:
            self.run_audit()

        return RememberResult(
            action=result.action,
            engram_id=engram.id,
            surprise_score=result.surprise_score,
            is_new=True,
            conflict=conflict,
        )

    def recall(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> List[Tuple[EngramNode, float]]:
        """
        NRNLANG-Ω: CORTEX ?? query @7 → RANKED top[K]
        """
        # BUG-007: Update session tokens for reawakening
        self._update_session_tokens(query)
        self.thermal.check_reawakenings(self.soma.engrams, self.session_tokens)

        return self.retrieval.retrieve(query, self.soma.engrams, top_k=top_k)

    def inject(self, memories: List[Tuple[EngramNode, float]]) -> str:
        """
        NRNLANG-Ω: @> PUSH_TO_AI — format memories for system prompt.
        """
        return self.injector.inject(memories)

    def get_context(
        self,
        message: str,
        top_k: int = DEFAULT_TOP_K,
        remember: bool = True,
    ) -> ContextResult:
        """
        Universal integration endpoint.
        Recalls relevant memories, optionally remembers the message,
        returns formatted context for AI injection.
        """
        # Recall first
        memories = self.recall(message, top_k=top_k)
        system_addition = self.inject(memories)

        # Remember if requested
        action = "RECALL"
        if remember:
            result = self.remember(message)
            action = result.action

        return ContextResult(
            system_prompt_addition=system_addition,
            memories_used=memories,
            action=action,
        )

    def run_audit(self) -> dict:
        """NRNLANG-Ω: AUDIT — full thermal check."""
        stats = self.thermal.audit(self.soma.engrams, self.session_tokens)
        self.soma.save()
        return stats

    def get_stats(self) -> dict:
        """Get brain statistics."""
        stats = self.soma.get_stats()
        stats["brain_name"] = self.name
        stats["session_engrams"] = len(self.session_engrams)
        stats["interaction_count"] = self.scheduler.interaction_count
        return stats

    def end_session(self) -> None:
        """
        NRNLANG-Ω: PULSE ends
          AXON_ENGINE WEAVE ::: THERMAL_AUDIT NMP_WRITE ✓
        """
        # Bond processing
        if self.session_engrams:
            self.bonds.process_session(self.session_engrams, self.soma)

        # Thermal audit
        self.thermal.audit(self.soma.engrams, self.session_tokens)

        # Save
        self.soma.save()

        # Reset session
        self.session_engrams.clear()
        self.session_tokens = frozenset()
        logger.info("PULSE ended — bonds processed, audit complete, saved")

    def export(self, format: str = "json", path: Optional[str] = None) -> str:
        """Export brain data."""
        from neuronx.utils.exporter import BrainExporter
        exporter = BrainExporter(self.soma)
        if format == "json":
            return exporter.to_json(path)
        elif format == "markdown":
            return exporter.to_markdown(path)
        elif format == "csv":
            return exporter.to_csv(path)
        elif format == "nrnlang":
            return exporter.to_nrnlang(path)
        else:
            return exporter.to_json(path)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Internal Helpers
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _update_session_tokens(self, text: str) -> None:
        """Add tokens from text to session token pool."""
        new_tokens = tokenize(text)
        self.session_tokens = self.session_tokens | new_tokens

    def _auto_save(self) -> None:
        """Auto-save at interval."""
        self.interaction_count += 1
        if self.interaction_count % AUTO_SAVE_INTERVAL == 0:
            self.soma.save()
