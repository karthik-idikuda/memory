"""CORTEX-X — CORTEXLANG-Ω Grammar & Validator."""

from __future__ import annotations
import re
from typing import List, Tuple, Optional
from cortex.language.symbols import ALL_SYMBOLS, SYMBOL_REVERSE
from cortex.language.keywords import ALL_KEYWORDS_SET
from cortex.exceptions import CortexLangSyntaxError, CortexLangValidationError


# CORTEXLANG-Ω Notation Grammar:
#
# ThoughtNotation ::= TypeSymbol ZoneSymbol? ConfidenceSymbol ShieldSymbol Content
# Content ::= '"' <text> '"'
# Command ::= Keyword '(' Args? ')'
# Args ::= Arg (',' Arg)*
# Arg ::= <string> | <number> | Keyword


def validate_notation(notation: str) -> List[str]:
    """Validate a CORTEXLANG-Ω notation string.

    Returns list of errors (empty = valid).
    """
    errors = []
    if not notation or not notation.strip():
        errors.append("Empty notation")
        return errors

    parts = notation.strip().split()
    if not parts:
        errors.append("No tokens found")
        return errors

    # First token should be a valid symbol
    first = parts[0]
    if first not in SYMBOL_REVERSE:
        # Could be a keyword command
        if not any(kw in notation.upper() for kw in ALL_KEYWORDS_SET):
            errors.append(f"First token '{first}' is not a valid symbol or keyword")

    # Check for balanced quotes
    quote_count = notation.count('"')
    if quote_count % 2 != 0:
        errors.append("Unbalanced quotes in notation")

    # Check for balanced parentheses (for commands)
    paren_open = notation.count('(')
    paren_close = notation.count(')')
    if paren_open != paren_close:
        errors.append("Unbalanced parentheses in notation")

    return errors


def is_valid_notation(notation: str) -> bool:
    """Check if notation is valid."""
    return len(validate_notation(notation)) == 0


def validate_command(command: str) -> List[str]:
    """Validate a CORTEXLANG command string like 'METACOG_SCORE()'."""
    errors = []
    match = re.match(r'^([A-Z_]+)\s*\((.*)\)$', command.strip())
    if not match:
        errors.append(f"Invalid command syntax: {command}")
        return errors

    keyword = match.group(1)
    if keyword not in ALL_KEYWORDS_SET:
        errors.append(f"Unknown keyword: {keyword}")

    return errors


def parse_command(command: str) -> Tuple[str, List[str]]:
    """Parse a CORTEXLANG command into (keyword, args).

    Example: 'METACOG_SCORE()' → ('METACOG_SCORE', [])
    Example: 'WISDOM_SEARCH("python patterns")' → ('WISDOM_SEARCH', ['python patterns'])
    """
    match = re.match(r'^([A-Z_]+)\s*\((.*)\)$', command.strip())
    if not match:
        raise CortexLangSyntaxError(f"Invalid command: {command}")

    keyword = match.group(1)
    args_str = match.group(2).strip()

    if not args_str:
        return keyword, []

    # Parse args (handle quoted strings and plain values)
    args = []
    for arg in re.findall(r'"([^"]*)"|\b(\w+)\b', args_str):
        args.append(arg[0] or arg[1])

    return keyword, args
