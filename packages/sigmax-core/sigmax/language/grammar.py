"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — CAULANG-Ω Grammar & Emitter              ║
║  Validates and emits CAULANG-Ω notation                    ║
╚══════════════════════════════════════════════════════════╝

Grammar Rules:
1. Chain notation: "cause" ~>~ "effect"
2. Zone prefix: ⚡ [A] or 🌡 [W] etc.
3. Confidence suffix: (?) (~) (!) (◆)
4. Evidence block: [+N/-M]
5. Session flow: SESSION_BEGIN ... SESSION_END
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from sigmax.core.causenode import CauseNode
from sigmax.language.symbols import (
    CHAIN_SYMBOLS, ZONE_SYMBOLS, CONFIDENCE_SYMBOLS,
    ACTION_SYMBOLS, EVIDENCE_SYMBOLS, PREDICTION_SYMBOLS,
)
from sigmax.language.keywords import ALL_KEYWORDS, is_keyword
from sigmax.exceptions import CaulangSyntaxError


# Grammar validation patterns
_CHAIN_PATTERN = re.compile(
    r'"([^"]+)"\s*(~[>|?t!<]+~)\s*"([^"]+)"'
)
_EVIDENCE_PATTERN = re.compile(r'\[([+-]\d+)/([+-]\d+)\]')
_CONFIDENCE_PATTERN = re.compile(r'\(([?~!◆])\)')
_SESSION_PATTERN = re.compile(r'SESSION_(BEGIN|END)\s*(.*)')
_ZONE_PREFIX = re.compile(r'^[⚡🌡💤◆📦]\s*\[[AWDXR]\]')

# Valid chain operators
VALID_OPERATORS = set(CHAIN_SYMBOLS.values())


def validate_chain_notation(notation: str) -> Tuple[bool, str]:
    """Validate CAULANG-Ω chain notation. Returns (valid, error_message)."""
    if not notation or not isinstance(notation, str):
        return False, "Empty notation"

    # Check for chain operator
    match = _CHAIN_PATTERN.search(notation)
    if not match:
        return False, "Missing chain operator (e.g., ~>~)"

    cause = match.group(1)
    operator = match.group(2)
    effect = match.group(3)

    if not cause:
        return False, "Empty cause text"
    if not effect:
        return False, "Empty effect text"
    if operator not in VALID_OPERATORS:
        return False, f"Unknown operator: {operator}"

    return True, ""


def validate_session(lines: List[str]) -> Tuple[bool, List[str]]:
    """Validate a CAULANG-Ω session block."""
    errors = []
    has_begin = False
    has_end = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("SESSION_BEGIN"):
            if has_begin:
                errors.append(f"Line {i+1}: Duplicate SESSION_BEGIN")
            has_begin = True

        elif stripped.startswith("SESSION_END"):
            if not has_begin:
                errors.append(f"Line {i+1}: SESSION_END without SESSION_BEGIN")
            has_end = True

        elif has_begin and not has_end:
            # Inside session — validate each line
            if _CHAIN_PATTERN.search(stripped):
                valid, err = validate_chain_notation(stripped)
                if not valid:
                    errors.append(f"Line {i+1}: {err}")

    if has_begin and not has_end:
        errors.append("Missing SESSION_END")

    return len(errors) == 0, errors


class CaulangEmitter:
    """Emits CAULANG-Ω notation from operations and nodes."""

    def emit_chain(self, node: CauseNode) -> str:
        """Emit chain notation for a single node."""
        return node.to_caulang()

    def emit_action(self, action: str, node: CauseNode, detail: str = "") -> str:
        """Emit an action notation."""
        symbol = ACTION_SYMBOLS.get(action, "??")
        base = f'{symbol} {node.to_caulang()}'
        if detail:
            base += f' — {detail}'
        return base

    def emit_session(
        self,
        session_name: str,
        nodes: List[CauseNode],
        scores: Optional[List[float]] = None,
    ) -> str:
        """Emit a complete session block."""
        lines = [f"SESSION_BEGIN {session_name}"]
        for i, node in enumerate(nodes):
            line = f"  {node.to_caulang()}"
            if scores and i < len(scores):
                line += f" [σ={scores[i]:.3f}]"
            lines.append(line)
        lines.append("SESSION_END")
        return "\n".join(lines)

    def emit_evidence(self, is_support: bool, text: str, conf: float) -> str:
        """Emit evidence notation."""
        sym = EVIDENCE_SYMBOLS.get("SUPPORT" if is_support else "CONTRADICT")
        return f'{sym} "{text}" (conf={conf:.2f})'

    def emit_prediction(self, status: str, text: str, conf: float) -> str:
        """Emit prediction notation."""
        sym = PREDICTION_SYMBOLS.get(status, "→?")
        return f'{sym} "{text}" (conf={conf:.2f})'

    def emit_multihop(self, nodes: List[CauseNode]) -> str:
        """Emit multi-hop path notation."""
        if not nodes:
            return ""
        parts = [f'>>> "{nodes[0].cause}"']
        for node in nodes:
            parts.append(f'~>~ "{node.effect}"')
        min_conf = min(n.confidence for n in nodes)
        parts.append(f'(hops={len(nodes)}, conf={min_conf:.2f})')
        return " ".join(parts)

    def emit_crystallization(self, node: CauseNode) -> str:
        """Emit axiom crystallization notation."""
        return f'◆◆ CRYSTALLIZE {node.to_caulang()} — PERMANENT TRUTH'

    def emit_brain_summary(self, stats: dict) -> str:
        """Emit brain statistics in CAULANG-Ω."""
        lines = [
            "╔══ SIGMA-X BRAIN STATUS ══╗",
            f"  Chains:       {stats.get('node_count', 0)}",
            f"  Axioms:       {stats.get('axiom_count', 0)}",
            f"  Predictions:  {stats.get('predictions', {}).get('total', 0)}",
            f"  Evidence:     {stats.get('evidence', 0)}",
            f"  Operations:   {stats.get('operation_count', 0)}",
            "╚══════════════════════════╝",
        ]
        return "\n".join(lines)
