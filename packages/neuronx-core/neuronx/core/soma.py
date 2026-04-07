"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — SOMA-DB Engine                         ║
║  NRNLANG-Ω: >> STORE / << INVOKE / ->> DEEP_STORE       ║
║  5-Layer Binary Neural Graph File                        ║
╚══════════════════════════════════════════════════════════╝

SOMA-DB is a single portable file that IS the database.
No server. No daemon. No port. No network.

5-LAYER STRUCTURE:
  Layer 1 → File Header (64 bytes, magic NRN-Ω)
  Layer 2 → Zone Index Table
  Layer 3 → Engram Store (HOT/WARM uncompressed, COLD/SILENT zlib)
  Layer 4 → Axon Map (bond network)
  Layer 5 → Integrity Seal (64 bytes, SHA-256)

NMP 4-PHASE WRITE PROTOCOL:
  Phase 1 → PREPARE (lock, backup)
  Phase 2 → WRITE (serialize all layers)
  Phase 3 → SEAL (SHA-256 + .soma.sig)
  Phase 4 → VERIFY (re-read and compare + .nrnlog)

FIXES:
  BUG-001: True binary format (struct module, not JSON wrapping)
  BUG-004: .soma.bak restore on corruption
  BUG-006: NMP creates .nrnlock, .soma.bak, .soma.sig, .nrnlog
  BUG-020: File lock handling with stale detection
