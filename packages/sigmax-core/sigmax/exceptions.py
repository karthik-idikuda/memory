"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Custom Exception Hierarchy              ║
║  CAULANG-Ω: EXCEPTION TREE — every failure mode named   ║
╚══════════════════════════════════════════════════════════╝

Every exception SIGMA-X can raise, organized by domain.
Mirror of NEURON-X exception philosophy: explicit, specific, catchable.
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SigmaXError(Exception):
    """Root of all SIGMA-X errors."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAUSADB ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CausaDBError(SigmaXError):
    """Base class for all CAUSADB storage errors."""
    pass


class CausaDBCorruptionError(CausaDBError):
    """The .sigma file is corrupted — magic bytes, seal, or structure invalid."""
    pass


class CausaDBVersionError(CausaDBError):
    """The .sigma file version is unsupported."""
    pass


class CausaDBLockError(CausaDBError):
    """Failed to acquire or release the .sigma.lock file."""
    pass


class CausaDBWriteError(CausaDBError):
    """Failed to write to .sigma file during NMP protocol."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAUSENODE ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CauseNodeError(SigmaXError):
    """Base class for CauseNode-related errors."""
    pass


class CauseNodeValidationError(CauseNodeError):
    """A CauseNode field has an invalid value."""
    pass


class CauseNodeNotFoundError(CauseNodeError):
    """Requested CauseNode does not exist in the brain."""
    pass


class CauseNodeDuplicateError(CauseNodeError):
    """A CauseNode with the same cause-effect pair already exists."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CHAIN ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ChainError(SigmaXError):
    """Base class for causal chain errors."""
    pass


class ChainExtractionError(ChainError):
    """Failed to extract causal chains from input text."""
    pass


class ChainCycleError(ChainError):
    """A causal cycle was detected in the chain graph."""
    pass


class ChainDepthError(ChainError):
    """Chain exceeds maximum allowed depth (multi-hop limit)."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PREDICTION ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PredictionError(SigmaXError):
    """Base class for prediction engine errors."""
    pass


class PredictionNotFoundError(PredictionError):
    """Requested prediction does not exist."""
    pass


class PredictionExpiredError(PredictionError):
    """Prediction horizon has passed without verification."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EVIDENCE ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EvidenceError(SigmaXError):
    """Base class for evidence engine errors."""
    pass


class EvidenceConflictError(EvidenceError):
    """New evidence directly contradicts existing strong evidence."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COUNTERFACTUAL ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CounterfactualError(SigmaXError):
    """Base class for counterfactual engine errors."""
    pass


class CounterfactualLimitError(CounterfactualError):
    """Max counterfactuals per chain exceeded."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTEGRITY ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class IntegrityError(SigmaXError):
    """Base class for integrity/seal errors."""
    pass


class IntegritySealError(IntegrityError):
    """Integrity seal verification failed — data may be tampered."""
    pass


class IntegrityHashError(IntegrityError):
    """SHA-256 hash mismatch detected."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BRIDGE ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BridgeError(SigmaXError):
    """Base class for NEURON-X bridge errors."""
    pass


class BridgeSyncError(BridgeError):
    """Failed to sync with NEURON-X memory system."""
    pass


class BridgeNotConnectedError(BridgeError):
    """NEURON-X bridge is not connected or available."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAULANG ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CaulangError(SigmaXError):
    """Base class for CAULANG-Ω language errors."""
    pass


class CaulangSyntaxError(CaulangError):
    """Invalid CAULANG-Ω syntax."""
    pass


class CaulangParseError(CaulangError):
    """Failed to parse CAULANG-Ω expression."""
    pass


class CaulangValidationError(CaulangError):
    """CAULANG-Ω notation validated but semantically invalid."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BRAIN ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BrainError(SigmaXError):
    """Base class for SigmaBrain orchestrator errors."""
    pass


class BrainNotLoadedError(BrainError):
    """SigmaBrain has not been loaded or initialized."""
    pass


class BrainCapacityError(BrainError):
    """Brain has reached maximum capacity."""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GRAPH ERRORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class GraphError(SigmaXError):
    """Base class for causal graph errors."""
    pass


class GraphCycleError(GraphError):
    """Cycle detected in directed causal graph."""
    pass


class GraphDisconnectedError(GraphError):
    """Graph contains disconnected components."""
    pass
