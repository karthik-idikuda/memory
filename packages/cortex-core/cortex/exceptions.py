"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Custom Exception Hierarchy                 ║
║  CORTEXLANG-Ω: EXCEPTION TREE — every failure mode named    ║
╚══════════════════════════════════════════════════════════════╝

Every exception CORTEX-X can raise, organized by domain.
12 domains, 42 exception classes — explicit, specific, catchable.
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CortexError(Exception):
    """Root of all CORTEX-X errors."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORTEX-DB ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CortexDBError(CortexError):
    """Base class for all CORTEX-DB storage errors."""
    pass


class CortexDBCorruptionError(CortexDBError):
    """The .cortex file is corrupted — magic bytes, seal, or structure invalid."""
    pass


class CortexDBVersionError(CortexDBError):
    """The .cortex file version is unsupported."""
    pass


class CortexDBLockError(CortexDBError):
    """Failed to acquire or release the .cortex.lock file."""
    pass


class CortexDBWriteError(CortexDBError):
    """Failed to write to .cortex file during CMP protocol."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THOUGHT NODE ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ThoughtNodeError(CortexError):
    """Base class for ThoughtNode-related errors."""
    pass


class ThoughtNodeValidationError(ThoughtNodeError):
    """A ThoughtNode field has an invalid value."""
    pass


class ThoughtNodeNotFoundError(ThoughtNodeError):
    """Requested ThoughtNode does not exist in the brain."""
    pass


class ThoughtNodeDuplicateError(ThoughtNodeError):
    """A ThoughtNode with the same content already exists."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# METACOG ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MetacogError(CortexError):
    """Base class for metacognitive engine errors."""
    pass


class MetacogCalibrationError(MetacogError):
    """Confidence calibration computation failed."""
    pass


class MetacogThresholdError(MetacogError):
    """A metacognitive threshold was exceeded."""
    pass


class MetacogOverflowError(MetacogError):
    """Metacognitive state buffer overflow."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIDENCE ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ConfidenceError(CortexError):
    """Base class for confidence calibration errors."""
    pass


class UncalibratedError(ConfidenceError):
    """Not enough data for reliable calibration."""
    pass


class ConfidenceOutOfRangeError(ConfidenceError):
    """Confidence value outside valid range [0.0, 1.0]."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HALLUCINATION ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class HallucinationError(CortexError):
    """Base class for hallucination shield errors."""
    pass


class HallucinationShieldBlockError(HallucinationError):
    """Response blocked by hallucination shield — critical evidence gap."""
    pass


class EvidenceMissingError(HallucinationError):
    """No supporting evidence found in memory for a claim."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DRIFT ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DriftError(CortexError):
    """Base class for cognitive drift errors."""
    pass


class DriftThresholdExceededError(DriftError):
    """Cognitive drift exceeds acceptable threshold."""
    pass


class DriftAuditTimeoutError(DriftError):
    """Drift audit took too long."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PATTERN ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PatternError(CortexError):
    """Base class for error pattern recognition errors."""
    pass


class PatternDetectionError(PatternError):
    """Failed to detect or classify error pattern."""
    pass


class PatternCycleError(PatternError):
    """Pattern feedback cycle detected — pattern recognition feeding itself."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WISDOM ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WisdomError(CortexError):
    """Base class for wisdom crystallization errors."""
    pass


class WisdomCrystallizationError(WisdomError):
    """Insight failed to meet crystallization criteria."""
    pass


class WisdomMaxReachedError(WisdomError):
    """Maximum wisdom count per domain exceeded."""
    pass


class WisdomOverrideError(WisdomError):
    """Insufficient counter-evidence to override existing wisdom."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STRATEGY ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class StrategyError(CortexError):
    """Base class for strategy evolution errors."""
    pass


class StrategyEvolutionError(StrategyError):
    """Strategy mutation or crossover failed."""
    pass


class StrategyPruneError(StrategyError):
    """No strategies left after pruning — all below threshold."""
    pass


class StrategyNotFoundError(StrategyError):
    """Requested strategy does not exist."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GROWTH ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class GrowthError(CortexError):
    """Base class for growth engine errors."""
    pass


class GrowthMeasurementError(GrowthError):
    """Failed to measure growth — insufficient data."""
    pass


class GrowthRegressionError(GrowthError):
    """Significant performance regression detected."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BRIDGE ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BridgeError(CortexError):
    """Base class for ecosystem bridge errors."""
    pass


class NeuronXSyncError(BridgeError):
    """Failed to sync with NEURON-X memory system."""
    pass


class SigmaXSyncError(BridgeError):
    """Failed to sync with SIGMA-X reasoning system."""
    pass


class LLMAdapterError(BridgeError):
    """LLM adapter connection or generation failed."""
    pass


class LLMTimeoutError(LLMAdapterError):
    """LLM generation timed out."""
    pass


class LLMNotAvailableError(LLMAdapterError):
    """Requested LLM model is not available."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORTEXLANG ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CortexLangError(CortexError):
    """Base class for CORTEXLANG-Ω language errors."""
    pass


class CortexLangSyntaxError(CortexLangError):
    """Invalid CORTEXLANG-Ω syntax."""
    pass


class CortexLangParseError(CortexLangError):
    """Failed to parse CORTEXLANG-Ω expression."""
    pass


class CortexLangValidationError(CortexLangError):
    """CORTEXLANG-Ω notation validated but semantically invalid."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENGINE ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EngineError(CortexError):
    """Base class for execution engine errors."""
    pass


class AgentLoopError(EngineError):
    """Error in the main agent thinking loop."""
    pass


class ConversationError(EngineError):
    """Conversation context management error."""
    pass


class ToolExecutionError(EngineError):
    """Tool execution failed."""
    pass


class ToolNotFoundError(EngineError):
    """Requested tool does not exist in the registry."""
    pass
