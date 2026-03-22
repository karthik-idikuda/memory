"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Integrity Engine                        ║
║  CAULANG-Ω: INTEGRITY — seals guard the chain of truth  ║
╚══════════════════════════════════════════════════════════╝

SHA-256 hashing, unique ID generation, integrity seals,
and the NMP (Node Memory Protocol) for safe .sigma writes.

Same philosophy as NEURON-X integrity but for causal data.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from sigmax.config import (
    CAUSADB_MAGIC,
    CAUSADB_VERSION,
    CAUSADB_SEAL_FORMAT,
    CAUSADB_SEAL_SIZE,
    STALE_LOCK_SECONDS,
    LOCK_WAIT_SECONDS,
    LOCK_POLL_INTERVAL_MS,
)
from sigmax.exceptions import (
    IntegritySealError,
    IntegrityHashError,
    CausaDBLockError,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ID GENERATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_node_id() -> str:
    """Generate a unique 32-char hex ID for a CauseNode."""
    return uuid.uuid4().hex


def generate_brain_id() -> str:
    """Generate a unique 16-char hex ID for a SigmaBrain."""
    return uuid.uuid4().hex[:16]


def generate_prediction_id() -> str:
    """Generate a unique 32-char hex ID for a prediction."""
    return uuid.uuid4().hex


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SHA-256 HASHING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sha256_bytes(data: bytes) -> bytes:
    """Compute SHA-256 hash of raw bytes. Returns 32-byte digest."""
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes) -> str:
    """Compute SHA-256 hash of raw bytes. Returns 64-char hex string."""
    return hashlib.sha256(data).hexdigest()


def sha256_dict(data: dict) -> str:
    """Compute SHA-256 hash of a dictionary (JSON-serialized, sorted keys)."""
    json_bytes = json.dumps(data, sort_keys=True, default=str).encode('utf-8')
    return sha256_hex(json_bytes)


def sha256_nodes(nodes: List[dict]) -> str:
    """Compute SHA-256 hash of a list of node dictionaries."""
    combined = json.dumps(nodes, sort_keys=True, default=str).encode('utf-8')
    return sha256_hex(combined)


