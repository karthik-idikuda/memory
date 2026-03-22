"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Compression Utilities                    ║
║  CAULANG-Ω: COMPRESS — smaller brain, same intelligence  ║
╚══════════════════════════════════════════════════════════╝

zlib and lzma compression for CAUSADB data layers.
Benchmarks both and selects optimal based on data size.
"""

from __future__ import annotations

import lzma
import zlib
import time
from typing import Tuple


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ZLIB (default, fast)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def zlib_compress(data: bytes, level: int = 6) -> bytes:
    """Compress with zlib. Level 1-9 (6 = balanced default)."""
    return zlib.compress(data, level)


def zlib_decompress(data: bytes) -> bytes:
    """Decompress zlib data."""
    return zlib.decompress(data)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LZMA (higher ratio, slower)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def lzma_compress(data: bytes, preset: int = 6) -> bytes:
    """Compress with LZMA. Preset 0-9 (higher = better ratio, slower)."""
    return lzma.compress(data, preset=preset)


def lzma_decompress(data: bytes) -> bytes:
    """Decompress LZMA data."""
    return lzma.decompress(data)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTO-SELECT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Compression method indicators (stored in file headers)
COMPRESS_NONE = 0
COMPRESS_ZLIB = 1
COMPRESS_LZMA = 2

_METHOD_NAMES = {
    COMPRESS_NONE: "none",
    COMPRESS_ZLIB: "zlib",
    COMPRESS_LZMA: "lzma",
}


def compress(data: bytes, method: int = COMPRESS_ZLIB) -> bytes:
    """Compress with the specified method."""
    if method == COMPRESS_ZLIB:
        return zlib_compress(data)
    elif method == COMPRESS_LZMA:
        return lzma_compress(data)
    elif method == COMPRESS_NONE:
        return data
    raise ValueError(f"Unknown compression method: {method}")


def decompress(data: bytes, method: int = COMPRESS_ZLIB) -> bytes:
    """Decompress with the specified method."""
    if method == COMPRESS_ZLIB:
        return zlib_decompress(data)
    elif method == COMPRESS_LZMA:
        return lzma_decompress(data)
    elif method == COMPRESS_NONE:
        return data
    raise ValueError(f"Unknown compression method: {method}")


def auto_compress(data: bytes) -> Tuple[bytes, int]:
    """
    Automatically select the best compression method.

    Strategy:
    - data < 1KB: no compression (overhead not worth it)
    - data < 100KB: zlib (fast, decent ratio)
    - data >= 100KB: try both, pick smaller result

    Returns: (compressed_data, method_code)
    """
    if len(data) < 1024:
        return data, COMPRESS_NONE

    if len(data) < 102400:  # 100KB
        return zlib_compress(data), COMPRESS_ZLIB

    # For larger data, benchmark both
    zlib_result = zlib_compress(data)
    lzma_result = lzma_compress(data)

    if len(lzma_result) < len(zlib_result) * 0.85:
        # LZMA is at least 15% smaller — worth the speed tradeoff
        return lzma_result, COMPRESS_LZMA
    return zlib_result, COMPRESS_ZLIB


def compression_ratio(original: bytes, compressed: bytes) -> float:
    """Compute compression ratio (0.0 = perfect, 1.0 = no compression)."""
    if len(original) == 0:
        return 1.0
    return len(compressed) / len(original)


def benchmark_compression(data: bytes) -> dict:
    """
    Benchmark all compression methods on the given data.
    Returns timing and ratio for each method.
    """
    results = {}

    for method, name in _METHOD_NAMES.items():
        if method == COMPRESS_NONE:
            results[name] = {
                'compressed_size': len(data),
                'ratio': 1.0,
                'compress_time_ms': 0.0,
                'decompress_time_ms': 0.0,
            }
            continue

        # Compress
        start = time.perf_counter()
        compressed = compress(data, method)
        compress_ms = (time.perf_counter() - start) * 1000

        # Decompress
        start = time.perf_counter()
        decompressed = decompress(compressed, method)
        decompress_ms = (time.perf_counter() - start) * 1000

        # Verify
        assert decompressed == data, f"Round-trip failed for {name}"

        results[name] = {
            'compressed_size': len(compressed),
            'ratio': compression_ratio(data, compressed),
            'compress_time_ms': round(compress_ms, 3),
            'decompress_time_ms': round(decompress_ms, 3),
        }

    results['original_size'] = len(data)
    return results
