"""CORTEX-X — CORTEXLANG-Ω Symbol Registry."""

from cortex.config import (
    CORTEXLANG_META_SYMBOLS, CORTEXLANG_THOUGHT_SYMBOLS,
    CORTEXLANG_ZONE_SYMBOLS, CORTEXLANG_LINK_SYMBOLS,
)

# Forward lookup: name → symbol
ALL_SYMBOLS = {
    **CORTEXLANG_META_SYMBOLS,
    **CORTEXLANG_THOUGHT_SYMBOLS,
    **CORTEXLANG_ZONE_SYMBOLS,
    **CORTEXLANG_LINK_SYMBOLS,
}

# Reverse lookup: symbol → name
SYMBOL_REVERSE = {v: k for k, v in ALL_SYMBOLS.items()}


def symbol(name: str) -> str:
    """Get symbol by name."""
    return ALL_SYMBOLS.get(name, "?")


def name_of(sym: str) -> str:
    """Get name from symbol."""
    return SYMBOL_REVERSE.get(sym, "UNKNOWN")


def is_valid_symbol(sym: str) -> bool:
    """Check if a string is a valid CORTEXLANG symbol."""
    return sym in SYMBOL_REVERSE
