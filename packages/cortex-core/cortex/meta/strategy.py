"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Strategy Evolution Engine                   ║
║  Self-evolving approach optimization via fitness selection    ║
╚══════════════════════════════════════════════════════════════╝

Strategies are approaches to task types that evolve over time.
The AI learns which approaches work best for which situations.

Algorithm:
  1. Select highest-fitness strategy for task type
  2. Execute, record outcome
  3. Periodically: MUTATE best, PRUNE worst, CROSSOVER top 2
  4. Fitness = success_rate × log(usage_count + 1)
"""

from __future__ import annotations

import time
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import defaultdict

from cortex.config import (
    STRATEGY_MAX_PER_TASK,
    STRATEGY_MIN_TRIALS,
    STRATEGY_EVOLUTION_RATE,
    STRATEGY_PRUNE_THRESHOLD,
    STRATEGY_CROSSOVER_RATE,
)


@dataclass
class StrategyRecord:
    """Record of a strategy's performance on a single trial."""
    success: bool
    timestamp: float = 0.0
    context: str = ""
    notes: str = ""

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class Strategy:
    """A task-solving approach that evolves over time."""
    strategy_id: str
    task_type: str
    approach: str                 # description of the approach
    prompt_template: str = ""     # optional prompt template
    trials: List[StrategyRecord] = field(default_factory=list)
    created_at: float = 0.0
    parent_id: Optional[str] = None  # if mutated/crossed from another
    generation: int = 1
    active: bool = True

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

    @property
    def usage_count(self) -> int:
        return len(self.trials)

    @property
    def success_count(self) -> int:
        return sum(1 for t in self.trials if t.success)

    @property
    def success_rate(self) -> float:
        if not self.trials:
            return 0.5  # prior belief
        return self.success_count / self.usage_count

    @property
    def fitness(self) -> float:
        """Fitness = success_rate × log(usage_count + 1)

        Balances exploitation (high success rate) with confidence
        (more trials = more reliable estimate).
        """
        return self.success_rate * math.log(self.usage_count + 1)

    @property
    def has_enough_trials(self) -> bool:
        return self.usage_count >= STRATEGY_MIN_TRIALS

    @property
    def should_prune(self) -> bool:
        return (
            self.has_enough_trials
            and self.success_rate < STRATEGY_PRUNE_THRESHOLD
        )


