"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Master Configuration                       ║
║  CORTEXLANG-Ω: CONFIG — every constant, formula, threshold  ║
╚══════════════════════════════════════════════════════════════╝

Single source of truth for the entire CORTEX-X ecosystem.
Every algorithm weight, every threshold, every symbol — defined here.
Nothing hardcoded anywhere else.
"""

from __future__ import annotations

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORTEX-DB BINARY FORMAT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORTEXDB_MAGIC = b'\x43\x54\x58\xCE'     # CTX + 0xCE
CORTEXDB_VERSION = 1
CORTEXDB_HEADER_FORMAT = '<4sHdIIIIIII32s'
# magic(4) + version(2) + timestamp(8) + thought_count(4) +
# edge_count(4) + strategy_count(4) + wisdom_count(4) +
# pattern_count(4) + session_count(4) + growth_entries(4) +
# reserved(32) = 70 bytes

import struct as _struct
CORTEXDB_HEADER_SIZE = _struct.calcsize(CORTEXDB_HEADER_FORMAT)

CORTEXDB_SEAL_FORMAT = '<32sdQ16s'   # sha256(32) + time(8) + count(8) + version(16) = 64
CORTEXDB_SEAL_SIZE = _struct.calcsize(CORTEXDB_SEAL_FORMAT)

# CMP (Cortex Memory Protocol) — safe write
STALE_LOCK_SECONDS = 30
LOCK_WAIT_SECONDS = 10
LOCK_POLL_INTERVAL_MS = 50

# Compression
COMPRESSION_LEVEL = 6
COMPRESSION_METHOD = "zlib"   # "zlib" or "lzma"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THOUGHT TYPES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

THOUGHT_RESPONSE = "response"
THOUGHT_REFLECTION = "reflection"
THOUGHT_CORRECTION = "correction"
THOUGHT_PREDICTION = "prediction"
THOUGHT_STRATEGY = "strategy"
THOUGHT_WISDOM = "wisdom"
THOUGHT_OBSERVATION = "observation"
THOUGHT_ERROR = "error"

ALL_THOUGHT_TYPES = [
    THOUGHT_RESPONSE, THOUGHT_REFLECTION, THOUGHT_CORRECTION,
    THOUGHT_PREDICTION, THOUGHT_STRATEGY, THOUGHT_WISDOM,
    THOUGHT_OBSERVATION, THOUGHT_ERROR,
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# METACOG-X ALGORITHM — 8 COMPONENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# METACOG-X = Σ(component_i × weight_i) / Σ(weight_i)
#
# Scores HOW WELL the AI is thinking (0.0 = blind, 1.0 = perfect self-awareness)
#

METACOG_CONFIDENCE_CALIBRATION = 3.0   # how accurate is self-assessed confidence
METACOG_CONTRADICTION_DENSITY  = 2.5   # contradictions per 100 thoughts (inverted)
METACOG_HALLUCINATION_RATE     = 2.8   # % responses with no evidence (inverted)
METACOG_DRIFT_VELOCITY         = 1.5   # accuracy change rate (inverted)
METACOG_PATTERN_DEPTH          = 2.0   # error patterns detected and resolved
METACOG_WISDOM_RATIO           = 1.8   # axioms / total_thoughts ratio
METACOG_STRATEGY_FITNESS       = 2.2   # avg success rate of active strategies
METACOG_GROWTH_RATE            = 1.2   # improvement slope over last N sessions

METACOG_TOTAL_WEIGHT = (
    METACOG_CONFIDENCE_CALIBRATION +
    METACOG_CONTRADICTION_DENSITY +
    METACOG_HALLUCINATION_RATE +
    METACOG_DRIFT_VELOCITY +
    METACOG_PATTERN_DEPTH +
    METACOG_WISDOM_RATIO +
    METACOG_STRATEGY_FITNESS +
    METACOG_GROWTH_RATE
)  # = 17.0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIDENCE CALIBRATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# CalibrationError = (1/N) × Σ(confidence_i - outcome_i)²
# Perfect = 0.0, Worst = 1.0

CONFIDENCE_WINDOW_SIZE = 50
CONFIDENCE_BUCKETS = 10
CONFIDENCE_DECAY_RATE = 0.02
CONFIDENCE_DEFAULT = 0.6

CONFIDENCE_LABELS = {
    "speculative": (0.0, 0.30),
    "uncertain":   (0.30, 0.50),
    "moderate":    (0.50, 0.70),
    "confident":   (0.70, 0.85),
    "certain":     (0.85, 1.0),
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HALLUCINATION SHIELD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# EvidenceRatio = evidence_count / total_claims
# HallucinationScore = 1.0 - EvidenceRatio

HALLUCINATION_EVIDENCE_THRESHOLD = 0.3
HALLUCINATION_MEMORY_SCAN_DEPTH = 50
HALLUCINATION_ALERT_LEVELS = {
    "safe":     (0.7, 1.0),
    "caution":  (0.4, 0.7),
    "warning":  (0.2, 0.4),
    "critical": (0.0, 0.2),
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DRIFT DETECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Dual-EWMA divergence algorithm
# drift_signal = |EWMA_recent - EWMA_historical|

DRIFT_EWMA_ALPHA = 0.15
DRIFT_THRESHOLD = 0.12
DRIFT_WINDOW_RECENT = 20
DRIFT_WINDOW_HISTORICAL = 200

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PATTERN RECOGNITION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# PatternStrength = frequency × recency_factor × severity_weight
# recency_factor = exp(-decay × days_since_last)

PATTERN_MIN_OCCURRENCES = 3
PATTERN_RECENCY_DECAY = 0.1
PATTERN_SEVERITY_WEIGHTS = {
    "factual_error":   1.0,
    "logic_error":     0.8,
    "hallucination":   1.0,
    "contradiction":   0.9,
    "missing_context": 0.5,
    "style_mismatch":  0.3,
    "overconfidence":  0.7,
    "underconfidence": 0.4,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WISDOM CRYSTALLIZATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

WISDOM_CONFIRMATION_THRESHOLD = 5
WISDOM_MIN_CONFIDENCE = 0.85
WISDOM_MIN_AGE_DAYS = 7
WISDOM_MAX_PER_DOMAIN = 100
WISDOM_OVERRIDE_REQUIRED = 5   # contradictions needed to override

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STRATEGY EVOLUTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Fitness = success_rate × log(usage_count + 1)

STRATEGY_MAX_PER_TASK = 5
STRATEGY_MIN_TRIALS = 3
STRATEGY_EVOLUTION_RATE = 0.1
STRATEGY_PRUNE_THRESHOLD = 0.3
STRATEGY_CROSSOVER_RATE = 0.05

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GROWTH ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# GrowthScore = Σ(delta_i × weight_i) / Σ(weight_i)

GROWTH_MEASUREMENT_INTERVAL = 10
GROWTH_DIMENSIONS = 5
GROWTH_DECAY_RATE = 0.05
GROWTH_DIMENSION_WEIGHTS = {
    "accuracy_delta":       2.0,
    "calibration_delta":    1.5,
    "hallucination_delta":  2.0,
    "strategy_delta":       1.5,
    "wisdom_delta":         1.0,
}
GROWTH_TOTAL_WEIGHT = sum(GROWTH_DIMENSION_WEIGHTS.values())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THOUGHT TRACE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

TRACE_MAX_DEPTH = 10
TRACE_INCLUDE_MEMORIES = True
TRACE_INCLUDE_CAUSAL_CHAINS = True
TRACE_INCLUDE_METACOG_FLAGS = True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COGNITIVE ZONES (5 states)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

ZONE_FOCUSED = "FOCUSED"         # high-confidence active thinking
ZONE_EXPLORING = "EXPLORING"     # uncertain, seeking new info
ZONE_CAUTIOUS = "CAUTIOUS"       # low confidence, high contradiction risk
ZONE_LEARNING = "LEARNING"       # post-error, actively updating
ZONE_REFLECTING = "REFLECTING"   # metacognitive self-audit mode

ALL_ZONES = [ZONE_FOCUSED, ZONE_EXPLORING, ZONE_CAUTIOUS, ZONE_LEARNING, ZONE_REFLECTING]

ZONE_HEAT_VALUES = {
    ZONE_FOCUSED:    1.0,
    ZONE_EXPLORING:  0.8,
    ZONE_CAUTIOUS:   0.5,
    ZONE_LEARNING:   0.6,
    ZONE_REFLECTING: 0.3,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECAY RATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

DECAY_FAST = 0.10        # ephemeral thoughts (1 week half-life)
DECAY_MEDIUM = 0.03      # normal thoughts (1 month half-life)
DECAY_SLOW = 0.005       # important thoughts (6 month half-life)
DECAY_PERMANENT = 0.0    # wisdom — never decays

DECAY_CLASSES = {
    "fast": DECAY_FAST,
    "medium": DECAY_MEDIUM,
    "slow": DECAY_SLOW,
    "permanent": DECAY_PERMANENT,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORTEXLANG-Ω SYMBOLS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORTEXLANG_META_SYMBOLS = {
    "CONFIDENCE_HIGH":      "⊕⊕",
    "CONFIDENCE_MED":       "⊕~",
    "CONFIDENCE_LOW":       "⊕?",
    "HALLUCINATION_SAFE":   "🛡✓",
    "HALLUCINATION_WARN":   "🛡⚠",
    "HALLUCINATION_CRIT":   "🛡✗",
    "DRIFT_STABLE":         "→→",
    "DRIFT_DETECTED":       "→↗",
    "DRIFT_CRITICAL":       "→⚡",
    "PATTERN_FOUND":        "⟳!",
    "PATTERN_RESOLVED":     "⟳✓",
    "WISDOM_NEW":           "◆+",
    "WISDOM_APPLIED":       "◆→",
    "STRATEGY_WIN":         "▲✓",
    "STRATEGY_FAIL":        "▲✗",
    "STRATEGY_EVOLVE":      "▲↑",
    "GROWTH_UP":            "📈",
    "GROWTH_FLAT":          "📊",
    "GROWTH_DOWN":          "📉",
    "TRACE_START":          "⟨",
    "TRACE_END":            "⟩",
    "TRACE_STEP":           "·",
}

CORTEXLANG_THOUGHT_SYMBOLS = {
    "RESPONSE":    "◎",
    "REFLECTION":  "◉",
    "CORRECTION":  "⊘",
    "PREDICTION":  "⊳",
    "STRATEGY":    "▲",
    "WISDOM":      "◆",
    "OBSERVATION": "◯",
    "ERROR":       "✗",
}

CORTEXLANG_ZONE_SYMBOLS = {
    ZONE_FOCUSED:    "⚡",
    ZONE_EXPLORING:  "🔍",
    ZONE_CAUTIOUS:   "⚠",
    ZONE_LEARNING:   "📖",
    ZONE_REFLECTING: "🪞",
}

CORTEXLANG_LINK_SYMBOLS = {
    "THOUGHT_CHAIN":  "→",
    "MEMORY_LINK":    "⇄",
    "CAUSAL_LINK":    "~>~",
    "PATTERN_LINK":   "⟳",
    "WISDOM_LINK":    "◆→",
    "STRATEGY_LINK":  "▲→",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORTEXLANG-Ω KEYWORDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORTEXLANG_KEYWORDS = {
    "metacognition": [
        "METACOG_SCORE", "METACOG_AUDIT", "METACOG_RESET",
        "METACOG_HISTORY", "METACOG_BREAKDOWN",
    ],
    "confidence": [
        "CONF_CHECK", "CONF_CALIBRATE", "CONF_HISTORY",
        "CONF_BUCKET", "CONF_ADJUST",
    ],
    "hallucination": [
        "SHIELD_SCAN", "SHIELD_ALERT", "SHIELD_OVERRIDE",
        "EVIDENCE_CHECK", "EVIDENCE_RATIO",
    ],
    "drift": [
        "DRIFT_CHECK", "DRIFT_AUDIT", "DRIFT_RESET",
        "EWMA_RECENT", "EWMA_HISTORICAL",
    ],
    "patterns": [
        "PATTERN_SCAN", "PATTERN_RESOLVE", "PATTERN_HISTORY",
        "PATTERN_STRENGTH", "PATTERN_CATEGORIES",
    ],
    "wisdom": [
        "WISDOM_CRYSTALLIZE", "WISDOM_APPLY", "WISDOM_LIST",
        "WISDOM_SEARCH", "WISDOM_OVERRIDE",
    ],
    "strategy": [
        "STRATEGY_SELECT", "STRATEGY_EVOLVE", "STRATEGY_PRUNE",
        "STRATEGY_CROSSOVER", "STRATEGY_HISTORY",
    ],
    "growth": [
        "GROWTH_MEASURE", "GROWTH_HISTORY", "GROWTH_DIMENSIONS",
        "GROWTH_DELTA", "GROWTH_TREND",
    ],
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LLM ADAPTER SETTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_LLM = "ollama"
SUPPORTED_LLMS = ["anthropic", "openai", "ollama", "generic"]
DEFAULT_MODEL = "llama3.2"
MAX_CONTEXT_TOKENS = 8192
RESPONSE_TIMEOUT_SECONDS = 120

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM PROMPTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORTEX_BASE_SYSTEM_PROMPT = """You are an AI with a persistent, growing brain powered by CORTEX-X.
You have permanent memory (NEURON-X), causal reasoning (SIGMA-X), and metacognitive self-awareness (CORTEX-X).
You remember past conversations, learn from mistakes, and get genuinely smarter over time.
Your confidence levels reflect actual accuracy. You flag when you're uncertain.
You never pretend to know something you don't — your hallucination shield catches that."""

