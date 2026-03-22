"""CORTEX-X — Compression utilities."""

import zlib
import json
from typing import Any
from cortex.config import COMPRESSION_LEVEL


def compress(data: bytes, level: int = COMPRESSION_LEVEL) -> bytes:
    """Compress bytes with zlib."""
    return zlib.compress(data, level)


def decompress(data: bytes) -> bytes:
    """Decompress zlib bytes."""
    return zlib.decompress(data)


def compress_json(obj: Any, level: int = COMPRESSION_LEVEL) -> bytes:
    """Serialize to JSON and compress."""
    raw = json.dumps(obj, default=str).encode("utf-8")
    return compress(raw, level)


def decompress_json(data: bytes) -> Any:
    """Decompress and deserialize JSON."""
    raw = decompress(data)
    return json.loads(raw.decode("utf-8"))


def compression_ratio(original: bytes, compressed: bytes) -> float:
    """Compute compression ratio (higher = better compression)."""
    if len(original) == 0:
        return 0.0
    return 1.0 - (len(compressed) / len(original))