class StrategyEngine:
    """Self-evolving strategy management engine.

    Maintains a population of strategies per task type,
    selecting, evaluating, and evolving them over time.
    """

    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}  # id → strategy
        self._task_index: Dict[str, List[str]] = defaultdict(list)  # task_type → [ids]
        self.evolution_count: int = 0

    def add_strategy(
        self,
        task_type: str,
        approach: str,
        prompt_template: str = "",
        parent_id: Optional[str] = None,
        generation: int = 1,
    ) -> Strategy:
        """Add a new strategy for a task type."""
        from cortex.core.integrity import strategy_id

        sid = strategy_id(task_type, approach)
        strategy = Strategy(
            strategy_id=sid,
            task_type=task_type,
            approach=approach,
            prompt_template=prompt_template,
            parent_id=parent_id,
            generation=generation,
        )

        self.strategies[sid] = strategy
        self._task_index[task_type].append(sid)

        # Enforce max per task
        self._enforce_limit(task_type)

        return strategy

    def select(self, task_type: str) -> Optional[Strategy]:
        """Select the best strategy for a task type.

        Uses fitness-based selection with exploration bonus for untried strategies.
        """
        candidates = self._get_active_for_task(task_type)
        if not candidates:
            return None

        # Exploration bonus for strategies with few trials
        def selection_score(s: Strategy) -> float:
            if s.usage_count < STRATEGY_MIN_TRIALS:
                return s.success_rate + 0.5  # explore untested
            return s.fitness

        return max(candidates, key=selection_score)

    def record_outcome(
        self,
        strategy_id: str,
        success: bool,
        context: str = "",
        notes: str = "",
    ) -> None:
        """Record the outcome of using a strategy."""
        strategy = self.strategies.get(strategy_id)
        if strategy:
            strategy.trials.append(StrategyRecord(
                success=success,
                context=context,
                notes=notes,
            ))

    def evolve(self, task_type: str) -> Dict[str, Any]:
        """Run one evolution cycle for a task type.

        Steps:
          1. PRUNE: Remove failed strategies
          2. MUTATE: Create variant of best strategy
          3. CROSSOVER: Combine top 2 strategies

        Returns dict with evolution results.
        """
        self.evolution_count += 1
        results = {"pruned": [], "mutated": None, "crossed": None}

        candidates = self._get_active_for_task(task_type)
        if not candidates:
            return results

        # 1. PRUNE
        for s in candidates:
            if s.should_prune:
                s.active = False
                results["pruned"].append(s.strategy_id)

        # Refresh candidates
        candidates = self._get_active_for_task(task_type)
        if not candidates:
            return results

        # Sort by fitness
        candidates.sort(key=lambda s: s.fitness, reverse=True)

        # 2. MUTATE best strategy
        if random.random() < STRATEGY_EVOLUTION_RATE and candidates:
            best = candidates[0]
            mutated = self._mutate(best)
            if mutated:
                results["mutated"] = mutated.strategy_id

        # 3. CROSSOVER top 2
        if random.random() < STRATEGY_CROSSOVER_RATE and len(candidates) >= 2:
            crossed = self._crossover(candidates[0], candidates[1])
            if crossed:
                results["crossed"] = crossed.strategy_id

        return results

    def _mutate(self, parent: Strategy) -> Optional[Strategy]:
        """Create a mutated variant of a strategy.

        Mutation: Appends variation instructions to the approach.
        """
        mutations = [
            "Be more concise.",
            "Include more examples.",
            "Think step by step.",
            "Consider edge cases first.",
            "Start with the most important point.",
            "Use analogies to explain.",
            "Break into smaller steps.",
            "Verify each assumption.",
        ]
        mutation = random.choice(mutations)
        new_approach = f"{parent.approach} [MUTATION: {mutation}]"

        return self.add_strategy(
            task_type=parent.task_type,
            approach=new_approach,
            prompt_template=parent.prompt_template,
            parent_id=parent.strategy_id,
            generation=parent.generation + 1,
        )

    def _crossover(self, parent_a: Strategy, parent_b: Strategy) -> Optional[Strategy]:
        """Combine elements of two strategies."""
        new_approach = (
            f"[CROSS] Combine: ({parent_a.approach[:100]}) + "
            f"({parent_b.approach[:100]})"
        )
        return self.add_strategy(
            task_type=parent_a.task_type,
            approach=new_approach,
            parent_id=parent_a.strategy_id,
            generation=max(parent_a.generation, parent_b.generation) + 1,
        )

    def _get_active_for_task(self, task_type: str) -> List[Strategy]:
        """Get active strategies for a task type."""
        ids = self._task_index.get(task_type, [])
        return [
            self.strategies[sid] for sid in ids
            if sid in self.strategies and self.strategies[sid].active
        ]

    def _enforce_limit(self, task_type: str) -> None:
        """Ensure we don't exceed max strategies per task."""
        active = self._get_active_for_task(task_type)
        if len(active) > STRATEGY_MAX_PER_TASK:
            # Deactivate lowest-fitness strategies
            active.sort(key=lambda s: s.fitness)
            for s in active[:len(active) - STRATEGY_MAX_PER_TASK]:
                s.active = False

    @property
    def total_strategies(self) -> int:
        return len(self.strategies)

    @property
    def active_strategies(self) -> int:
        return sum(1 for s in self.strategies.values() if s.active)

    @property
    def avg_fitness(self) -> float:
        """Average fitness across all active strategies."""
        active = [s for s in self.strategies.values() if s.active]
        if not active:
            return 0.0
        return sum(s.fitness for s in active) / len(active)

    @property
    def strategy_score(self) -> float:
        """Score for METACOG-X: average success rate of active strategies."""
        active = [s for s in self.strategies.values() if s.active and s.has_enough_trials]
        if not active:
            return 0.5  # prior
        return sum(s.success_rate for s in active) / len(active)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_strategies": self.total_strategies,
            "active_strategies": self.active_strategies,
            "avg_fitness": round(self.avg_fitness, 4),
            "strategy_score": round(self.strategy_score, 4),
            "evolution_count": self.evolution_count,
            "strategies": {
                sid: {
                    "task_type": s.task_type,
                    "approach": s.approach[:200],
                    "success_rate": round(s.success_rate, 2),
                    "usage_count": s.usage_count,
                    "fitness": round(s.fitness, 4),
                    "generation": s.generation,
                    "active": s.active,
                }
                for sid, s in self.strategies.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyEngine":
        engine = cls()
        engine.evolution_count = data.get("evolution_count", 0)
        return engine
