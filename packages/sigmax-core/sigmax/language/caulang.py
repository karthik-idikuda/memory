"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — CAULANG-Ω Parser & Interpreter          ║
║  CAULANG-Ω: PARSER — read notation back into chains     ║
╚══════════════════════════════════════════════════════════╝

Parses CAULANG-Ω notation strings back into CauseNode objects.
Completes the round-trip: CauseNode → notation → CauseNode.

Grammar:
  [ZONE_SYM] "cause" CHAIN_SYM "effect" CONF_SYM [evidence] {predictions}
  Example: ⚡ [A] "rain" ~>~ "wet roads" (!) [+3/-1] {5/6 83%}
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from sigmax.config import (
    CAULANG_CHAIN_SYMBOLS,
    CAULANG_ZONE_SYMBOLS,
    CAULANG_CONFIDENCE_SYMBOLS,
    CAULANG_ACTION_SYMBOLS,
    CAULANG_KEYWORDS,
    ZONE_ACTIVE, ZONE_WARM, ZONE_DORMANT, ZONE_AXIOM, ZONE_ARCHIVED,
)
from sigmax.exceptions import CaulangParseError, CaulangValidationError


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REVERSE LOOKUP TABLES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

_CHAIN_SYM_TO_TYPE = {v: k.lower() for k, v in CAULANG_CHAIN_SYMBOLS.items()}
_ZONE_SYM_TO_NAME = {v: k for k, v in CAULANG_ZONE_SYMBOLS.items()}
_CONF_SYM_TO_LABEL = {v: k for k, v in CAULANG_CONFIDENCE_SYMBOLS.items()}