"""

import json
import os
import time
import zlib
import shutil
import logging
from typing import Optional, Dict, List

from neuronx.config import (
    SOMA_MAGIC, SOMA_HEADER_SIZE, SOMA_SEAL_SIZE,
    ZONE_HOT, ZONE_WARM, ZONE_COLD, ZONE_SILENT,
    STALE_LOCK_SECONDS, LOCK_WAIT_SECONDS, LOCK_POLL_INTERVAL_MS,
    AXON_TYPE_WORD, AXON_TYPE_NAMES,
)
from neuronx.core.node import EngramNode
from neuronx.core.integrity import (
    build_header, parse_header, build_seal, parse_seal,
    compute_checksum, verify_checksum, build_owner_hash,
)
from neuronx.exceptions import (
    NeuronXCorruptionError, NeuronXLockTimeoutError,
)

logger = logging.getLogger("NEURONX.SOMA")


class AxonRecord:
    """
    NRNLANG-Ω: AXON — A bond/connection linking two engrams.
    Stored in Layer 4 of SOMA-DB.
    """

    def __init__(
        self,
        from_id: str,
        to_id: str,
        synapse: float = 0.0,
        born: float = 0.0,
        reinforced: float = 0.0,
        axon_type: int = AXON_TYPE_WORD,
    ):
        self.from_id = from_id
        self.to_id = to_id
        self.synapse = synapse
        self.born = born or time.time()
        self.reinforced = reinforced or time.time()
        self.axon_type = axon_type

    def to_dict(self) -> dict:
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "synapse": self.synapse,
            "born": self.born,
            "reinforced": self.reinforced,
            "axon_type": self.axon_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AxonRecord":
        return cls(
            from_id=data.get("from_id", ""),
            to_id=data.get("to_id", ""),
            synapse=data.get("synapse", 0.0),
            born=data.get("born", 0.0),
            reinforced=data.get("reinforced", 0.0),
            axon_type=data.get("axon_type", AXON_TYPE_WORD),
        )

    def __repr__(self) -> str:
        type_name = AXON_TYPE_NAMES.get(self.axon_type, "?")
        return (
            f"AXON {self.from_id[:8]}…⟷{self.to_id[:8]}… "
            f"syn={self.synapse:.3f} type={type_name}"
        )


class SomaDB:
    """
    NRNLANG-Ω: SOMA — The brain file. Contains all engrams forever.

    A 5-layer binary file with SHA-256 integrity protection and
    NMP 4-phase write protocol for data safety.
    """

    def __init__(self, filepath: str, brain_name: str = "default"):
        self.filepath = str(filepath)
        self.brain_name = brain_name
        self.lock_path = self.filepath + ".nrnlock"
        self.backup_path = self.filepath + ".bak"
        self.sig_path = self.filepath + ".sig"

        # Derive log path
        base = self.filepath
        if base.endswith(".soma"):
            base = base[:-5]
        self.log_path = base + ".nrnlog"

        # In-memory state
        self.engrams: Dict[str, EngramNode] = {}
        self.axons: List[AxonRecord] = []
        self.created_at: float = time.time()
        self.modified_at: float = time.time()
        self.save_count: int = 0
        self.owner_hash: bytes = build_owner_hash(brain_name)

        # Ensure directories
        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Zone Helpers
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _zone_engrams(self, zone: str) -> List[EngramNode]:
        return [e for e in self.engrams.values() if e.zone == zone]

    @property
    def hot_engrams(self) -> List[EngramNode]:
        hot = self._zone_engrams(ZONE_HOT)
        anchors = [e for e in self.engrams.values() if e.is_anchor and e.zone != ZONE_HOT]
        return hot + anchors

    @property
    def warm_engrams(self) -> List[EngramNode]:
        return self._zone_engrams(ZONE_WARM)

    @property
    def cold_engrams(self) -> List[EngramNode]:
        return self._zone_engrams(ZONE_COLD)

    @property
    def silent_engrams(self) -> List[EngramNode]:
        return self._zone_engrams(ZONE_SILENT)

    @property
    def active_engrams(self) -> List[EngramNode]:
        return [e for e in self.engrams.values() if e.is_active_engram()]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ENGRAM Operations
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def add_engram(self, engram: EngramNode) -> None:
        """NRNLANG-Ω: ⊕ ENGRAM_FORGE >> SOMA"""
        self.engrams[engram.id] = engram
        logger.debug(f"⊕ FORGE {engram}")

    def get_engram(self, engram_id: str) -> Optional[EngramNode]:
        """NRNLANG-Ω: << INVOKE — retrieve from SOMA"""
        return self.engrams.get(engram_id)

    def remove_engram(self, engram_id: str) -> bool:
        if engram_id in self.engrams:
            del self.engrams[engram_id]
            self.axons = [
                a for a in self.axons
                if a.from_id != engram_id and a.to_id != engram_id
            ]
            return True
        return False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AXON Operations
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def add_axon(self, axon: AxonRecord) -> None:
        for existing in self.axons:
            if (existing.from_id == axon.from_id and existing.to_id == axon.to_id) or \
               (existing.from_id == axon.to_id and existing.to_id == axon.from_id):
                existing.synapse = min(1.0, existing.synapse + 0.05)
                existing.reinforced = time.time()
                return
        self.axons.append(axon)

    def get_axons_for(self, engram_id: str) -> List[AxonRecord]:
        return [a for a in self.axons if a.from_id == engram_id or a.to_id == engram_id]

    def prune_weak_axons(self, threshold: float = 0.05) -> int:
        """NRNLANG-Ω: PRUNE -x- SEVERED"""
        before = len(self.axons)
        self.axons = [a for a in self.axons if a.synapse >= threshold]
        pruned = before - len(self.axons)
        if pruned > 0:
            logger.info(f"PRUNE -x- {pruned} axons severed (below {threshold})")
        return pruned

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FILE LOCK HANDLING (BUG-020 FIX)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _acquire_lock(self) -> None:
        """
        BUG-020 FIX: Proper file lock handling.
        - If .nrnlock exists and is older than 30s: stale, delete and proceed
        - If .nrnlock is fresh: wait up to 5s with 100ms polling
        - If still locked: raise NeuronXLockTimeoutError
        """
        if os.path.exists(self.lock_path):
            lock_age = time.time() - os.path.getmtime(self.lock_path)
            if lock_age > STALE_LOCK_SECONDS:
                logger.warning(f"Stale lock detected ({lock_age:.1f}s old), clearing")
                os.remove(self.lock_path)
            else:
                # Wait for lock release
                wait_end = time.time() + LOCK_WAIT_SECONDS
                while os.path.exists(self.lock_path) and time.time() < wait_end:
                    time.sleep(LOCK_POLL_INTERVAL_MS / 1000.0)
                if os.path.exists(self.lock_path):
                    raise NeuronXLockTimeoutError(
                        f"Could not acquire lock after {LOCK_WAIT_SECONDS}s"
                    )

        # Create lock
        with open(self.lock_path, "w") as f:
            f.write(f"LOCKED AT {time.time()}\nPID: {os.getpid()}\n")

    def _release_lock(self) -> None:
        if os.path.exists(self.lock_path):
            os.remove(self.lock_path)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # NMP 4-PHASE WRITE PROTOCOL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _nmp_log(self, message: str) -> None:
        try:
            log_dir = os.path.dirname(self.log_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            with open(self.log_path, "a") as f:
                ts = time.strftime("%Y.%m.%d:%H:%M:%S")
                f.write(f"T[{ts}] {message}\n")
        except Exception:
            pass

    def _phase1_prepare(self) -> None:
        """NMP Phase 1: Lock file + backup."""
        self._acquire_lock()
        if os.path.exists(self.filepath):
            shutil.copy2(self.filepath, self.backup_path)
        self._nmp_log("PHASE1 PREPARE — file locked, backup created")

    def _phase2_write(self) -> bytes:
        """NMP Phase 2: Serialize all 5 layers into bytes."""
        hot = self.hot_engrams
        warm = self.warm_engrams
        cold = self.cold_engrams
        silent = self.silent_engrams

        self.modified_at = time.time()

        # ── Layer 1: Header (64 bytes) ──
        header = build_header(
            total_engrams=len(self.engrams),
            hot_count=len(hot),
            warm_count=len(warm),
            cold_count=len(cold),
            silent_count=len(silent),
            total_axons=len(self.axons),
            created_at=self.created_at,
            modified_at=self.modified_at,
            owner_hash=self.owner_hash,
        )

        # ── Layer 2: Zone Index ──
        zone_index = {
            "H": [e.id for e in hot],
            "W": [e.id for e in warm],
            "C": [e.id for e in cold],
            "S": [e.id for e in silent],
        }
        zone_json = json.dumps(zone_index).encode("utf-8")
        zone_block = len(zone_json).to_bytes(4, "big") + zone_json

        # ── Layer 3: Engram Store ──
        engram_blocks = b""

        # HOT + WARM — uncompressed
        for e in (hot + warm):
            data = json.dumps(e.to_dict(), ensure_ascii=False, default=str).encode("utf-8")
            eid = e.id.encode("utf-8")
            engram_blocks += (
                len(eid).to_bytes(2, "big") + eid +
                len(data).to_bytes(4, "big") + data
            )

        # COLD — zlib level 6
        for e in cold:
            data = zlib.compress(
                json.dumps(e.to_dict(), ensure_ascii=False, default=str).encode("utf-8"),
                level=6,
            )
            eid = e.id.encode("utf-8")
            engram_blocks += (
                len(eid).to_bytes(2, "big") + eid +
                len(data).to_bytes(4, "big") + data
            )

        # SILENT — zlib level 9
        for e in silent:
            data = zlib.compress(
                json.dumps(e.to_dict(), ensure_ascii=False, default=str).encode("utf-8"),
                level=9,
            )
            eid = e.id.encode("utf-8")
            engram_blocks += (
                len(eid).to_bytes(2, "big") + eid +
                len(data).to_bytes(4, "big") + data
            )

        engram_store = len(engram_blocks).to_bytes(4, "big") + engram_blocks

        # ── Layer 4: Axon Map ──
        axon_json = json.dumps(
            [a.to_dict() for a in self.axons],
            ensure_ascii=False, default=str,
        ).encode("utf-8")
        axon_block = len(axon_json).to_bytes(4, "big") + axon_json

        content = header + zone_block + engram_store + axon_block
        self._nmp_log(
            f"PHASE2 WRITE — {len(self.engrams)} engrams, "
            f"{len(self.axons)} axons, {len(content)} bytes"
        )
        return content

    def _phase3_seal(self, content: bytes) -> bytes:
        """NMP Phase 3: SHA-256 seal + .soma.sig file."""
        self.save_count += 1
        data_hash = compute_checksum(content)
        seal = build_seal(data_hash, self.save_count)

        # Write .soma.sig file (BUG-006 fix)
        try:
            with open(self.sig_path, "w") as f:
                json.dump({
                    "hash": data_hash.hex(),
                    "timestamp": time.time(),
                    "save_count": self.save_count,
                    "engram_count": len(self.engrams),
                    "axon_count": len(self.axons),
                }, f, indent=2)
        except Exception:
            pass

        self._nmp_log(f"PHASE3 SEAL — SHA-256: {data_hash.hex()[:16]}… save #{self.save_count}")
        return content + seal

    def _phase4_verify(self, full_data: bytes) -> bool:
        """NMP Phase 4: Re-read, verify, unlock, log."""
        content = full_data[:-SOMA_SEAL_SIZE]
        seal_bytes = full_data[-SOMA_SEAL_SIZE:]

        seal_info = parse_seal(seal_bytes)
        is_valid = verify_checksum(content, seal_info["data_hash"])

        self._release_lock()

        if is_valid:
            self._nmp_log("PHASE4 VERIFY — ✓ integrity confirmed, file unlocked")
        else:
            self._nmp_log("PHASE4 VERIFY — ✗ INTEGRITY FAIL — rolling back")
            if os.path.exists(self.backup_path):
                shutil.copy2(self.backup_path, self.filepath)

        return is_valid

    def save(self) -> bool:
        """
        NRNLANG-Ω: >> SOMA — Full NMP write protocol.
        Returns True if save succeeded.
        """
        try:
            self._phase1_prepare()
            content = self._phase2_write()
            full_data = self._phase3_seal(content)

            with open(self.filepath, "wb") as f:
                f.write(full_data)

            # Verify
            with open(self.filepath, "rb") as f:
                written_data = f.read()

            success = self._phase4_verify(written_data)
            if success:
                logger.info(
                    f"SOMA SAVED — {len(self.engrams)} engrams, "
                    f"{len(self.axons)} axons, {len(full_data)} bytes"
                )
            return success

        except NeuronXLockTimeoutError:
            raise
        except Exception as e:
            logger.error(f"SOMA SAVE FAILED: {e}")
            self._nmp_log(f"SAVE FAILED — {e}")
            self._release_lock()
            if os.path.exists(self.backup_path):
                shutil.copy2(self.backup_path, self.filepath)
            return False

    def load(self) -> bool:
        """
        NRNLANG-Ω: << INVOKE — Load brain from SOMA file.
        BUG-004 FIX: Auto-restore from .soma.bak on corruption.
        """
        if not os.path.exists(self.filepath):
            logger.info("SOMA file not found — starting with empty brain")
            return True

        try:
            with open(self.filepath, "rb") as f:
                full_data = f.read()

            # BUG-001 FIX: Verify magic bytes
            if len(full_data) < 4 or full_data[:4] != SOMA_MAGIC:
                raise NeuronXCorruptionError(
                    f"Invalid SOMA magic bytes: {full_data[:4]!r}"
                )

            if len(full_data) < SOMA_HEADER_SIZE + SOMA_SEAL_SIZE:
                logger.warning("SOMA file too small — starting fresh")
                return True

            content = full_data[:-SOMA_SEAL_SIZE]
            seal_bytes = full_data[-SOMA_SEAL_SIZE:]

            # Verify integrity
            seal_info = parse_seal(seal_bytes)
            if not verify_checksum(content, seal_info["data_hash"]):
                logger.warning("SOMA integrity check failed — attempting backup restore")
                return self._restore_from_backup()

            self.save_count = seal_info["save_count"]
            return self._parse_content(content)

        except NeuronXCorruptionError:
            logger.error("SOMA file corrupted")
            return self._restore_from_backup()
        except Exception as e:
            logger.error(f"SOMA LOAD FAILED: {e}")
            return self._restore_from_backup()

    def _restore_from_backup(self) -> bool:
        """BUG-004 FIX: Restore from .soma.bak."""
        if not os.path.exists(self.backup_path):
            raise NeuronXCorruptionError(
                "SOMA file corrupted and no backup available"
            )

        logger.info("Restoring from backup...")
        try:
            with open(self.backup_path, "rb") as f:
                bak_data = f.read()

            if len(bak_data) < 4 or bak_data[:4] != SOMA_MAGIC:
                raise NeuronXCorruptionError(
                    "Both SOMA file and backup are corrupted"
                )

            if len(bak_data) < SOMA_HEADER_SIZE + SOMA_SEAL_SIZE:
                raise NeuronXCorruptionError("Backup too small")

            bak_content = bak_data[:-SOMA_SEAL_SIZE]
            bak_seal = bak_data[-SOMA_SEAL_SIZE:]
            bak_info = parse_seal(bak_seal)

            if not verify_checksum(bak_content, bak_info["data_hash"]):
                raise NeuronXCorruptionError(
                    "Both SOMA file and backup are corrupted"
                )

            # Backup is valid — copy to main and load
            shutil.copy2(self.backup_path, self.filepath)
            self.save_count = bak_info["save_count"]
            return self._parse_content(bak_content)

        except NeuronXCorruptionError:
            raise
        except Exception as e:
            raise NeuronXCorruptionError(f"Backup restore failed: {e}")

    def _parse_content(self, content: bytes) -> bool:
        """Parse layers 1-4 from content bytes."""
        pos = 0

        # Layer 1: Header
        header_info = parse_header(content[pos:pos + SOMA_HEADER_SIZE])
        pos += SOMA_HEADER_SIZE
        self.created_at = header_info["created_at"]
        self.modified_at = header_info["modified_at"]

        # Layer 2: Zone Index
        zone_index_len = int.from_bytes(content[pos:pos + 4], "big")
        pos += 4
        zone_index = json.loads(content[pos:pos + zone_index_len].decode("utf-8"))
        pos += zone_index_len

        cold_ids = set(zone_index.get("C", []))
        silent_ids = set(zone_index.get("S", []))

        # Layer 3: Engram Store
        engram_store_len = int.from_bytes(content[pos:pos + 4], "big")
        pos += 4
        engram_end = pos + engram_store_len

        self.engrams = {}
        while pos < engram_end:
            eid_len = int.from_bytes(content[pos:pos + 2], "big")
            pos += 2
            eid = content[pos:pos + eid_len].decode("utf-8")
            pos += eid_len

            data_len = int.from_bytes(content[pos:pos + 4], "big")
            pos += 4
            raw_data = content[pos:pos + data_len]
            pos += data_len

            if eid in cold_ids or eid in silent_ids:
                try:
                    raw_data = zlib.decompress(raw_data)
                except zlib.error:
                    pass

            engram_dict = json.loads(raw_data.decode("utf-8"))
            engram = EngramNode.from_dict(engram_dict)
            self.engrams[engram.id] = engram

        # Layer 4: Axon Map
        axon_data_len = int.from_bytes(content[pos:pos + 4], "big")
        pos += 4
        axon_json = content[pos:pos + axon_data_len].decode("utf-8")
        axon_list = json.loads(axon_json)
        self.axons = [AxonRecord.from_dict(a) for a in axon_list]

        logger.info(
            f"SOMA LOADED — {len(self.engrams)} engrams, "
            f"{len(self.axons)} axons, save #{self.save_count}"
        )
        return True

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Statistics
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_stats(self) -> dict:
        file_size = 0
        if os.path.exists(self.filepath):
            file_size = os.path.getsize(self.filepath)

        confidences = [e.confidence for e in self.engrams.values()]
        weights = [e.weight for e in self.engrams.values()]
        heats = [e.heat for e in self.engrams.values()]

        return {
            "total_engrams": len(self.engrams),
            "hot_count": len(self.hot_engrams),
            "warm_count": len(self.warm_engrams),
            "cold_count": len(self.cold_engrams),
            "silent_count": len(self.silent_engrams),
            "active_count": len(self.active_engrams),
            "total_axons": len(self.axons),
            "anchor_count": sum(1 for e in self.engrams.values() if e.is_anchor),
            "conflict_count": sum(1 for e in self.engrams.values() if len(e.contradicts) > 0),
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
            "avg_weight": sum(weights) / len(weights) if weights else 0.0,
            "avg_heat": sum(heats) / len(heats) if heats else 0.0,
            "soma_size_kb": file_size / 1024,
            "save_count": self.save_count,
            "brain_age_days": (time.time() - self.created_at) / 86400,
        }

    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"SOMA-DB [{stats['total_engrams']} engrams | "
            f"{stats['total_axons']} axons | "
            f"{stats['soma_size_kb']:.1f} KB | "
            f"save #{stats['save_count']}]"
        )
