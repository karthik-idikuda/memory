"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — CAULANG-Ω Symbol Definitions             ║
║  All symbols for the causal reasoning language             ║
╚══════════════════════════════════════════════════════════╝
"""

from sigmax.config import (
    CAULANG_CHAIN_SYMBOLS,
    CAULANG_ZONE_SYMBOLS,
    CAULANG_CONFIDENCE_SYMBOLS,
    CAULANG_ACTION_SYMBOLS,
    CAULANG_EVIDENCE_SYMBOLS,
    CAULANG_PREDICTION_SYMBOLS,
    CAULANG_EXISTENCE_SYMBOLS,
    CAULANG_GRAPH_SYMBOLS,
)

# Re-export all symbol tables for convenience
CHAIN_SYMBOLS = CAULANG_CHAIN_SYMBOLS
ZONE_SYMBOLS = CAULANG_ZONE_SYMBOLS
CONFIDENCE_SYMBOLS = CAULANG_CONFIDENCE_SYMBOLS
ACTION_SYMBOLS = CAULANG_ACTION_SYMBOLS
EVIDENCE_SYMBOLS = CAULANG_EVIDENCE_SYMBOLS
PREDICTION_SYMBOLS = CAULANG_PREDICTION_SYMBOLS
EXISTENCE_SYMBOLS = CAULANG_EXISTENCE_SYMBOLS
GRAPH_SYMBOLS = CAULANG_GRAPH_SYMBOLS

# Complete symbol table
ALL_SYMBOLS = {}
ALL_SYMBOLS.update({f"CHAIN_{k}": v for k, v in CHAIN_SYMBOLS.items()})
ALL_SYMBOLS.update({f"ZONE_{k}": v for k, v in ZONE_SYMBOLS.items()})
ALL_SYMBOLS.update({f"CONF_{k}": v for k, v in CONFIDENCE_SYMBOLS.items()})
ALL_SYMBOLS.update({f"ACT_{k}": v for k, v in ACTION_SYMBOLS.items()})
ALL_SYMBOLS.update({f"EV_{k}": v for k, v in EVIDENCE_SYMBOLS.items()})
ALL_SYMBOLS.update({f"PRED_{k}": v for k, v in PREDICTION_SYMBOLS.items()})
ALL_SYMBOLS.update({f"EXIST_{k}": v for k, v in EXISTENCE_SYMBOLS.items()})
ALL_SYMBOLS.update({f"GRAPH_{k}": v for k, v in GRAPH_SYMBOLS.items()})

# Reverse lookup: symbol → name
SYMBOL_TO_NAME = {v: k for k, v in ALL_SYMBOLS.items()}


def get_symbol(category: str, name: str) -> str:
    """Get a symbol by category and name."""
    tables = {
        'chain': CHAIN_SYMBOLS,
        'zone': ZONE_SYMBOLS,
        'confidence': CONFIDENCE_SYMBOLS,
        'action': ACTION_SYMBOLS,
        'evidence': EVIDENCE_SYMBOLS,
        'prediction': PREDICTION_SYMBOLS,
        'existence': EXISTENCE_SYMBOLS,
        'graph': GRAPH_SYMBOLS,
    }
    table = tables.get(category.lower())
    if table:
        return table.get(name.upper(), "?")
    return "?"


def lookup_symbol(symbol: str) -> str:
    """Reverse-lookup: find the name for a symbol."""
    return SYMBOL_TO_NAME.get(symbol, "UNKNOWN")
