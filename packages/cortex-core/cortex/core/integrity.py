"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Integrity Engine                           ║
║  SHA-256, CMP Lock Protocol, IntegritySeal                   ║
╚══════════════════════════════════════════════════════════════╝

Provides cryptographic integrity guarantees for CORTEX-DB:
  - SHA-256 hashing (bytes, hex, dict, file)
  - Deterministic ID generation for thoughts, sessions, strategies
  - IntegritySeal dataclass for tamper detection
  - CMP Lock (Cortex Memory Protocol) for safe concurrent writes
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

from cortex.config import (
    STALE_LOCK_SECONDS, LOCK_WAIT_SECONDS,
    LOCK_POLL_INTERVAL_MS, CORTEXDB_SEAL_FORMAT,
    CORTEXDB_SEAL_SIZE,
)
from cortex.exceptions import (
    CortexDBLockError, CortexDBCorruptionError,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HASHING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sha256_bytes(data: bytes) -> bytes:
    """Return raw SHA-256 digest (32 bytes)."""
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes) -> str:
    """Return hex SHA-256 digest (64 chars)."""
    return hashlib.sha256(data).hexdigest()


def sha256_str(text: str) -> str:
    """Hash a string with SHA-256, return hex."""
    return sha256_hex(text.encode("utf-8"))


def sha256_dict(d: Dict[str, Any]) -> str:
    """Hash a dictionary deterministically (sorted keys, JSON encoded)."""
    canonical = json.dumps(d, sort_keys=True, default=str)
    return sha256_str(canonical)


def sha256_file(path: str) -> str:
    """Hash an entire file with SHA-256, return hex."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ID GENERATORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_id(prefix: str, *parts: str) -> str:
    """Generate a 32-char hex ID from prefix + parts + timestamp."""
    raw = f"{prefix}:{':'.join(str(p) for p in parts)}:{time.time()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def thought_id(content: str, context: str = "") -> str:
    """Generate a unique thought ID."""
    return generate_id("thought", content, context)


def session_id(brain_name: str = "") -> str:
    """Generate a unique session ID."""
    return generate_id("session", brain_name, str(os.getpid()))


def strategy_id(task_type: str, approach: str = "") -> str:
    """Generate a unique strategy ID."""
    return generate_id("strategy", task_type, approach)


def pattern_id(error_type: str, context_type: str = "") -> str:
    """Generate a unique pattern ID."""
    return generate_id("pattern", error_type, context_type)


def brain_id(name: str) -> str:
    """Generate a unique brain ID."""
    return generate_id("brain", name)


def wisdom_id(content: str, domain: str = "") -> str:
    """Generate a unique wisdom ID."""
    return generate_id("wisdom", content, domain)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTEGRITY SEAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class IntegritySeal:
    """Cryptographic seal for .cortex file integrity.

    Stored as last 64 bytes of the file.
    Layout: sha256(32) + timestamp(8) + node_count(8) + version(16)
    """
    sha256_hash: bytes       # 32-byte raw digest
    timestamp: float         # when seal was created
    node_count: int          # number of thoughts at seal time
    version: str             # cortex version string (max 16 chars)

    def pack(self) -> bytes:
        """Serialize to binary (CORTEXDB_SEAL_SIZE bytes)."""
        ver = self.version.encode("utf-8")[:16].ljust(16, b'\x00')
        return struct.pack(
            CORTEXDB_SEAL_FORMAT,
            self.sha256_hash,
            self.timestamp,
            self.node_count,
            ver,
        )

    @classmethod
    def unpack(cls, data: bytes) -> "IntegritySeal":
        """Deserialize from binary."""
        if len(data) != CORTEXDB_SEAL_SIZE:
            raise CortexDBCorruptionError(
                f"Seal must be {CORTEXDB_SEAL_SIZE} bytes, got {len(data)}"
            )
        sha256_hash, ts, count, ver_bytes = struct.unpack(
            CORTEXDB_SEAL_FORMAT, data
        )
        version = ver_bytes.rstrip(b'\x00').decode("utf-8", errors="replace")
        return cls(
            sha256_hash=sha256_hash,
            timestamp=ts,
            node_count=count,
            version=version,
        )

    def verify(self, data: bytes) -> bool:
        """Verify that data matches this seal's SHA-256."""
        return sha256_bytes(data) == self.sha256_hash

    @classmethod
    def create(cls, data: bytes, node_count: int, version: str = "1.0.0") -> "IntegritySeal":
        """Create a new seal for the given data."""
        return cls(
            sha256_hash=sha256_bytes(data),
            timestamp=time.time(),
            node_count=node_count,
            version=version,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CMP LOCK — Cortex Memory Protocol
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CMPLock:
    """File-based lock for safe concurrent .cortex writes.

    CMP (Cortex Memory Protocol) — 4-phase safe write:
      1. PREPARE → acquire lock, create backup
      2. WRITE → serialize all layers
      3. SEAL → compute integrity seal
      4. VERIFY → verify seal, release lock
    """

    def __init__(self, cortex_path: str):
        self.cortex_path = cortex_path
        self.lock_path = cortex_path + ".lock"
        self.backup_path = cortex_path + ".bak"
        self._held = False

    @property
    def is_locked(self) -> bool:
        """Check if the lock file exists."""
        return os.path.exists(self.lock_path)

    @property
    def is_stale(self) -> bool:
        """Check if an existing lock is stale (older than threshold)."""
        if not self.is_locked:
            return False
        try:
            mtime = os.path.getmtime(self.lock_path)
            return (time.time() - mtime) > STALE_LOCK_SECONDS
        except OSError:
            return True

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire the lock. Returns True on success.

        - Waits up to timeout seconds (default: LOCK_WAIT_SECONDS)
        - Breaks stale locks automatically
        """
        timeout = timeout if timeout is not None else LOCK_WAIT_SECONDS
        deadline = time.time() + timeout

        while True:
            # Try to create lock atomically
            if not self.is_locked:
                try:
                    fd = os.open(
                        self.lock_path,
                        os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    )
                    os.write(fd, str(os.getpid()).encode())
                    os.close(fd)
                    self._held = True
                    return True
                except FileExistsError:
                    pass

            # Check for stale lock
            if self.is_stale:
                self._break_stale()
                continue

            # Check timeout
            if time.time() >= deadline:
                raise CortexDBLockError(
                    f"Failed to acquire lock on {self.cortex_path} "
                    f"within {timeout}s"
                )

            # Wait briefly
            time.sleep(LOCK_POLL_INTERVAL_MS / 1000.0)

    def release(self) -> None:
        """Release the lock."""
        if self._held and os.path.exists(self.lock_path):
            try:
                os.unlink(self.lock_path)
            except OSError:
                pass
        self._held = False

    def create_backup(self) -> Optional[str]:
        """Create a backup of the .cortex file before writing.

        Returns the backup path, or None if source doesn't exist.
        """
        if not os.path.exists(self.cortex_path):
            return None
        import shutil
        shutil.copy2(self.cortex_path, self.backup_path)
        return self.backup_path

    def restore_backup(self) -> bool:
        """Restore from backup if write failed."""
        if os.path.exists(self.backup_path):
            import shutil
            shutil.copy2(self.backup_path, self.cortex_path)
            return True
        return False

    def cleanup_backup(self) -> None:
        """Remove backup file after successful write."""
        if os.path.exists(self.backup_path):
            try:
                os.unlink(self.backup_path)
            except OSError:
                pass

    def _break_stale(self) -> None:
        """Break a stale lock."""
        try:
            os.unlink(self.lock_path)
        except OSError:
            pass

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False  # don't suppress exceptions
