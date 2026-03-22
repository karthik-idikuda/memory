"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — CortexAgent                                ║
║  The main 9-step metacognitive thinking loop                 ║
╚══════════════════════════════════════════════════════════════╝

The CORTEX-X Agent Loop (unprecedented):
  1. RECEIVE   → user input arrives
  2. RECALL    → NEURON-X retrieves relevant memories
  3. REASON    → SIGMA-X activates causal chains
  4. THINK     → LLM generates response draft
  5. MONITOR   → METACOG-X scans the draft
  6. RESPOND   → send (possibly modified) response
  7. LEARN     → store thought + trace + update calibration
  8. EVOLVE    → update strategies, check drift, crystallize wisdom
  9. GROW      → measure growth metrics
"""

from __future__ import annotations

import time
from typing import List, Dict, Any, Optional, Callable

from cortex.config import (
    AGENT_AUTO_SAVE_INTERVAL, AGENT_AUDIT_INTERVAL,
    DEFAULT_TOP_K_MEMORIES, DEFAULT_TOP_K_CHAINS,
    CORTEX_BASE_SYSTEM_PROMPT, CORTEX_METACOG_INJECTION_TEMPLATE,
    ZONE_FOCUSED, ZONE_EXPLORING, ZONE_CAUTIOUS,
    ZONE_LEARNING, ZONE_REFLECTING,
)
from cortex.core.thought_node import ThoughtNode
from cortex.core.cortexdb import CortexDB
from cortex.core.integrity import session_id
from cortex.meta.metacog import metacog_score, metacog_breakdown
from cortex.meta.confidence import ConfidenceTracker
from cortex.meta.contradiction import ContradictionDetector
from cortex.meta.hallucination import HallucinationShield
from cortex.meta.drift import DriftDetector
from cortex.meta.patterns import PatternRecognizer
from cortex.meta.wisdom import WisdomCrystallizer
from cortex.meta.strategy import StrategyEngine
from cortex.meta.thought_trace import ThoughtTrace, TraceLogger
from cortex.engine.growth import GrowthEngine
from cortex.engine.conversation import ConversationManager
from cortex.engine.router import LLMRouter


class CortexAgent:
    """The metacognitive AI agent — the heart of CORTEX-X.

    Combines NEURON-X memories, SIGMA-X reasoning, and METACOG-X
    self-awareness into a single agent that learns from every interaction.
    """

    def __init__(
        self,
        brain_path: str = "brain.cortex",
        adapter_name: str = "ollama",
        model: str = "llama3.2",
    ):
        # Core storage
        self.db = CortexDB(brain_path)
        self.brain_path = brain_path

        # Metacognitive engines
        self.confidence = ConfidenceTracker()
        self.contradictions = ContradictionDetector()
        self.hallucination = HallucinationShield()
        self.drift = DriftDetector()
        self.patterns = PatternRecognizer()
        self.wisdom = WisdomCrystallizer()
        self.strategies = StrategyEngine()
        self.growth = GrowthEngine()
        self.trace_logger = TraceLogger()

        # Execution
        self.router = LLMRouter()
        self.conversation = ConversationManager()
        self.adapter_name = adapter_name
        self.model = model

        # State
        self.current_session_id = session_id()
        self.interaction_count: int = 0
        self.current_zone: str = ZONE_FOCUSED

        # Bridges (set externally)
        self._memory_recall_fn: Optional[Callable] = None
        self._causal_recall_fn: Optional[Callable] = None

    def set_memory_bridge(self, recall_fn: Callable) -> None:
        """Set the NEURON-X memory recall function.

        Expected signature: recall_fn(query: str, top_k: int) -> List[Dict]
        """
        self._memory_recall_fn = recall_fn

    def set_causal_bridge(self, recall_fn: Callable) -> None:
        """Set the SIGMA-X causal chain recall function.

        Expected signature: recall_fn(query: str, top_k: int) -> List[Dict]
        """
        self._causal_recall_fn = recall_fn

    def think(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """The main 9-step thinking loop.

        Args:
            user_input: What the user said

        Returns:
            Dict with 'response', 'trace', 'metacog', 'thought_id'
        """
        self.interaction_count += 1
        start_time = time.time()
        trace = self.trace_logger.new_trace()

        # ═══ STEP 1: RECEIVE ═══
        step_start = time.time()
        trace.add_step(
            "receive",
            f"User input: '{user_input[:100]}...' " if len(user_input) > 100 else f"User input: '{user_input}'",
            duration_ms=_elapsed_ms(step_start),
        )

        # ═══ STEP 2: RECALL ═══
        step_start = time.time()
        memories = self._recall_memories(user_input)
        trace.add_step(
            "recall",
            f"Retrieved {len(memories)} relevant memories",
            duration_ms=_elapsed_ms(step_start),
        )
        trace.record_memory_recall(len(memories))

        # ═══ STEP 3: REASON ═══
        step_start = time.time()
        chains = self._recall_chains(user_input)
        trace.add_step(
            "reason",
            f"Activated {len(chains)} causal chains",
            duration_ms=_elapsed_ms(step_start),
        )
        trace.record_chains(len(chains))

        # ═══ STEP 4: THINK ═══
        step_start = time.time()
        context = self._build_context(user_input, memories, chains)
        response = self._generate_response(context)
        trace.add_step(
            "generate",
            f"LLM generated response ({len(response)} chars)",
            duration_ms=_elapsed_ms(step_start),
        )

        # ═══ STEP 5: MONITOR ═══
        step_start = time.time()
        monitor_result = self._metacognitive_monitor(
            response, user_input, memories, chains, trace
        )
        trace.add_step(
            "monitor",
            f"Shield: {monitor_result['shield_level']} | "
            f"Contradictions: {monitor_result['new_contradictions']}",
            duration_ms=_elapsed_ms(step_start),
            flags=monitor_result.get('flags', []),
        )

        # ═══ STEP 6: RESPOND ═══
        confidence = monitor_result.get("confidence", 0.6)
        zone = self._determine_zone(confidence, monitor_result)
        self.current_zone = zone

        # ═══ STEP 7: LEARN ═══
        step_start = time.time()
        thought = self._create_thought(
            user_input, response, confidence, zone, trace
        )
        self.db.add_thought(thought)
        trace.add_step(
            "learn",
            f"Stored thought {thought.id[:8]} in zone {zone}",
            duration_ms=_elapsed_ms(step_start),
        )

        # ═══ STEP 8: EVOLVE ═══
        step_start = time.time()
        self._evolve(user_input, trace)
        trace.add_step(
            "evolve",
            "Updated strategies, checked drift, considered wisdom",
            duration_ms=_elapsed_ms(step_start),
        )

        # ═══ STEP 9: GROW ═══
        step_start = time.time()
        growth_delta = self._measure_growth()
        trace.finalize(confidence, zone, growth_delta)
        trace.add_step(
            "grow",
            f"Growth delta: {growth_delta:+.2%}",
            duration_ms=_elapsed_ms(step_start),
        )

        # Auto-save periodically
        if self.interaction_count % AGENT_AUTO_SAVE_INTERVAL == 0:
            self.save()

        # Periodic metacog audit
        if self.interaction_count % AGENT_AUDIT_INTERVAL == 0:
            self._metacog_audit()

        total_ms = _elapsed_ms(start_time)
        trace.total_time_ms = total_ms

        return {
            "response": response,
            "thought_id": thought.id,
            "confidence": confidence,
            "zone": zone,
            "trace": trace.to_dict(),
            "trace_compact": trace.format_compact(),
            "metacog": self._metacog_snapshot(),
            "total_ms": total_ms,
        }

    def correct(self, thought_id: str, note: str, accuracy: float = 0.0) -> bool:
        """User corrects a previous response."""
        thought = self.db.get_thought(thought_id)
        if not thought:
            return False
        thought.correct(note, accuracy)
        self.confidence.record(thought.confidence, accuracy, thought.domain, thought_id)
        self.patterns.record_error(
            "user_correction",
            thought.domain,
            thought.domain,
            thought_id,
            note,
        )
        return True

    def save(self) -> None:
        """Save brain state."""
        self.db.set_metacog_state({
            "confidence": self.confidence.to_dict(),
            "contradiction": self.contradictions.to_dict(),
            "hallucination": self.hallucination.to_dict(),
            "drift": self.drift.to_dict(),
            "patterns": self.patterns.summary(),
            "wisdom": self.wisdom.to_dict(),
            "strategies": self.strategies.to_dict(),
            "growth": self.growth.to_dict(),
        })
        self.db.save()

    def load(self) -> bool:
        """Load brain state from file."""
        try:
            self.db = CortexDB.load(self.brain_path)
            state = self.db.get_metacog_state()
            if state:
                if "confidence" in state:
                    self.confidence = ConfidenceTracker.from_dict(state["confidence"])
                if "drift" in state:
                    self.drift = DriftDetector.from_dict(state["drift"])
            return True
        except Exception:
            return False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # INTERNAL METHODS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _recall_memories(self, query: str) -> List[Dict[str, str]]:
        """Recall relevant memories from NEURON-X."""
        if self._memory_recall_fn:
            try:
                return self._memory_recall_fn(query, DEFAULT_TOP_K_MEMORIES)
            except Exception:
                pass
        # Fallback: search local thoughts
        thoughts = self.db.search_thoughts(query, DEFAULT_TOP_K_MEMORIES)
        return [{"id": t.id, "content": t.content} for t in thoughts]

    def _recall_chains(self, query: str) -> List[Dict[str, str]]:
        """Recall relevant causal chains from SIGMA-X."""
        if self._causal_recall_fn:
            try:
                return self._causal_recall_fn(query, DEFAULT_TOP_K_CHAINS)
            except Exception:
                pass
        return []

    def _build_context(
        self,
        user_input: str,
        memories: List[Dict[str, str]],
        chains: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        """Build the full conversation context with injected metacognitive state."""
        # Get wisdom axioms relevant to this query
        relevant_axioms = self.wisdom.search_axioms(user_input)
        axiom_text = "\n".join([f"• {a.content}" for a in relevant_axioms[:5]])

        # Get error patterns to avoid
        from cortex.core.tokenizer import detect_domain
        domain = detect_domain(user_input)
        active_patterns = self.patterns.patterns_for_context(domain, domain)
        pattern_text = "\n".join([
            f"• AVOID: {p.error_type} in {p.context_type} (seen {p.frequency}x)"
            for p in active_patterns[:5]
        ])

        # Build memory context
        memory_text = "\n".join([
            f"• {m.get('content', '')[:200]}"
            for m in memories[:5]
        ])

        # Build causal context
        causal_text = "\n".join([
            f"• {c.get('content', '')[:200]}"
            for c in chains[:3]
        ])

        # Inject metacognitive context
        metacog_injection = CORTEX_METACOG_INJECTION_TEMPLATE.format(
            calibration_error=self.confidence.brier_score,
            pattern_count=self.patterns.active_count,
            wisdom_count=self.wisdom.axiom_count,
            growth_trend=self.drift.drift_direction,
            zone=self.current_zone,
            memory_context=memory_text or "No relevant memories found.",
            causal_context=causal_text or "No relevant causal chains.",
            error_patterns=pattern_text or "No active error patterns.",
            wisdom_context=axiom_text or "No relevant wisdom axioms yet.",
        )

        system_prompt = CORTEX_BASE_SYSTEM_PROMPT + metacog_injection

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation.get_context_messages())
        messages.append({"role": "user", "content": user_input})

        return messages

    def _generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate response via LLM router."""
        try:
            return self.router.generate(
                messages=messages,
                adapter_name=self.adapter_name,
                model=self.model,
            )
        except Exception as e:
            return f"[CORTEX-X] LLM error: {str(e)}"

    def _metacognitive_monitor(
        self,
        response: str,
        user_input: str,
        memories: List[Dict[str, str]],
        chains: List[Dict[str, str]],
        trace: ThoughtTrace,
    ) -> Dict[str, Any]:
        """Run all metacognitive checks on the response."""
        flags = []

        # 1. Hallucination shield
        shield_report = self.hallucination.scan(response, memories, chains)
        if shield_report.alert_level != "safe":
            flags.append(f"🛡{shield_report.alert_level.upper()}")

        # 2. Contradiction check
        past_thoughts = [
            {"id": t.id, "content": t.content}
            for t in list(self.db.thoughts.values())[-50:]
        ]
        new_contradictions = self.contradictions.scan(response, past_thoughts)
        if new_contradictions:
            flags.append(f"⟳{len(new_contradictions)} contradictions")

        # 3. Compute confidence (adjusted by calibration)
        raw_confidence = shield_report.evidence_ratio
        adjusted_confidence = self.confidence.suggest_adjusted_confidence(raw_confidence)

        # 4. Check for known patterns
        from cortex.core.tokenizer import detect_domain
        domain = detect_domain(user_input)
        active_pattern = self.patterns.check_for_pattern("any", domain, domain)
        if active_pattern:
            flags.append(f"⟳!PATTERN:{active_pattern.error_type}")
            trace.record_error_avoided(active_pattern.error_type)

        # 5. Apply wisdom
        relevant_axioms = self.wisdom.search_axioms(user_input)
        for axiom in relevant_axioms[:3]:
            trace.record_axiom_applied(axiom.content[:50])

        return {
            "shield_level": shield_report.alert_level,
            "evidence_ratio": shield_report.evidence_ratio,
            "new_contradictions": len(new_contradictions),
            "confidence": adjusted_confidence,
            "flags": flags,
            "domain": domain,
        }

    def _determine_zone(self, confidence: float, monitor: Dict) -> str:
        """Determine cognitive zone from current state."""
        if self.drift.audit_triggered:
            return ZONE_REFLECTING
        if monitor.get("new_contradictions", 0) > 0:
            return ZONE_CAUTIOUS
        if any(t.was_corrected for t in list(self.db.thoughts.values())[-5:]):
            return ZONE_LEARNING
        if confidence < 0.4:
            return ZONE_EXPLORING
        return ZONE_FOCUSED

    def _create_thought(
        self,
        user_input: str,
        response: str,
        confidence: float,
        zone: str,
        trace: ThoughtTrace,
    ) -> ThoughtNode:
        """Create a ThoughtNode from the interaction."""
        from cortex.core.tokenizer import detect_domain, extract_keywords
        domain = detect_domain(user_input + " " + response)
        tags = extract_keywords(user_input + " " + response, top_k=5)

        thought = ThoughtNode(
            content=response[:2000],
            context=user_input[:500],
            confidence=confidence,
            session_id=self.current_session_id,
            zone=zone,
            domain=domain,
            tags=tags,
        )

        # Add to conversation
        self.conversation.add_turn(user_input, response)

        return thought

    def _evolve(self, user_input: str, trace: ThoughtTrace) -> None:
        """Run strategy evolution and wisdom observation."""
        # Observe for wisdom potential
        from cortex.core.tokenizer import detect_domain
        domain = detect_domain(user_input)
        self.wisdom.observe(
            user_input, domain,
            confidence=0.5,
            session_id=self.current_session_id,
        )

    def _measure_growth(self) -> float:
        """Measure growth and record."""
        return self.growth.measure(
            accuracy=self.confidence.calibration_score,
            calibration=1.0 - self.confidence.brier_score,
            hallucination=self.hallucination.hallucination_score,
            strategy=self.strategies.strategy_score,
            wisdom=self.wisdom.wisdom_ratio,
        )

    def _metacog_audit(self) -> None:
        """Run periodic full metacognitive audit."""
        breakdown = metacog_breakdown(
            calibration_score=self.confidence.calibration_score,
            contradiction_score=self.contradictions.contradiction_score,
            hallucination_score=self.hallucination.hallucination_score,
            drift_score=self.drift.drift_score,
            pattern_score=self.patterns.pattern_score,
            wisdom_score=self.wisdom.wisdom_ratio,
            strategy_score=self.strategies.strategy_score,
            growth_score=0.5,
        )
        self.drift.acknowledge_audit()

    def _metacog_snapshot(self) -> Dict[str, Any]:
        """Quick snapshot of metacognitive state."""
        return {
            "calibration": round(self.confidence.calibration_score, 2),
            "hallucination_score": round(self.hallucination.hallucination_score, 2),
            "contradiction_density": round(self.contradictions.density, 2),
            "drift_signal": round(self.drift.current_drift, 4),
            "active_patterns": self.patterns.active_count,
            "wisdom_count": self.wisdom.axiom_count,
            "zone": self.current_zone,
            "interaction_count": self.interaction_count,
        }

    @property
    def stats(self) -> Dict[str, Any]:
        """Full brain statistics."""
        return {
            "brain": self.db.stats(),
            "metacog": self._metacog_snapshot(),
            "session_id": self.current_session_id,
            "interactions": self.interaction_count,
        }


def _elapsed_ms(start: float) -> float:
    """Compute elapsed milliseconds."""
    return (time.time() - start) * 1000