# All chain symbols sorted by length (longest first for greedy match)
_ALL_CHAIN_SYMS = sorted(CAULANG_CHAIN_SYMBOLS.values(), key=len, reverse=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PARSED TOKEN TYPES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ParsedChain:
    """Result of parsing a CAULANG-Ω chain notation."""
    cause: str = ""
    effect: str = ""
    cause_type: str = "direct"
    zone: str = ZONE_ACTIVE
    confidence_label: str = "moderate"
    evidence_for: int = 0
    evidence_against: int = 0
    predictions_correct: int = 0
    predictions_total: int = 0
    raw_notation: str = ""

    @property
    def confidence_estimate(self) -> float:
        """Estimate confidence from label."""
        estimates = {
            "speculative": 0.30,
            "moderate": 0.60,
            "strong": 0.80,
            "axiom": 0.95,
        }
        return estimates.get(self.confidence_label, 0.50)


@dataclass
class ParsedAction:
    """Result of parsing a CAULANG-Ω action line."""
    action: str = ""
    target: str = ""
    details: Dict = field(default_factory=dict)
    raw_notation: str = ""


@dataclass
class ParsedSession:
    """Result of parsing a CAULANG-Ω session block."""
    chains: List[ParsedChain] = field(default_factory=list)
    actions: List[ParsedAction] = field(default_factory=list)
    raw_lines: List[str] = field(default_factory=list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CHAIN PARSER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Pattern: optional zone symbol, "cause" chain_sym "effect" optional_conf optional_evidence optional_predictions
_CHAIN_PATTERN = re.compile(
    r'(?P<zone_sym>.*?)?'              # optional zone indicator
    r'"(?P<cause>[^"]+)"'              # "cause"
    r'\s*(?P<chain_sym>[~\-\|?t><!=]+)\s*'  # chain symbol (~>~, ~>>~, etc.)
    r'"(?P<effect>[^"]+)"'             # "effect"
    r'(?:\s*(?P<conf_sym>\([^)]+\)))?'  # optional (!) or (~) or (?)
    r'(?:\s*\[(?P<evidence>[^\]]+)\])?' # optional [+3/-1]
    r'(?:\s*\{(?P<predictions>[^}]+)\})?'  # optional {5/6 83%}
)

_EVIDENCE_PATTERN = re.compile(r'\+(\d+)/\-(\d+)')
_PREDICTION_PATTERN = re.compile(r'(\d+)/(\d+)')


def parse_chain(notation: str) -> ParsedChain:
    """
    Parse a CAULANG-Ω chain notation string into a ParsedChain.

    Examples:
        '⚡ [A] "rain" ~>~ "wet roads" (!)'
        '"study" ~>~ "good grades" (~) [+5/-2] {3/4 75%}'

    Raises:
        CaulangParseError: If notation cannot be parsed
    """
    if not notation or not notation.strip():
        raise CaulangParseError("Empty notation string")

    match = _CHAIN_PATTERN.search(notation)
    if not match:
        raise CaulangParseError(f"Cannot parse chain notation: {notation!r}")

    result = ParsedChain(raw_notation=notation)

    # Extract cause and effect
    result.cause = match.group('cause')
    result.effect = match.group('effect')

    # Determine cause type from chain symbol
    chain_sym = match.group('chain_sym').strip()
    result.cause_type = _CHAIN_SYM_TO_TYPE.get(chain_sym, "direct")

    # Determine zone from prefix
    zone_sym = match.group('zone_sym') or ""
    zone_sym = zone_sym.strip()
    for sym, zname in _ZONE_SYM_TO_NAME.items():
        if sym in zone_sym:
            result.zone = zname
            break

    # Confidence symbol
    conf_sym = match.group('conf_sym')
    if conf_sym:
        result.confidence_label = _CONF_SYM_TO_LABEL.get(conf_sym, "moderate")

    # Evidence [+N/-M]
    evidence_str = match.group('evidence')
    if evidence_str:
        ev_match = _EVIDENCE_PATTERN.search(evidence_str)
        if ev_match:
            result.evidence_for = int(ev_match.group(1))
            result.evidence_against = int(ev_match.group(2))

    # Predictions {N/M P%}
    pred_str = match.group('predictions')
    if pred_str:
        pred_match = _PREDICTION_PATTERN.search(pred_str)
        if pred_match:
            result.predictions_correct = int(pred_match.group(1))
            result.predictions_total = int(pred_match.group(2))

    return result


def parse_chains(text: str) -> List[ParsedChain]:
    """
    Parse multiple chain notations from multi-line text.
    Each line is attempted as a chain notation; unparseable lines are skipped.
    """
    chains = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('//'):
            continue
        try:
            chain = parse_chain(line)
            chains.append(chain)
        except CaulangParseError:
            continue
    return chains


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ACTION PARSER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

_ACTION_PATTERN = re.compile(
    r'(?P<action_sym>[⊕●↑↓◆📦\^→~⇄🔍><\-]+[A-Z]?[⊕/]*)\s*'
    r'(?:"(?P<target>[^"]+)")?'
    r'(?:\s*(?P<rest>.*))?'
)


def parse_action(notation: str) -> ParsedAction:
    """
    Parse a CAULANG-Ω action notation.

    Examples:
        '⊕C "rain causes flooding"'
        '→✓ pred_12345'
        '↑↑ chain_abc'
    """
    if not notation or not notation.strip():
        raise CaulangParseError("Empty action notation")

    # Try to match action symbols
    for sym, action_name in CAULANG_ACTION_SYMBOLS.items():
        if notation.strip().startswith(action_name):
            rest = notation.strip()[len(action_name):].strip()
            target = ""
            # Extract quoted target
            target_match = re.search(r'"([^"]+)"', rest)
            if target_match:
                target = target_match.group(1)
            else:
                target = rest

            return ParsedAction(
                action=sym,
                target=target.strip(),
                raw_notation=notation,
            )

    raise CaulangParseError(f"Cannot parse action: {notation!r}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SESSION PARSER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def parse_session(text: str) -> ParsedSession:
    """
    Parse a full CAULANG-Ω session block.

    Session format:
        ╔══╗ SESSION_BEGIN
        [chain lines]
        [action lines]
        ╚══╝ SESSION_END

    Lines starting with ╔══╗ and ╚══╝ are session markers.
    """
    session = ParsedSession()
    in_session = False

    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        session.raw_lines.append(line)

        if '╔══╗' in line or 'SESSION_BEGIN' in line:
            in_session = True
            continue
        if '╚══╝' in line or 'SESSION_END' in line:
            in_session = False
            continue

        if not line or line.startswith('#'):
            continue

        # Try parsing as chain first
        try:
            chain = parse_chain(line)
            session.chains.append(chain)
            continue
        except CaulangParseError:
            pass

        # Try parsing as action
        try:
            action = parse_action(line)
            session.actions.append(action)
            continue
        except CaulangParseError:
            pass

    return session


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROUND-TRIP: ParsedChain → CauseNode
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def to_causenode(parsed: ParsedChain):
    """
    Convert a ParsedChain back into a CauseNode.
    Completes the full notation round-trip.
    """
    from sigmax.core.causenode import CauseNode
    return CauseNode(
        cause=parsed.cause,
        effect=parsed.effect,
        cause_type=parsed.cause_type,
        confidence=parsed.confidence_estimate,
        zone=parsed.zone,
        evidence_for=parsed.evidence_for,
        evidence_against=parsed.evidence_against,
        predictions_correct=parsed.predictions_correct,
        predictions_made=parsed.predictions_total,
    )


def notation_round_trip(notation: str):
    """
    Full round-trip: notation string → ParsedChain → CauseNode → notation string.
    Returns (CauseNode, new_notation).
    """
    parsed = parse_chain(notation)
    node = to_causenode(parsed)
    return node, node.to_caulang()