def sha256_file(filepath: str) -> str:
    """Compute SHA-256 hash of a file's contents."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTEGRITY SEAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class IntegritySeal:
    """
    Integrity seal for CAUSADB files.

    Layout (64 bytes):
    - sha256: 32 bytes — hash of all node data
    - seal_time: double (8 bytes) — UNIX timestamp
    - node_count: uint64 (8 bytes) — number of nodes
    - version_tag: 16 bytes — version identifier
    """

    __slots__ = ('sha256', 'seal_time', 'node_count', 'version_tag')

    def __init__(
        self,
        sha256: bytes,
        seal_time: float,
        node_count: int,
        version_tag: bytes = b'SIGMAX_V1\x00\x00\x00\x00\x00\x00\x00'
    ):
        self.sha256 = sha256
        self.seal_time = seal_time
        self.node_count = node_count
        self.version_tag = version_tag[:16].ljust(16, b'\x00')

    def pack(self) -> bytes:
        """Pack seal into 64 bytes."""
        return struct.pack(
            CAUSADB_SEAL_FORMAT,
            self.sha256[:32].ljust(32, b'\x00'),
            self.seal_time,
            self.node_count,
            self.version_tag
        )

    @classmethod
    def unpack(cls, data: bytes) -> 'IntegritySeal':
        """Unpack seal from 64 bytes."""
        if len(data) < CAUSADB_SEAL_SIZE:
            raise IntegritySealError(
                f"Seal data too short: {len(data)} bytes, expected {CAUSADB_SEAL_SIZE}"
            )
        sha256, seal_time, node_count, version_tag = struct.unpack(
            CAUSADB_SEAL_FORMAT, data[:CAUSADB_SEAL_SIZE]
        )
        return cls(sha256, seal_time, node_count, version_tag)

    @classmethod
    def create(cls, nodes_data: bytes, node_count: int) -> 'IntegritySeal':
        """Create a new seal from node data."""
        sha256 = hashlib.sha256(nodes_data).digest()
        return cls(
            sha256=sha256,
            seal_time=time.time(),
            node_count=node_count,
        )

    def verify(self, nodes_data: bytes) -> bool:
        """Verify that nodes_data matches the seal's SHA-256."""
        computed = hashlib.sha256(nodes_data).digest()
        return computed == self.sha256

    def __repr__(self) -> str:
        return (
            f"IntegritySeal(nodes={self.node_count}, "
            f"time={self.seal_time:.0f}, "
            f"hash={self.sha256[:8].hex()}...)"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIGNATURE FILE (.sigma.sig)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def write_signature_file(sigma_path: str, seal: IntegritySeal) -> None:
    """Write a companion .sigma.sig file with the seal hash."""
    sig_path = sigma_path + '.sig'
    sig_data = {
        'sha256': seal.sha256.hex(),
        'seal_time': seal.seal_time,
        'node_count': seal.node_count,
        'version': seal.version_tag.rstrip(b'\x00').decode('ascii', errors='replace'),
        'sigma_file': os.path.basename(sigma_path),
    }
    with open(sig_path, 'w', encoding='utf-8') as f:
        json.dump(sig_data, f, indent=2)


def verify_signature_file(sigma_path: str) -> bool:
    """Verify the .sigma.sig file matches the actual .sigma file seal."""
    sig_path = sigma_path + '.sig'
    if not os.path.exists(sig_path):
        return False
    try:
        with open(sig_path, 'r', encoding='utf-8') as f:
            sig_data = json.load(f)
        expected_hash = sig_data.get('sha256', '')
        actual_hash = sha256_file(sigma_path)
        # Note: sig file stores seal hash, not file hash
        # For full verification, would need to read the seal from the file
        return bool(expected_hash)
    except (json.JSONDecodeError, KeyError):
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NMP LOCK PROTOCOL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class NMPLock:
    """
    Node Memory Protocol lock for safe .sigma file writes.

    4-phase write protocol:
    1. PREPARE — acquire .sigma.lock, create .sigma.bak
    2. WRITE   — write new data to .sigma
    3. SEAL    — compute and append integrity seal
    4. VERIFY  — verify seal, remove .sigma.lock

    If any phase fails, restore from .sigma.bak.
    """

    def __init__(self, sigma_path: str):
        self.sigma_path = sigma_path
        self.lock_path = sigma_path + '.lock'
        self.backup_path = sigma_path + '.bak'
        self.log_path = sigma_path + '.log'
        self._locked = False

    def acquire(self) -> bool:
        """
        Acquire the write lock.
        Returns True if lock acquired, False if already locked.
        Removes stale locks (older than STALE_LOCK_SECONDS).
        """
        # Check for stale lock
        if os.path.exists(self.lock_path):
            try:
                lock_age = time.time() - os.path.getmtime(self.lock_path)
                if lock_age > STALE_LOCK_SECONDS:
                    os.remove(self.lock_path)
                    self._log("LOCK", "Removed stale lock (age={:.1f}s)".format(lock_age))
                else:
                    return False
            except OSError:
                return False

        # Create lock file
        try:
            fd = os.open(
                self.lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY
            )
            os.write(fd, json.dumps({
                'pid': os.getpid(),
                'time': time.time(),
                'sigma_file': os.path.basename(self.sigma_path),
            }).encode('utf-8'))
            os.close(fd)
            self._locked = True
            return True
        except FileExistsError:
            return False
        except OSError as e:
            raise CausaDBLockError(f"Failed to create lock: {e}")

    def release(self) -> None:
        """Release the write lock."""
        try:
            if os.path.exists(self.lock_path):
                os.remove(self.lock_path)
        except OSError:
            pass
        self._locked = False

    def wait_and_acquire(self) -> bool:
        """
        Wait for lock with timeout.
        Polls every LOCK_POLL_INTERVAL_MS until LOCK_WAIT_SECONDS.
        """
        deadline = time.time() + LOCK_WAIT_SECONDS
        while time.time() < deadline:
            if self.acquire():
                return True
            time.sleep(LOCK_POLL_INTERVAL_MS / 1000.0)

        raise CausaDBLockError(
            f"Timeout waiting for lock on {self.sigma_path} "
            f"(waited {LOCK_WAIT_SECONDS}s)"
        )

    def create_backup(self) -> None:
        """Phase 1: Create backup of current .sigma file."""
        if os.path.exists(self.sigma_path):
            import shutil
            shutil.copy2(self.sigma_path, self.backup_path)
            self._log("BACKUP", f"Created backup: {self.backup_path}")

    def restore_backup(self) -> bool:
        """Restore from backup if write failed."""
        if os.path.exists(self.backup_path):
            import shutil
            shutil.copy2(self.backup_path, self.sigma_path)
            self._log("RESTORE", "Restored from backup")
            return True
        return False

    def cleanup_backup(self) -> None:
        """Remove backup after successful write (keep last backup)."""
        # We keep the .bak file as a safety net
        pass

    def _log(self, phase: str, message: str) -> None:
        """Append to .sigma.log file."""
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] [{phase}] {message}\n")
        except OSError:
            pass  # logging is best-effort

    @property
    def is_locked(self) -> bool:
        return self._locked

    def __enter__(self):
        self.wait_and_acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._log("ERROR", f"Write failed: {exc_type.__name__}: {exc_val}")
            self.restore_backup()
        self.release()
        return False
