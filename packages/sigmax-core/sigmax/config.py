"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Central Configuration                   ║
║  CAULANG-Ω: CORTEX CONFIG — source of all truth          ║
╚══════════════════════════════════════════════════════════╝

Every tunable parameter lives here. No magic numbers scattered
in code. Change a value here → it changes everywhere.

Sister to NEURON-X config.py — same philosophy, causal domain.
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAUSADB BINARY FORMAT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAUSADB_MAGIC = b'\x53\x49\x47\xCE'   # SIG + 0xCE — unique to SIGMA-X
CAUSADB_VERSION = 0x0001
CAUSADB_EXTENSION = ".sigma"

# Layer 1: Header — 80 bytes
CAUSADB_HEADER_FORMAT = '>4sHIIIIIIddd8sI4sHI'
CAUSADB_HEADER_SIZE = 80

# Layer 4: Causal Graph Map — edge entries
CAUSADB_EDGE_FORMAT = '>16s16sfB'    # source_id, target_id, weight, edge_type
CAUSADB_EDGE_SIZE = 37

# Layer 5: Prediction Log entry
CAUSADB_PRED_FORMAT = '>16s16sdBf'   # pred_id, chain_id, timestamp, status, accuracy
CAUSADB_PRED_SIZE = 41

# Layer 6: Integrity Seal — 64 bytes
CAUSADB_SEAL_FORMAT = '>32sdQ16s'    # sha256, seal_time, node_count, version_tag
CAUSADB_SEAL_SIZE = 64

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAUSENODE TYPES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAUSE_TYPES = (
    "direct",        # A directly causes B
    "indirect",      # A leads to B through intermediaries
    "correlative",   # A and B co-occur, direction unclear
    "inhibitory",    # A prevents B
    "conditional",   # A causes B only if C
    "temporal",      # A precedes B in time
    "counterfactual", # If not A, then not B
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIDENCE LEVELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONFIDENCE_SPECULATIVE = 0.30
CONFIDENCE_MODERATE = 0.60
CONFIDENCE_STRONG = 0.80
CONFIDENCE_AXIOM = 0.95

CONFIDENCE_LEVELS = {
    "speculative": CONFIDENCE_SPECULATIVE,
    "moderate":    CONFIDENCE_MODERATE,
    "strong":      CONFIDENCE_STRONG,
    "axiom":       CONFIDENCE_AXIOM,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAUSAL DECAY RATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAUSAL_DECAY_RATES = {
    "fast":      0.015000,   # half-life ≈ 46.2 days — speculative reasoning
    "medium":    0.005000,   # half-life ≈ 138.6 days — normal chains
    "slow":      0.001500,   # half-life ≈ 462.1 days — well-evidenced
    "permanent": 0.000000,   # never decays — axioms
}

DECAY_CLASS_TO_RATE = {
    "fast":      0.015000,
    "medium":    0.005000,
    "slow":      0.001500,
    "permanent": 0.000000,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAUSAL THERMAL ZONES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

ZONE_ACTIVE = "ACTIVE"
ZONE_WARM = "WARM"
ZONE_DORMANT = "DORMANT"
ZONE_AXIOM = "AXIOM"
ZONE_ARCHIVED = "ARCHIVED"

ZONE_HEAT_THRESHOLDS = {
    ZONE_ACTIVE:   0.70,   # heat >= 0.70
    ZONE_WARM:     0.40,   # heat >= 0.40
    ZONE_DORMANT:  0.10,   # heat >= 0.10
    ZONE_AXIOM:    -1.0,   # special: confidence >= AXIOM threshold
    ZONE_ARCHIVED: 0.00,   # heat < 0.10 and not axiom
}

ZONE_HEAT_VALUES = {
    ZONE_ACTIVE:   1.0,
    ZONE_WARM:     0.6,
    ZONE_DORMANT:  0.2,
    ZONE_AXIOM:    0.9,    # axioms stay high but don't compete with active
    ZONE_ARCHIVED: 0.0,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIGMA SCORING WEIGHTS (9-component)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIGMA = Σ(component × weight) / Σ(weights)

SIGMA_CAUSAL_RESONANCE = 3.0    # word overlap between query and cause+effect
SIGMA_EVIDENCE_WEIGHT = 2.5     # tanh(net_evidence / 5.0)
SIGMA_PREDICTION_ACCURACY = 2.0 # verified_correct / total_predictions
SIGMA_RECENCY_CURVE = 1.8       # exp(-λ × age_days)
SIGMA_ZONE_HEAT = 1.5           # zone_heat_value
SIGMA_CHAIN_DEPTH = 1.2         # log2(1 + chain_length) / 5.0
SIGMA_CONFIDENCE = 1.0          # node.confidence directly
SIGMA_DECAY_DEBT = 1.3          # 1.0 - current_decay_amount
SIGMA_FALSIFICATION_PENALTY = 0.8  # penalty for falsified predictions

SIGMA_TOTAL_WEIGHT = (
    SIGMA_CAUSAL_RESONANCE +
    SIGMA_EVIDENCE_WEIGHT +
    SIGMA_PREDICTION_ACCURACY +
    SIGMA_RECENCY_CURVE +
    SIGMA_ZONE_HEAT +
    SIGMA_CHAIN_DEPTH +
    SIGMA_CONFIDENCE +
    SIGMA_DECAY_DEBT +
    SIGMA_FALSIFICATION_PENALTY
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAUSAL HEAT FORMULA WEIGHTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

HEAT_ACCESS_WEIGHT = 0.30
HEAT_RECENCY_WEIGHT = 0.25
HEAT_EVIDENCE_WEIGHT = 0.20
HEAT_PREDICTION_WEIGHT = 0.15
HEAT_CONFIDENCE_WEIGHT = 0.10

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PREDICTION ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

PREDICTION_STATUS_PENDING = "pending"
PREDICTION_STATUS_VERIFIED = "verified"
PREDICTION_STATUS_FALSIFIED = "falsified"
PREDICTION_STATUS_EXPIRED = "expired"

PREDICTION_HORIZONS = {
    "immediate":  1,     # 1 day
    "short":      7,     # 1 week
    "medium":     30,    # 1 month
    "long":       90,    # 3 months
    "extended":   365,   # 1 year
}

PREDICTION_CONFIDENCE_BOOST = 0.05    # on verified prediction
PREDICTION_CONFIDENCE_HIT = 0.10      # on falsified prediction

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EVIDENCE ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

EVIDENCE_SUPPORT_BOOST = 0.03
EVIDENCE_CONTRADICT_HIT = 0.05
EVIDENCE_TANH_SCALE = 5.0    # tanh(net_evidence / EVIDENCE_TANH_SCALE)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AXIOM CRYSTALLIZATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

AXIOM_CONFIDENCE_THRESHOLD = 0.95
AXIOM_ACCESS_THRESHOLD = 15
AXIOM_EVIDENCE_NET_THRESHOLD = 10
AXIOM_PREDICTION_ACCURACY_THRESHOLD = 0.80

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COUNTERFACTUAL ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

COUNTERFACTUAL_MAX_PER_CHAIN = 5
COUNTERFACTUAL_MIN_CONFIDENCE = 0.40

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MULTI-HOP CHAINS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

MULTIHOP_MAX_DEPTH = 10
MULTIHOP_MIN_CONFIDENCE = 0.20

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REACTIVATION THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

REACTIVATE_ACTIVE_THRESHOLD = 0.80
REACTIVATE_WARM_THRESHOLD = 0.50
REACTIVATE_JACCARD_GATE = 0.15

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM OPERATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

AUDIT_INTERVAL = 50           # run audit every N operations
DEFAULT_TOP_K = 7             # default retrieval count
AUTO_SAVE_INTERVAL = 5        # auto-save every N chain additions
DEFAULT_PAGE_SIZE = 50        # pagination
MAX_INPUT_CHARS = 2000        # max input for chain extraction
STALE_LOCK_SECONDS = 30       # lock file timeout
LOCK_WAIT_SECONDS = 5         # max wait for lock acquisition
LOCK_POLL_INTERVAL_MS = 100   # poll interval for lock checks

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAUSAL CHAIN WEIGHT LIMITS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

MAX_CHAIN_WEIGHT = 3.0
MIN_CHAIN_WEIGHT = 0.1
STRENGTHEN_CHAIN_AMOUNT = 0.12

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIDENCE EVOLUTION RULES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONFIDENCE_EVIDENCE_BOOST = 0.03    # per supporting evidence
CONFIDENCE_EVIDENCE_HIT = 0.05      # per contradicting evidence
CONFIDENCE_PREDICTION_BOOST = 0.05  # on verified prediction
CONFIDENCE_PREDICTION_HIT = 0.10    # on falsified prediction
CONFIDENCE_MIN = 0.01               # never reaches zero
CONFIDENCE_MAX = 1.00               # hard cap

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CHAIN EXTRACTION SIGNAL WORDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAUSAL_SIGNAL_WORDS = frozenset({
    'because', 'since', 'therefore', 'thus', 'hence', 'consequently',
    'causes', 'caused', 'causing', 'leads', 'led', 'leading',
    'results', 'resulted', 'resulting', 'due', 'owing',
    'triggers', 'triggered', 'triggering', 'produces', 'produced',
    'enables', 'enabled', 'prevents', 'prevented', 'preventing',
    'implies', 'implied', 'means', 'meant', 'indicates', 'indicated',
    'drives', 'drove', 'driving', 'forces', 'forced', 'forcing',
    'creates', 'created', 'generates', 'generated', 'spawns', 'spawned',
    'affects', 'affected', 'influences', 'influenced', 'determines',
    'explains', 'explained', 'accounts', 'contributes', 'contributed',
    'so', 'accordingly', 'as_a_result', 'for_this_reason',
    'if', 'then', 'when', 'whenever', 'unless', 'provided',
})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STOP WORDS (shared with NEURON-X)
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
    'via', 'per', 'yet', 'nor', 'she', 'him', 'whom',
})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAULANG-Ω SYMBOLS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAULANG_CHAIN_SYMBOLS = {
    "DIRECT":        "~>~",       # A causes B
    "INDIRECT":      "~>>~",      # A leads to B through intermediaries
    "CORRELATIVE":   "~<>~",      # A and B correlate
    "INHIBITORY":    "~|~",       # A prevents B
    "CONDITIONAL":   "~?~",       # A causes B if C
    "TEMPORAL":      "~t>~",      # A precedes B
    "COUNTERFACTUAL": "~!~",      # if not A, not B
}

CAULANG_ZONE_SYMBOLS = {
    ZONE_ACTIVE:   "⚡ [A]",
    ZONE_WARM:     "🌡 [W]",
    ZONE_DORMANT:  "💤 [D]",
    ZONE_AXIOM:    "◆ [X]",
    ZONE_ARCHIVED: "📦 [R]",
}

CAULANG_CONFIDENCE_SYMBOLS = {
    "speculative": "(?)",
    "moderate":    "(~)",
    "strong":      "(!)",
    "axiom":       "(◆)",
}

CAULANG_ACTION_SYMBOLS = {
    "FORGE_CHAIN":    "⊕C",
    "ECHO_CHAIN":     "●C",
    "STRENGTHEN":     "↑↑",
    "WEAKEN":         "↓↓",
    "CRYSTALLIZE":    "◆◆",
    "ARCHIVE":        "📦",
    "REACTIVATE":     "^^",
    "PREDICT":        "→?",
    "VERIFY":         "→✓",
    "FALSIFY":        "→✗",
    "COUNTERFACT":    "~!",
    "MULTIHOP":       ">>>",
    "BRIDGE_SYNC":    "⇄",
    "AUDIT":          "🔍",
    "NMP_WRITE":      ">>",
    "PRUNE":          "-x-",
    "MERGE":          "⊕⊕",
    "FORK":           "⊕/",
}

CAULANG_EVIDENCE_SYMBOLS = {
    "SUPPORT":   "[+]",
    "CONTRADICT": "[-]",
    "NEUTRAL":   "[~]",
}

CAULANG_PREDICTION_SYMBOLS = {
    PREDICTION_STATUS_PENDING:   "→?",
    PREDICTION_STATUS_VERIFIED:  "→✓",
    PREDICTION_STATUS_FALSIFIED: "→✗",
    PREDICTION_STATUS_EXPIRED:   "→⊘",
}

CAULANG_EXISTENCE_SYMBOLS = {
    "BORN":       "╔══╗",
    "DIED":       "╚══╝",
    "LIVE":       "◈",
    "SLEEP":      "◇",
    "AXIOM":      "◆",
    "GHOST":      "○",
    "FORGE":      "⊕",
    "ARCHIVE":    "⊖",
}

CAULANG_GRAPH_SYMBOLS = {
    "NODE":       "[C]",
    "EDGE":       "|||",
    "PATH":       ">>>",
    "CYCLE":      "⟲",
    "ROOT":       "▲",
    "LEAF":       "▼",
    "HUB":        "★",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAULANG-Ω KEYWORDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAULANG_KEYWORDS = frozenset({
    'CAUSENODE', 'CHAIN', 'SIGMA', 'CAUSADB',
    'AXIOM', 'PREDICT', 'VERIFY', 'FALSIFY',
    'COUNTERFACT', 'MULTIHOP', 'BRIDGE',
    'EVIDENCE', 'SUPPORT', 'CONTRADICT',
    'PULSE_C', 'ZONE', 'HEAT', 'DECAY',
    'FORGE_CHAIN', 'ECHO_CHAIN', 'REACTIVATE',
    'CRYSTALLIZE', 'ARCHIVE', 'PRUNE',
    'SESSION_BEGIN', 'SESSION_END',
    'GRAPH', 'PATH', 'CYCLE', 'HUB',
    'BRAIN', 'THINK', 'REASON', 'CONCLUDE',
})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EDGE TYPES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

EDGE_TYPE_CAUSES = 0
EDGE_TYPE_ENABLES = 1
EDGE_TYPE_PREVENTS = 2
EDGE_TYPE_CORRELATES = 3
EDGE_TYPE_TEMPORAL = 4

EDGE_TYPE_NAMES = {
    0: "CAUSES",
    1: "ENABLES",
    2: "PREVENTS",
    3: "CORRELATES",
    4: "TEMPORAL",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEURON-X BRIDGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

BRIDGE_SYNC_INTERVAL = 10        # sync every N operations
BRIDGE_MIN_CONFIDENCE = 0.50     # min confidence to push conclusion to NEURON-X
BRIDGE_MAX_CONCLUSIONS = 20      # max conclusions per sync

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RATE LIMITING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

RATE_LIMIT_REQUESTS_PER_MINUTE = 60

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM PROMPTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROMPT_SYSTEM = """You are an AI assistant powered by SIGMA-X OMEGA persistent causal reasoning.
Retrieved causal chains ({count} total, SIGMA-scored):
{causal_context}
Rules: reference causal chains naturally, explain reasoning paths,
surface predictions and their accuracy, note axioms as established facts,
use tentative language for confidence < 0.5, cite multi-hop paths."""

PROMPT_EXTRACT_CHAINS = """Extract causal relationships from: "{message}"
Look for: cause-effect pairs, temporal sequences, conditional logic,
inhibitory relationships, correlations.
Return JSON array: [{{"cause": str, "effect": str, "type": str,
"confidence": float, "evidence": str, "tags": [str],
"subject": str, "decay_class": str}}]
Types: direct, indirect, correlative, inhibitory, conditional, temporal, counterfactual
Decay: fast (speculation), medium (normal), slow (well-evidenced), permanent (axiom)"""

PROMPT_PREDICT = """Based on causal chain: "{chain}"
Context: "{context}"
Generate a prediction about what will happen next.
Return JSON: {{"prediction": str, "confidence": float,
"horizon": str, "reasoning": str, "conditions": [str]}}
Horizons: immediate (1d), short (1w), medium (1m), long (3m), extended (1y)"""

PROMPT_COUNTERFACTUAL = """Original chain: "{cause}" ~>~ "{effect}" (conf: {confidence})
Generate a counterfactual scenario: what if the cause didn't happen?
Return JSON: {{"counterfactual_cause": str, "counterfactual_effect": str,
"plausibility": float, "reasoning": str, "implications": [str]}}"""

PROMPT_VERIFY_PREDICTION = """Prediction: "{prediction}" (made {days_ago} days ago)
Current context: "{context}"
Chain: "{cause}" ~>~ "{effect}"
Return JSON: {{"is_verified": bool, "confidence_in_verdict": float,
"evidence": str, "should_update_chain": bool, "new_confidence": float}}"""

PROMPT_CONSOLIDATE_CHAINS = """Chain A: "{cause_a}" ~>~ "{effect_a}" (conf: {conf_a}, created: {date_a})
Chain B: "{cause_b}" ~>~ "{effect_b}" (conf: {conf_b}, created: {date_b})
Similarity: {similarity}
Return JSON: {{"should_merge": bool, "merged_cause": str, "merged_effect": str,
"merged_confidence": float, "reason": str}}"""

PROMPT_BRAIN_SUMMARY = """Causal Brain Stats: {stats}
Top reasoning chains: {top_chains}
Write 3 sentences: what the brain understands causally, reasoning health,
patterns in predictions. Sound like a scientist reviewing evidence. Not a robot."""
