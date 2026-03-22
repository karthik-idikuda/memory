"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Central Configuration                  ║
║  NRNLANG-Ω: CORTEX CONFIG — source of all truth         ║
╚══════════════════════════════════════════════════════════╝

Every tunable parameter lives here. No magic numbers scattered
in code. Change a value here → it changes everywhere.
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOMA-DB BINARY FORMAT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOMA_MAGIC = b'\x4E\x52\x4E\xCE'   # NRN + 0xCE — unique to NEURON-X
SOMA_VERSION = 0x0001
SOMA_HEADER_FORMAT = '>4sHIIIIIIddd8sI4sH'  # 72 bytes (struct-aligned)
SOMA_AXON_FORMAT = '>16s16sfdb'              # 45 bytes per axon
SOMA_SEAL_FORMAT = '>32sdQ16s'               # 64 bytes total
SOMA_HEADER_SIZE = 72
SOMA_SEAL_SIZE = 64
SOMA_AXON_SIZE = 45

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SURPRISE ENGINE THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

SURPRISE_ECHO_THRESHOLD = 0.25
SURPRISE_CLASH_THRESHOLD = 0.85
CLASH_JACCARD_GATE = 0.15

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BOND ENGINE THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

BOND_PRUNE_THRESHOLD = 0.05
BOND_REINFORCE_AMOUNT = 0.05
BOND_TIME_WINDOW = 180
BOND_TIME_MAX = 0.30
BOND_WORD_MIN_SHARED = 3
BOND_WORD_MAX = 0.50
BOND_EMOTION_VALUE = 0.10
MAX_SYNAPSE = 1.0
HERALD_DECAY_FACTOR = 0.5

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THERMAL ZONE THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

HEAT_HOT_THRESHOLD = 0.70
HEAT_WARM_THRESHOLD = 0.30
HEAT_COLD_THRESHOLD = 0.05
SILENCE_AGE_DAYS = 90
FOSSIL_AGE_DAYS = 180

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANCHOR THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANCHOR_CONFIDENCE_THRESHOLD = 0.95
ANCHOR_ACCESS_THRESHOLD = 20

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REAWAKENING THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

REAWAKEN_HOT_THRESHOLD = 0.80
REAWAKEN_WARM_THRESHOLD = 0.50

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENGRAM WEIGHT LIMITS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

MAX_WEIGHT = 3.0
MIN_WEIGHT = 0.1
STRENGTHEN_AMOUNT = 0.15

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WSRA-X RETRIEVAL WEIGHTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

WSRAX_WORD_RESONANCE = 2.5
WSRAX_ZONE_HEAT = 2.0
WSRAX_SPARK_LEGACY = 1.8
WSRAX_RECENCY_CURVE = 1.5
WSRAX_BOND_CENTRALITY = 1.2
WSRAX_CONFIDENCE = 1.0
WSRAX_DECAY_DEBT = 1.3
WSRAX_CLASH_PENALTY = 0.8

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM OPERATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

AUDIT_INTERVAL = 100
DEFAULT_TOP_K = 7
AUTO_SAVE_INTERVAL = 5
DEFAULT_PAGE_SIZE = 50
MAX_INPUT_CHARS_BEFORE_CHUNK = 500
STALE_LOCK_SECONDS = 30
LOCK_WAIT_SECONDS = 5
LOCK_POLL_INTERVAL_MS = 100

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONTRADICTION ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUPERSEDE_MARGIN = 1.10
CONFIDENCE_CLASH_HIT = 0.10
CONFIDENCE_SUPERSEDE_HIT = 0.30

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECAY RATES (immutable)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