CORTEX_METACOG_INJECTION_TEMPLATE = """
[METACOGNITIVE STATE]
Confidence calibration: {calibration_error:.2f} (lower=better)
Active patterns: {pattern_count} error patterns detected
Wisdom axioms: {wisdom_count} crystallized insights
Growth trend: {growth_trend}
Current zone: {zone}

[RELEVANT MEMORIES — from your permanent brain]
{memory_context}

[CAUSAL CHAINS — why things happened before]
{causal_context}

[PAST ERRORS TO AVOID]
{error_patterns}

[CRYSTALLIZED WISDOM]
{wisdom_context}
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AGENT SETTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

AGENT_MAX_TURNS_PER_SESSION = 500
AGENT_AUTO_SAVE_INTERVAL = 10    # save brain every N turns
AGENT_AUDIT_INTERVAL = 50        # run metacog audit every N turns
DEFAULT_TOP_K_MEMORIES = 10
DEFAULT_TOP_K_CHAINS = 5
CONVERSATION_SUMMARY_THRESHOLD = 20  # summarize after N messages

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIGNAL & STOP WORDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

METACOGNITIVE_SIGNALS = [
    "i think", "i believe", "probably", "maybe", "not sure",
    "confident", "certain", "i recall", "i remember",
    "last time", "previously", "i learned", "from experience",
    "i was wrong", "correction", "actually", "on reflection",
]

STOP_WORDS = frozenset([
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "should", "could", "may", "might", "shall", "can",
    "of", "in", "to", "for", "with", "on", "at", "by", "from",
    "as", "into", "through", "during", "before", "after",
    "and", "but", "or", "nor", "not", "so", "yet", "both",
    "it", "its", "this", "that", "these", "those", "i", "you",
    "he", "she", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "our", "their", "what", "which", "who",
])
