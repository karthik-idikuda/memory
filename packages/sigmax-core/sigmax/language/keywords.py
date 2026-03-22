"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — CAULANG-Ω Keywords                       ║
║  All reserved keywords for the causal language              ║
╚══════════════════════════════════════════════════════════╝
"""

from sigmax.config import CAULANG_KEYWORDS

# Keyword categories
KEYWORDS_CORE = frozenset({
    'CAUSENODE', 'CHAIN', 'SIGMA', 'CAUSADB', 'BRAIN',
})

KEYWORDS_OPERATIONS = frozenset({
    'FORGE_CHAIN', 'ECHO_CHAIN', 'CRYSTALLIZE', 'ARCHIVE',
    'PRUNE', 'REACTIVATE',
})

KEYWORDS_REASONING = frozenset({
    'THINK', 'REASON', 'CONCLUDE', 'PREDICT', 'VERIFY',
    'FALSIFY', 'COUNTERFACT', 'MULTIHOP', 'BRIDGE',
})

KEYWORDS_EVIDENCE = frozenset({
    'EVIDENCE', 'SUPPORT', 'CONTRADICT',
})

KEYWORDS_STATE = frozenset({
    'AXIOM', 'ZONE', 'HEAT', 'DECAY', 'PULSE_C',
})

KEYWORDS_SESSION = frozenset({
    'SESSION_BEGIN', 'SESSION_END',
})

KEYWORDS_GRAPH = frozenset({
    'GRAPH', 'PATH', 'CYCLE', 'HUB',
})

# All keywords combined
ALL_KEYWORDS = CAULANG_KEYWORDS


def is_keyword(word: str) -> bool:
    """Check if a word is a CAULANG-Ω keyword."""
    return word.upper() in ALL_KEYWORDS


def get_category(keyword: str) -> str:
    """Get the category of a keyword."""
    kw = keyword.upper()
    if kw in KEYWORDS_CORE:
        return "core"
    if kw in KEYWORDS_OPERATIONS:
        return "operations"
    if kw in KEYWORDS_REASONING:
        return "reasoning"
    if kw in KEYWORDS_EVIDENCE:
        return "evidence"
    if kw in KEYWORDS_STATE:
        return "state"
    if kw in KEYWORDS_SESSION:
        return "session"
    if kw in KEYWORDS_GRAPH:
        return "graph"
    return "unknown"
