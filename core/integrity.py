"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Integrity Engine                       ║
║  SHA-256 hashing, ID generation, and file verification   ║
║  NRNLANG-Ω: SEAL — the integrity guardian                ║
╚══════════════════════════════════════════════════════════╝
"""

import hashlib
import uuid
import time
import struct


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAGIC SIGNATURE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOMA_MAGIC = b"NRN\xce\xa9"  # "NRNΩ" — 4-byte magic signature (Ω = U+03A9, UTF-8: CE A9, but we use 4 bytes total)
SOMA_MAGIC_4 = b"NRN\xce"    # First 4 bytes for file header (we use 4 bytes)
FORMAT_VERSION = 1
HEADER_SIZE = 64
SEAL_SIZE = 64


def generate_engram_id(raw_text: str, timestamp: float = None) -> str:
    """
    NRNLANG-Ω: FORMULA A — ENGRAM ID GENERATION

    id = HASH(raw_text + T[born] + RANDOM_SALT)
    id = TRUNCATE(id, 16_chars)

    SHA-256 → 64 hex chars → take first 16
    Collision probability at 1M engrams: 1 in 18 quadrillion
    """
    if timestamp is None:
        timestamp = time.time()

    salt = uuid.uuid4().hex
    raw_string = f"{raw_text}{timestamp}{salt}"
    full_hash = hashlib.sha256(raw_string.encode("utf-8")).hexdigest()
    return full_hash[:16]


def compute_checksum(data: bytes) -> bytes:
    """
    Compute SHA-256 hash of binary data.
    Used for SOMA-DB integrity seal (Layer 5).
    """
    return hashlib.sha256(data).digest()


def compute_checksum_hex(data: bytes) -> str:
    """Compute SHA-256 hash as hex string."""
    return hashlib.sha256(data).hexdigest()


def verify_checksum(data: bytes, expected_hash: bytes) -> bool:
    """
    NRNLANG-Ω: VERIFY — re-read, recompute, compare to seal.
    Returns True if data integrity is valid.
    """
    actual = compute_checksum(data)
    return actual == expected_hash


def build_header(
    total_engrams: int,
    hot_count: int,
    warm_count: int,
    cold_count: int,
    silent_count: int,
    total_axons: int,
    created_at: float,
    modified_at: float,
    owner_fingerprint: bytes = b"\x00" * 8,
    compression_flag: int = 1,
) -> bytes:
    """
    Build the 64-byte SOMA-DB file header (Layer 1).

    Layout:
      Bytes 0-3   : Magic signature "NRNΩ" (4 bytes)
      Bytes 4-5   : Format version (2 bytes)
      Bytes 6-9   : Total engram count (4 bytes)
      Bytes 10-13 : HOT zone count (4 bytes)
      Bytes 14-17 : WARM zone count (4 bytes)
      Bytes 18-21 : COLD zone count (4 bytes)
      Bytes 22-25 : SILENT zone count (4 bytes)
      Bytes 26-29 : Total axon count (4 bytes)
      Bytes 30-37 : Creation timestamp (8 bytes, double)
      Bytes 38-45 : Last modification timestamp (8 bytes, double)
      Bytes 46-53 : Owner fingerprint (8 bytes)
      Bytes 54-57 : Compression flag (4 bytes)
      Bytes 58-61 : Reserved (4 bytes)
      Bytes 62-63 : Header checksum (2 bytes)
    """
    # Pack everything except the final 2-byte checksum
    header_data = struct.pack(
        ">4sH IIII II dd 8s I 4s",
        SOMA_MAGIC_4,           # 4 bytes magic
        FORMAT_VERSION,         # 2 bytes version
        total_engrams,          # 4 bytes
        hot_count,              # 4 bytes
        warm_count,             # 4 bytes
        cold_count,             # 4 bytes
        silent_count,           # 4 bytes
        total_axons,            # 4 bytes
        created_at,             # 8 bytes
        modified_at,            # 8 bytes
        owner_fingerprint,      # 8 bytes
        compression_flag,       # 4 bytes
        b"\x00" * 4,            # 4 bytes reserved
    )

    # Header should be 62 bytes before checksum
    # Pad if needed
    header_data = header_data[:62].ljust(62, b"\x00")

    # Compute 2-byte checksum (first 2 bytes of SHA-256)
    checksum = compute_checksum(header_data)[:2]

    return header_data + checksum


def parse_header(header_bytes: bytes) -> dict:
    """
    Parse a 64-byte SOMA-DB header back into its components.
    """
    if len(header_bytes) < HEADER_SIZE:
        raise ValueError(f"Header too short: {len(header_bytes)} bytes (need {HEADER_SIZE})")

    # Verify magic
    magic = header_bytes[:4]
    if magic != SOMA_MAGIC_4:
        raise ValueError(f"Invalid SOMA magic: {magic!r} (expected {SOMA_MAGIC_4!r})")

    # Verify header checksum
    stored_checksum = header_bytes[62:64]
    computed_checksum = compute_checksum(header_bytes[:62])[:2]
    if stored_checksum != computed_checksum:
        raise ValueError("Header checksum mismatch — file may be corrupted")

    # Unpack fields
    version = struct.unpack(">H", header_bytes[4:6])[0]
    total_engrams = struct.unpack(">I", header_bytes[6:10])[0]
    hot_count = struct.unpack(">I", header_bytes[10:14])[0]
    warm_count = struct.unpack(">I", header_bytes[14:18])[0]
    cold_count = struct.unpack(">I", header_bytes[18:22])[0]
    silent_count = struct.unpack(">I", header_bytes[22:26])[0]
    total_axons = struct.unpack(">I", header_bytes[26:30])[0]
    created_at = struct.unpack(">d", header_bytes[30:38])[0]
    modified_at = struct.unpack(">d", header_bytes[38:46])[0]
    owner_fingerprint = header_bytes[46:54]
    compression_flag = struct.unpack(">I", header_bytes[54:58])[0]

    return {
        "version": version,
        "total_engrams": total_engrams,
        "hot_count": hot_count,
        "warm_count": warm_count,
        "cold_count": cold_count,
        "silent_count": silent_count,
        "total_axons": total_axons,
        "created_at": created_at,
        "modified_at": modified_at,
        "owner_fingerprint": owner_fingerprint,
        "compression_flag": compression_flag,
    }


def build_seal(data_hash: bytes, save_count: int) -> bytes:
    """
    Build the 64-byte integrity seal (Layer 5).

    Layout:
      Bytes 0-31  : SHA-256 of all previous layers
      Bytes 32-39 : Timestamp of last save (double)
      Bytes 40-47 : Save count (8 bytes, unsigned long long)
      Bytes 48-63 : Reserved for signature extension
    """
    seal = struct.pack(
        ">32s d Q 16s",
        data_hash[:32],         # 32 bytes SHA-256
        time.time(),            # 8 bytes timestamp
        save_count,             # 8 bytes save count
        b"\x00" * 16,           # 16 bytes reserved
    )
    return seal[:SEAL_SIZE].ljust(SEAL_SIZE, b"\x00")


def parse_seal(seal_bytes: bytes) -> dict:
    """Parse a 64-byte integrity seal."""
    if len(seal_bytes) < SEAL_SIZE:
        raise ValueError(f"Seal too short: {len(seal_bytes)} bytes (need {SEAL_SIZE})")

    data_hash = seal_bytes[:32]
    save_timestamp = struct.unpack(">d", seal_bytes[32:40])[0]
    save_count = struct.unpack(">Q", seal_bytes[40:48])[0]

    return {
        "data_hash": data_hash,
        "save_timestamp": save_timestamp,
        "save_count": save_count,
    }
