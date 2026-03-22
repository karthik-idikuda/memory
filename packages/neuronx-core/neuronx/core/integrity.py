"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Integrity Engine                       ║
║  NRNLANG-Ω: SHA-256, ID generation, NMP protocol        ║
║  Ensures every byte of the brain is tamper-proof         ║
╚══════════════════════════════════════════════════════════╝
"""

import hashlib
import struct
import time
from typing import Optional

from neuronx.config import (
    SOMA_MAGIC, SOMA_VERSION, SOMA_HEADER_SIZE, SOMA_SEAL_SIZE,
)


def generate_engram_id(text: str, salt: Optional[str] = None) -> str:
    """
    NRNLANG-Ω: Generate a 16-char SHA-256 fingerprint for an engram.
    Uses text + timestamp + optional salt for uniqueness.
    """
    data = f"{text}:{time.time()}"
    if salt:
        data = f"{data}:{salt}"
    h = hashlib.sha256(data.encode("utf-8")).hexdigest()
    return h[:16]


def compute_checksum(data: bytes) -> bytes:
    """
    NRNLANG-Ω: Compute SHA-256 checksum of binary data.
    Returns 32 raw bytes.
    """
    return hashlib.sha256(data).digest()


def verify_checksum(data: bytes, expected_hash: bytes) -> bool:
    """
    NRNLANG-Ω: Verify SHA-256 checksum matches.
    """
    return compute_checksum(data) == expected_hash


def build_header(
    total_engrams: int,
    hot_count: int,
    warm_count: int,
    cold_count: int,
    silent_count: int,
    total_axons: int,
    created_at: float,
    modified_at: float,
    owner_hash: Optional[bytes] = None,
    compression_flag: int = 1,
) -> bytes:
    """
    NRNLANG-Ω: Build the 64-byte SOMA-DB header.

    Format (big-endian): '>4sHIIIIIIddd8sI4sH'
      [4s]  magic = b'NRN\\xCE'
      [H]   version
      [I]   total_engram_count
      [I]   hot_count
      [I]   warm_count
      [I]   cold_count
      [I]   silent_count
      [I]   axon_count
      [d]   created_ts
      [d]   modified_ts
      [d]   saved_ts
      [8s]  owner_hash (first 8 bytes of SHA-256(brain_name))
      [I]   compression_flag (0=none, 1=zlib, 2=lzma)
      [4s]  reserved
      [H]   header_checksum (sum of all preceding bytes mod 65536)
    """
    if owner_hash is None:
        owner_hash = b'\x00' * 8
    else:
        owner_hash = owner_hash[:8].ljust(8, b'\x00')

    saved_ts = time.time()
    reserved = b'\x00\x00\x00\x00'

    # Pack everything except the last H (checksum)
    preamble_format = '>4sHIIIIIIddd8sI4s'
    preamble = struct.pack(
        preamble_format,
        SOMA_MAGIC,
        SOMA_VERSION,
        total_engrams,
        hot_count,
        warm_count,
        cold_count,
        silent_count,
        total_axons,
        created_at,
        modified_at,
        saved_ts,
        owner_hash,
        compression_flag,
        reserved,
    )

    # Compute header checksum
    header_checksum = sum(preamble) % 65536

    # Full header
    header = preamble + struct.pack('>H', header_checksum)
    assert len(header) == SOMA_HEADER_SIZE, f"Header must be {SOMA_HEADER_SIZE} bytes, got {len(header)}"
    return header


def parse_header(header_bytes: bytes) -> dict:
    """
    NRNLANG-Ω: Parse the 64-byte SOMA-DB header.
    """
    assert len(header_bytes) >= SOMA_HEADER_SIZE, f"Header too short: {len(header_bytes)} < {SOMA_HEADER_SIZE}"

    fmt = '>4sHIIIIIIddd8sI4sH'
    fields = struct.unpack(fmt, header_bytes[:SOMA_HEADER_SIZE])

    magic = fields[0]
    if magic != SOMA_MAGIC:
        raise ValueError(f"Invalid SOMA magic: {magic!r}, expected {SOMA_MAGIC!r}")

    return {
        "magic": magic,
        "version": fields[1],
        "total_engrams": fields[2],
        "hot_count": fields[3],
        "warm_count": fields[4],
        "cold_count": fields[5],
        "silent_count": fields[6],
        "total_axons": fields[7],
        "created_at": fields[8],
        "modified_at": fields[9],
        "saved_at": fields[10],
        "owner_hash": fields[11],
        "compression_flag": fields[12],
        "reserved": fields[13],
        "header_checksum": fields[14],
    }


def build_seal(data_hash: bytes, save_count: int) -> bytes:
    """
    NRNLANG-Ω: Build the 64-byte integrity seal.

    Format (big-endian): '>32sdQ16s'
      [32s] sha256_hash (32 raw bytes)
      [d]   sealed_ts
      [Q]   save_count (unsigned 64-bit)
      [16s] reserved
    """
    sealed_ts = time.time()
    reserved = b'\x00' * 16

    seal = struct.pack(
        '>32sdQ16s',
        data_hash,
        sealed_ts,
        save_count,
        reserved,
    )
    assert len(seal) == SOMA_SEAL_SIZE, f"Seal must be {SOMA_SEAL_SIZE} bytes, got {len(seal)}"
    return seal


def parse_seal(seal_bytes: bytes) -> dict:
    """
    NRNLANG-Ω: Parse the 64-byte integrity seal.
    """
    assert len(seal_bytes) >= SOMA_SEAL_SIZE, f"Seal too short: {len(seal_bytes)} < {SOMA_SEAL_SIZE}"

    fields = struct.unpack('>32sdQ16s', seal_bytes[:SOMA_SEAL_SIZE])

    return {
        "data_hash": fields[0],
        "sealed_ts": fields[1],
        "save_count": fields[2],
        "reserved": fields[3],
    }


def build_owner_hash(brain_name: str) -> bytes:
    """
    NRNLANG-Ω: Compute owner hash from brain name.
    Returns first 8 bytes of SHA-256(brain_name).
    """
    return hashlib.sha256(brain_name.encode("utf-8")).digest()[:8]
