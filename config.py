"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Central Configuration                  ║
║  All thresholds and constants in one place                ║
╚══════════════════════════════════════════════════════════╝

Every tunable parameter lives here. No magic numbers scattered
in code. Change a value here → it changes everywhere.
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SURPRISE ENGINE THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

SURPRISE_ECHO_THRESHOLD = 0.25     # Below this → ECHO (reinforce existing)
SURPRISE_CLASH_THRESHOLD = 0.85    # Above this → potential CLASH
CLASH_JACCARD_GATE = 0.15          # Min similarity to allow CLASH routing

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BOND ENGINE THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

BOND_PRUNE_THRESHOLD = 0.05        # Remove axons weaker than this
BOND_REINFORCE_AMOUNT = 0.05       # Synapse boost per co-retrieval
BOND_TIME_WINDOW = 180             # Seconds within which TIME_BOND forms
BOND_TIME_MAX = 0.30               # Max TIME_BOND strength
BOND_WORD_MIN_SHARED = 3           # Min shared tokens for WORD_BOND
BOND_WORD_MAX = 0.50               # Max WORD_BOND strength
BOND_EMOTION_VALUE = 0.10          # EMOTION_BOND value when emotions match
MAX_SYNAPSE = 1.0                  # Synapse strength cap

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THERMAL ZONE THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

HEAT_HOT_THRESHOLD = 0.70          # heat >= this → HOT
HEAT_WARM_THRESHOLD = 0.30         # heat >= this → WARM
HEAT_COLD_THRESHOLD = 0.05         # heat >= this → COLD
SILENCE_AGE_DAYS = 90              # heat < COLD + age > this → SILENT
FOSSIL_AGE_DAYS = 180              # Mark as fossil after this many days in COLD

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANCHOR THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANCHOR_CONFIDENCE_THRESHOLD = 0.95  # Confidence required for crystallization
ANCHOR_ACCESS_THRESHOLD = 20        # Access count required for crystallization

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REAWAKENING THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

REAWAKEN_HOT_THRESHOLD = 0.80      # Score above this → reawaken to HOT
REAWAKEN_WARM_THRESHOLD = 0.50     # Score above this → reawaken to WARM

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENGRAM WEIGHT LIMITS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

MAX_WEIGHT = 3.0                    # Maximum engram weight
MIN_WEIGHT = 0.1                    # Minimum engram weight
STRENGTHEN_AMOUNT = 0.15            # Default weight boost on ECHO

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WSRA-X RETRIEVAL WEIGHTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

WSRAX_WORD_RESONANCE = 2.5         # Direct content relevance — most important
WSRAX_ZONE_HEAT = 2.0              # Hot memories are hot for a reason
WSRAX_SPARK_LEGACY = 1.8           # Surprising memories stay important
WSRAX_RECENCY_CURVE = 1.5          # Recent memories matter
WSRAX_BOND_CENTRALITY = 1.2       # Connected = important
WSRAX_CONFIDENCE = 1.0             # Trust level
WSRAX_DECAY_DEBT = 1.3             # Penalty for old unused memories
WSRAX_CLASH_PENALTY = 0.8          # Softer penalty — conflicted ≠ worthless

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM OPERATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

AUDIT_INTERVAL = 100                # Run thermal audit every N interactions
DEFAULT_TOP_K = 7                   # Default number of memories to retrieve
AUTO_SAVE_INTERVAL = 5              # Auto-save every N interactions

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECAY RATES (do NOT change)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# These are mathematically derived from Ebbinghaus forgetting curve.

DECAY_RATES = {
    "emotion":  0.010,   # half-life ≈ 69 days
    "opinion":  0.005,   # half-life ≈ 139 days
    "event":    0.003,   # half-life ≈ 231 days
    "fact":     0.001,   # half-life ≈ 693 days
    "identity": 0.0001,  # half-life ≈ 6931 days (~19 years)
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONTRADICTION ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUPERSEDE_MARGIN = 1.10             # New must exceed old×margin to supersede
CONFIDENCE_CLASH_HIT = 0.10         # Confidence reduction in CONTESTED
CONFIDENCE_SUPERSEDE_HIT = 0.30     # Confidence reduction when superseded

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NRNLANG-Ω SYMBOL MAPS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

NRNLANG_ZONE_SYMBOLS = {
    "H": "🔥 [H]",
    "W": "🌡 [W]",
    "C": "❄  [C]",
    "S": "👻 [S]",
    "A": "◆  [A]",
    "G": "○  [G]",
    "F": "🪨 [F]",
}

NRNLANG_EMOTION_SYMBOLS = {
    "happy":   ":+:",
    "sad":     ":-:",
    "excited": ":!:",
    "curious": ":?:",
    "angry":   ":x:",
    "neutral": ":~:",
    "love":    ":*:",
    "fear":    ":/:",
}

NRNLANG_TRUTH_SYMBOLS = {
    "ACTIVE":    "◈ |-",
    "EXPIRED":   "◇ -|",
    "MAYBE":     "○ |?|",
    "CONFLICT":  "● |!|",
    "ANCHOR":    "◆ [A]",
}

