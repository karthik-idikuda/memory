"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Context Injector                         ║
║  CAULANG-Ω: INJECT — feed reasoning to the AI             ║
╚══════════════════════════════════════════════════════════╝

Formats retrieved causal chains into context strings
for injection into LLM system prompts.
"""

from __future__ import annotations

from typing import List, Tuple

from sigmax.config import PROMPT_SYSTEM
from sigmax.core.causenode import CauseNode


class ContextInjector:
    """
    Formats causal chains for AI prompt injection.

    Takes ranked CauseNodes and formats them into context strings
    that can be injected into LLM system prompts.
    """

    def format_context(
        self,
        ranked_nodes: List[Tuple[CauseNode, float]],
        include_predictions: bool = True,
        include_evidence: bool = True,
        max_nodes: int = 7,
    ) -> str:
        """
        Format ranked CauseNodes into a context string.

        Args:
            ranked_nodes: List of (CauseNode, sigma_score) tuples
            include_predictions: Include prediction info
            include_evidence: Include evidence counts
            max_nodes: Maximum nodes to include

        Returns:
            Formatted context string for LLM injection.
        """
        if not ranked_nodes:
            return "No causal chains available."

        lines = []
        for i, (node, score) in enumerate(ranked_nodes[:max_nodes], 1):
            line = (
                f"[{i}] [{node.zone}] "
                f'"{node.cause}" → "{node.effect}" '
                f"(type={node.cause_type}, conf={node.confidence:.2f}, "
                f"score={score:.3f})"
            )

            extras = []
            if include_evidence and (node.evidence_for > 0 or node.evidence_against > 0):
                extras.append(f"evidence: +{node.evidence_for}/-{node.evidence_against}")

            if include_predictions and node.predictions_made > 0:
                extras.append(
                    f"predictions: {node.predictions_correct}/{node.predictions_made} "
                    f"({node.prediction_accuracy:.0%})"
                )

            if node.age_days > 0:
                extras.append(f"age: {node.age_days:.0f}d")

            if extras:
                line += f" | {', '.join(extras)}"

            lines.append(line)

        return "\n".join(lines)

    def build_system_prompt(
        self,
        ranked_nodes: List[Tuple[CauseNode, float]],
        max_nodes: int = 7,
    ) -> str:
        """
        Build a complete system prompt with causal context injected.
        """
        context = self.format_context(ranked_nodes, max_nodes=max_nodes)
        return PROMPT_SYSTEM.format(
            count=len(ranked_nodes),
            causal_context=context,
        )

    def format_chain_detail(self, node: CauseNode) -> str:
        """Format a single node with full detail."""
        lines = [
            f"═══ CAUSAL CHAIN ═══",
            f"Cause:      {node.cause}",
            f"Effect:     {node.effect}",
            f"Type:       {node.cause_type}",
            f"Confidence: {node.confidence:.2f} ({node.confidence_label})",
            f"Zone:       {node.zone}",
            f"Weight:     {node.weight:.2f}",
            f"Evidence:   +{node.evidence_for} / -{node.evidence_against} (net: {node.evidence_net:+d})",
            f"Predictions: {node.predictions_correct}/{node.predictions_made}",
            f"Age:        {node.age_days:.1f} days",
            f"Accesses:   {node.access_count}",
            f"Decay:      {node.decay_class} (rate={node.decay_rate})",
            f"CAULANG:    {node.to_caulang()}",
        ]
        if node.tags:
            lines.append(f"Tags:       {', '.join(node.tags)}")
        if node.subject:
            lines.append(f"Subject:    {node.subject}")
        if node.neuronx_link_id:
            lines.append(f"NEURON-X:   linked ({node.neuronx_link_id})")
        return "\n".join(lines)

    def format_caulang_session(
        self,
        ranked_nodes: List[Tuple[CauseNode, float]],
    ) -> str:
        """Format as a CAULANG-Ω session block."""
        lines = ["SESSION_BEGIN SIGMA_RETRIEVAL"]
        for node, score in ranked_nodes:
            lines.append(f"  {node.to_caulang()} [σ={score:.3f}]")
        lines.append("SESSION_END")
        return "\n".join(lines)
