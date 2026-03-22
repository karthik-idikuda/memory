"""CORTEX-X — CORTEXLANG-Ω Parser (Notation → Operations)."""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from cortex.language.symbols import SYMBOL_REVERSE, ALL_SYMBOLS
from cortex.language.keywords import KEYWORD_CATEGORY, ALL_KEYWORDS_SET
from cortex.language.grammar import validate_notation, parse_command
from cortex.exceptions import CortexLangParseError


@dataclass
class ParsedThought:
    """Parsed thought from CORTEXLANG notation."""
    thought_type: str = ""
    zone: str = ""
    confidence_level: str = ""
    shield_level: str = ""
    content: str = ""
    raw: str = ""


@dataclass
class ParsedCommand:
    """Parsed command from CORTEXLANG notation."""
    keyword: str = ""
    category: str = ""
    args: List[str] = field(default_factory=list)
    raw: str = ""


def parse_thought_notation(notation: str) -> ParsedThought:
    """Parse a thought notation string back into components.

    Input: ◎ ⚡ ⊕⊕ 🛡✓ "How to sort a list"
    Output: ParsedThought(type=RESPONSE, zone=FOCUSED, conf=HIGH, shield=SAFE, ...)
    """
    errors = validate_notation(notation)
    if errors:
        raise CortexLangParseError(f"Invalid notation: {'; '.join(errors)}")

    parsed = ParsedThought(raw=notation)
    tokens = notation.strip().split()
    i = 0

    while i < len(tokens):
        token = tokens[i]

        # Check if it's a symbol
        name = SYMBOL_REVERSE.get(token)
        if name:
            # Categorize by name pattern
            if name in ("RESPONSE", "REFLECTION", "CORRECTION", "PREDICTION",
                       "STRATEGY", "WISDOM", "OBSERVATION", "ERROR"):
                parsed.thought_type = name
            elif name.startswith("CONFIDENCE"):
                parsed.confidence_level = name
            elif name.startswith("HALLUCINATION"):
                parsed.shield_level = name
            elif name in (SYMBOL_REVERSE.get(v, "") for v in
                         ["⚡", "🔍", "⚠", "📖", "🪞"]):
                parsed.zone = name
            # Check zone symbols explicitly
            for zone_name, zone_sym in ALL_SYMBOLS.items():
                if token == zone_sym and zone_name in (
                    "FOCUSED", "EXPLORING", "CAUTIOUS", "LEARNING", "REFLECTING"
                ):
                    parsed.zone = zone_name
                    break

        # Check for quoted content
        if token.startswith('"'):
            # Collect until closing quote
            content_parts = [token.lstrip('"')]
            while i + 1 < len(tokens) and not tokens[i].endswith('"'):
                i += 1
                content_parts.append(tokens[i])
            content = " ".join(content_parts).rstrip('"')
            parsed.content = content

        i += 1

    return parsed


def parse_cortexlang(text: str) -> List[Any]:
    """Parse any CORTEXLANG text into a list of operations.

    Handles both thought notations and commands.
    """
    results = []
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Try as command first
        if re.match(r'^[A-Z_]+\s*\(', line):
            try:
                keyword, args = parse_command(line)
                results.append(ParsedCommand(
                    keyword=keyword,
                    category=KEYWORD_CATEGORY.get(keyword, "unknown"),
                    args=args,
                    raw=line,
                ))
                continue
            except Exception:
                pass

        # Try as thought notation
        try:
            parsed = parse_thought_notation(line)
            results.append(parsed)
        except CortexLangParseError:
            pass  # Skip unparseable lines

    return results
