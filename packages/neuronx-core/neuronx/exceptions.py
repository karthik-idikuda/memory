"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Custom Exceptions                      ║
║  NRNLANG-Ω: ERROR CORTEX — all failure modes defined     ║
╚══════════════════════════════════════════════════════════╝
"""


class NeuronXError(Exception):
    """Base exception for all NEURON-X errors."""
    pass


class NeuronXCorruptionError(NeuronXError):
    """SOMA file is corrupted and cannot be recovered."""
    pass


class NeuronXLockTimeoutError(NeuronXError):
    """Could not acquire file lock within timeout period."""
    pass


class NeuronXIntegrityError(NeuronXError):
    """SHA-256 integrity check failed."""
    pass


class NeuronXBrainNotFoundError(NeuronXError):
    """Referenced brain does not exist."""
    pass


class NeuronXMemoryExpiredError(NeuronXError):
    """Attempted operation on an expired memory."""
    pass


class NeuronXConfigError(NeuronXError):
    """Invalid configuration parameter."""
    pass


class NeuronXExportError(NeuronXError):
    """Error during brain export."""
    pass


class NeuronXImportError(NeuronXError):
    """Error during brain import."""
    pass


class NRNSyntaxError(NeuronXError):
    """NRNLANG-Ω syntax error during parsing."""

    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.line = line
        self.column = column
        super().__init__(f"Line {line}, Col {column}: {message}")


class NRNRuntimeError(NeuronXError):
    """NRNLANG-Ω runtime error during execution."""
    pass


class NeuronXLicenseError(NeuronXError):
    """License validation failed."""
    pass


class NeuronXRateLimitError(NeuronXError):
    """API rate limit exceeded."""

    def __init__(self, retry_after: float = 60.0):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s")


class NeuronXAuthError(NeuronXError):
    """Authentication or authorization failed."""
    pass