DECAY_RATES = {
    "emotion":  0.010000,   # half-life ≈ 69.3 days
    "opinion":  0.005000,   # half-life ≈ 138.6 days
    "event":    0.003000,   # half-life ≈ 231.0 days
    "fact":     0.001000,   # half-life ≈ 693.1 days
    "identity": 0.000100,   # half-life ≈ 6931 days
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ZONE CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

ZONE_HOT = "HOT"
ZONE_WARM = "WARM"
ZONE_COLD = "COLD"
ZONE_SILENT = "SILENT"

ZONE_HEAT_VALUES = {
    ZONE_HOT: 1.0,
    ZONE_WARM: 0.6,
    ZONE_COLD: 0.2,
    ZONE_SILENT: 0.0,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRUTH STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

TRUTH_ACTIVE = "active"
TRUTH_EXPIRED = "expired"
TRUTH_CONTESTED = "contested"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EMOTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

EMOTIONS = ("neutral", "happy", "sad", "curious", "excited", "angry", "love", "fear")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECAY CLASSES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

DECAY_CLASSES = ("fact", "opinion", "emotion", "event", "identity")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOURCES = ("user", "inference", "import")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STOP WORDS (exact, immutable)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

STOP_WORDS = frozenset({
    'the', 'and', 'but', 'for', 'are', 'was', 'were', 'been', 'have',
    'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might',
    'shall', 'that', 'this', 'with', 'from', 'they', 'them', 'their',
    'what', 'when', 'where', 'which', 'who', 'how', 'its', 'our', 'your',
    'his', 'her', 'not', 'into', 'onto', 'upon', 'over', 'under', 'about',
    'above', 'below', 'you', 'can', 'did', 'does', 'just', 'also', 'then',
    'than', 'more', 'some', 'any', 'all', 'both', 'each', 'few', 'most',
    'other', 'such', 'own', 'same', 'too', 'very', 'now', 'here', 'there',
    'out', 'off', 'why', 'let', 'get', 'got', 'set', 'put', 'use', 'used',
    'via', 'per', 'yet', 'nor', 'its', 'she', 'him', 'her', 'who', 'whom',
})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NRNLANG-Ω SYMBOLS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

NRNLANG_ZONE_SYMBOLS = {
    "HOT":    "🔥 [H]",
    "WARM":   "🌡 [W]",
    "COLD":   "❄  [C]",
    "SILENT": "👻 [S]",
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

NRNLANG_ACTION_SYMBOLS = {
    "FORGE":     "⊕",
    "ECHO":      "●",
    "CLASH":     "##",
    "SUPERSEDE": "!!=",
    "CONTESTED": "|?|",
    "REAWAKEN":  "^^",
    "WEAVE":     ":::",
    "PRUNE":     "-x-",
    "TEMPER":    "~~",
    "CRYSTALLIZE": "◆",
    "AUDIT":     "🔍",
    "NMP_WRITE": ">>",
}

NRNLANG_EXISTENCE_SYMBOLS = {
    "BORN":    "╔══╗",
    "DIED":    "╚══╝",
    "LIVE":    "◈",
    "SLEEP":   "◇",
    "ANCHOR":  "◆",
    "GHOST":   "○",
    "ECHO":    "●",
    "FORGE":   "⊕",
    "EXPIRE":  "⊖",
}

NRNLANG_TRUTH_SYMBOLS = {
    "active":    "|-",
    "expired":   "-|",
    "contested": "|?|",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AXON TYPES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

AXON_TYPE_TIME = 0
AXON_TYPE_WORD = 1
AXON_TYPE_EMOTION = 2
AXON_TYPE_CLASH = 3
AXON_TYPE_HERALD = 4

AXON_TYPE_NAMES = {
    0: "TIME",
    1: "WORD",
    2: "EMOTION",
    3: "CLASH",
    4: "HERALD",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RATE LIMITING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

RATE_LIMIT_REQUESTS_PER_MINUTE = 60

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM PROMPTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROMPT_SYSTEM = """You are an AI assistant powered by NEURON-X OMEGA permanent memory.
Retrieved memories ({count} total, WSRA-X ranked):
{memory_context}
Rules: reference memories naturally, verify old memories (age>365d),
never pretend to forget, surface conflicts when present,
tentative language for confidence < 0.5."""

PROMPT_EXTRACT = """Extract each distinct storable memory from: "{message}"
Rules: split compounds, third person, ignore greetings/questions/filler.
Return JSON array: [{{"text": str, "decay_class": str, "emotion": str, "confidence": float, "tags": [str], "subject": str}}]"""

PROMPT_CONTRADICTION = """OLD: "{old}" (from {date}, conf:{conf})
NEW: "{new}"
Return JSON: {{"is_contradiction": bool, "newer_wins": bool, "confidence_in_decision": float, "reason": str}}"""

PROMPT_TAG = """Memory: "{text}"
Return JSON: {{"decay_class": str, "emotion": str, "tags": [str], "confidence": float, "subject": str, "is_time_sensitive": bool}}"""

PROMPT_CONSOLIDATE = """A (from {date_a}): "{text_a}"
B (from {date_b}): "{text_b}"
Similarity: {score}
Return JSON: {{"should_consolidate": bool, "consolidated_text": str, "keep_if_not": str, "reason": str}}"""

PROMPT_REAWAKEN = """DORMANT: "{text}" | Age: {days}d | Context: "{context}"
Return JSON: {{"should_reawaken": bool, "relevance": float, "how_to_reference": str}}"""

PROMPT_BRAIN_SUMMARY = """Stats: {stats} | Top memories: {top_memories}
Write 3 sentences: what brain knows most about, health status, patterns noticed.
Use actual memory content. Sound like a doctor. Not a robot."""
