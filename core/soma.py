"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — SOMA-DB Engine                         ║
║  Layered Neural Graph File — The custom database          ║
║  NRNLANG-Ω: >> STORE / << INVOKE / ->> DEEP_STORE        ║
╚══════════════════════════════════════════════════════════╝

SOMA-DB is a single portable file that IS the database.
No server. No daemon. No port. No network.

5-LAYER STRUCTURE:
  Layer 1 → File Header (64 bytes)
  Layer 2 → Zone Index Table
  Layer 3 → Engram Store (HOT → WARM → COLD → SILENT)
  Layer 4 → Axon Map (connection graph)
  Layer 5 → Integrity Seal (64 bytes)

NMP WRITE PROTOCOL:
  Phase 1 → PREPARE (lock, backup, checksum)
  Phase 2 → WRITE (update all layers)
  Phase 3 → SEAL (SHA-256 integrity)
  Phase 4 → VERIFY (re-read and compare)
"""

import json
import os
import time
import zlib
import shutil
import logging
from pathlib import Path
from typing import Optional

from core.node import (
    Engram, ZONE_HOT, ZONE_WARM, ZONE_COLD, ZONE_SILENT, ZONE_ANCHOR,
)
from core.integrity import (
    build_header, parse_header, build_seal, parse_seal,
    compute_checksum, verify_checksum, HEADER_SIZE, SEAL_SIZE,
)

logger = logging.getLogger("NEURONX.SOMA")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AXON RECORD — stored in Layer 4
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AXON_TYPE_TIME = 0
AXON_TYPE_WORD = 1
AXON_TYPE_EMOTION = 2
AXON_TYPE_CLASH = 3
AXON_TYPE_REINFORCE = 4
AXON_TYPE_HERALD = 5


class AxonRecord:
    """
    NRNLANG-Ω: AXON — A bond/connection linking two engrams.
    """

    def __init__(
        self,
        from_id: str,
        to_id: str,
        synapse: float = 0.0,
        born: float = 0.0,
        reinforced: float = 0.0,
        axon_type: int = AXON_TYPE_WORD,
        direction: str = "BIDIRECTIONAL",
    ):
        self.from_id = from_id
        self.to_id = to_id
        self.synapse = synapse
        self.born = born or time.time()
        self.reinforced = reinforced or time.time()
        self.axon_type = axon_type
        self.direction = direction

    def to_dict(self) -> dict:
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "synapse": self.synapse,
            "born": self.born,
            "reinforced": self.reinforced,
            "axon_type": self.axon_type,
            "direction": self.direction,
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
            direction=data.get("direction", "BIDIRECTIONAL"),
        )

    def __repr__(self) -> str:
        types = {0: "TIME", 1: "WORD", 2: "EMO", 3: "CLASH", 4: "REINF", 5: "HERALD"}
        return (
            f"AXON {self.from_id[:8]}…⟷{self.to_id[:8]}… "
            f"syn={self.synapse:.3f} type={types.get(self.axon_type, '?')}"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOMA-DB ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SomaDB:
    """
    NRNLANG-Ω: SOMA — The brain file. Contains all engrams forever.

    A Layered Neural Graph File that manages the complete lifecycle
    of memories, connections, and integrity verification.
    """

    def __init__(self, filepath: str):
        """
        Initialize SOMA-DB engine.

        Args:
            filepath: Path to the .soma file (created if doesn't exist)
        """
        self.filepath = filepath
        self.lock_path = filepath + ".nrnlock"
        self.backup_path = filepath + ".bak"
        self.sig_path = filepath + ".sig"
        self.log_path = filepath.replace(".soma", ".nrnlog")

        # In-memory state
        self.engrams: dict[str, Engram] = {}        # id → Engram
        self.axons: list[AxonRecord] = []            # all connections
        self.created_at: float = time.time()
        self.modified_at: float = time.time()
        self.save_count: int = 0

        # Ensure directories exist
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        log_dir = os.path.dirname(self.log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Zone Helpers
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _zone_engrams(self, zone: str) -> list[Engram]:
        """Get all engrams in a specific zone."""
        return [e for e in self.engrams.values() if e.zone == zone]

    @property
    def hot_engrams(self) -> list[Engram]:
        return self._zone_engrams(ZONE_HOT) + self._zone_engrams(ZONE_ANCHOR)

    @property
    def warm_engrams(self) -> list[Engram]:
        return self._zone_engrams(ZONE_WARM)

    @property
    def cold_engrams(self) -> list[Engram]:
        return self._zone_engrams(ZONE_COLD)

    @property
    def silent_engrams(self) -> list[Engram]:
        return self._zone_engrams(ZONE_SILENT)

    @property
    def active_engrams(self) -> list[Engram]:
        """All engrams with truth state ACTIVE."""
        return [e for e in self.engrams.values() if e.is_active]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ENGRAM Operations
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def add_engram(self, engram: Engram):
        """
        NRNLANG-Ω: ⊕ ENGRAM_FORGE >> SOMA
        Add a new engram to the brain.
        """
        self.engrams[engram.id] = engram
        logger.debug(f"⊕ FORGE {engram}")

    def get_engram(self, engram_id: str) -> Optional[Engram]:
        """
        NRNLANG-Ω: << INVOKE — retrieve from SOMA
        """
        return self.engrams.get(engram_id)

    def remove_engram(self, engram_id: str) -> bool:
        """Remove engram by ID. Returns True if found and removed."""
        if engram_id in self.engrams:
            del self.engrams[engram_id]
            # Also remove related axons
            self.axons = [
                a for a in self.axons
                if a.from_id != engram_id and a.to_id != engram_id
            ]
            return True
        return False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AXON Operations
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def add_axon(self, axon: AxonRecord):
        """Add a new axon (bond) between two engrams."""
        # Check if axon already exists
        for existing in self.axons:
            if (existing.from_id == axon.from_id and existing.to_id == axon.to_id) or \
               (existing.from_id == axon.to_id and existing.to_id == axon.from_id):
                # Reinforce existing bond
                existing.synapse = min(1.0, existing.synapse + 0.05)
                existing.reinforced = time.time()
                return

        self.axons.append(axon)
        logger.debug(f"WEAVE {axon}")

    def get_axons_for(self, engram_id: str) -> list[AxonRecord]:
        """Get all axons connected to a specific engram."""
        return [
            a for a in self.axons
            if a.from_id == engram_id or a.to_id == engram_id
        ]

    def prune_weak_axons(self, threshold: float = 0.05):
        """
        NRNLANG-Ω: PRUNE — remove axons weaker than threshold.
        axon -x- SEVERED
        """
        before = len(self.axons)
        self.axons = [a for a in self.axons if a.synapse >= threshold]
        pruned = before - len(self.axons)
        if pruned > 0:
            logger.info(f"PRUNE -x- {pruned} axons severed (below {threshold})")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # NMP WRITE PROTOCOL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _nmp_log(self, message: str):
        """Write to the NMP protocol log."""
        try:
            with open(self.log_path, "a") as f:
                ts = time.strftime("%Y.%m.%d:%H:%M:%S")
                f.write(f"T[{ts}] {message}\n")
        except Exception:
            pass

    def _phase1_prepare(self):
        """
        NMP Phase 1 — PREPARE:
        Lock file, snapshot to .bak, log write intention.
        """
        # Create lock file
        with open(self.lock_path, "w") as f:
            f.write(f"LOCKED AT {time.time()}\n")

        # Backup existing file if it exists
        if os.path.exists(self.filepath):
            shutil.copy2(self.filepath, self.backup_path)

        self._nmp_log("PHASE1 PREPARE — file locked, backup created")

    def _phase2_write(self) -> bytes:
        """
        NMP Phase 2 — WRITE:
        Serialize all layers into bytes.
        Returns the complete file content as bytes.
        """
        # Count zones
        hot = self.hot_engrams
        warm = self.warm_engrams
        cold = self.cold_engrams
        silent = self.silent_engrams

        hot_count = len(hot)
        warm_count = len(warm)
        cold_count = len(cold)
        silent_count = len(silent)
        total = len(self.engrams)
        total_axons = len(self.axons)

        self.modified_at = time.time()

        # ── Layer 1: Header ──
        header = build_header(
            total_engrams=total,
            hot_count=hot_count,
            warm_count=warm_count,
            cold_count=cold_count,
            silent_count=silent_count,
            total_axons=total_axons,
            created_at=self.created_at,
            modified_at=self.modified_at,
        )

        # ── Layer 2: Zone Index (JSON) ──
        zone_index = {
            "H": [e.id for e in hot],
            "W": [e.id for e in warm],
            "C": [e.id for e in cold],
            "S": [e.id for e in silent],
        }
        zone_index_json = json.dumps(zone_index).encode("utf-8")
        zone_index_block = len(zone_index_json).to_bytes(4, "big") + zone_index_json

        # ── Layer 3: Engram Store ──
        engram_blocks = b""

        # HOT — no compression
        for e in hot:
            data = json.dumps(e.to_dict()).encode("utf-8")
            eid = e.id.encode("utf-8")
            engram_blocks += (
                len(eid).to_bytes(2, "big") + eid +
                len(data).to_bytes(4, "big") + data
            )

        # WARM — no compression
        for e in warm:
            data = json.dumps(e.to_dict()).encode("utf-8")
            eid = e.id.encode("utf-8")
            engram_blocks += (
                len(eid).to_bytes(2, "big") + eid +
                len(data).to_bytes(4, "big") + data
            )

        # COLD — zlib level 6
        for e in cold:
            data = zlib.compress(json.dumps(e.to_dict()).encode("utf-8"), level=6)
            eid = e.id.encode("utf-8")
            engram_blocks += (
                len(eid).to_bytes(2, "big") + eid +
                len(data).to_bytes(4, "big") + data
            )

        # SILENT — zlib level 9
        for e in silent:
            data = zlib.compress(json.dumps(e.to_dict()).encode("utf-8"), level=9)
            eid = e.id.encode("utf-8")
            engram_blocks += (
                len(eid).to_bytes(2, "big") + eid +
                len(data).to_bytes(4, "big") + data
            )

        engram_store = len(engram_blocks).to_bytes(4, "big") + engram_blocks

        # ── Layer 4: Axon Map ──
        axon_data = json.dumps([a.to_dict() for a in self.axons]).encode("utf-8")
        axon_block = len(axon_data).to_bytes(4, "big") + axon_data

        # Combine layers 1-4
        content = header + zone_index_block + engram_store + axon_block

        self._nmp_log(f"PHASE2 WRITE — {total} engrams, {total_axons} axons, {len(content)} bytes")
        return content

    def _phase3_seal(self, content: bytes) -> bytes:
        """
        NMP Phase 3 — SEAL:
        Compute SHA-256, write integrity seal.
        """
        self.save_count += 1
        data_hash = compute_checksum(content)
        seal = build_seal(data_hash, self.save_count)

        # Save signature file
        try:
            with open(self.sig_path, "w") as f:
                f.write(f"HASH: {data_hash.hex()}\n")
                f.write(f"TIME: {time.time()}\n")
                f.write(f"SAVE: {self.save_count}\n")
        except Exception:
            pass

        self._nmp_log(f"PHASE3 SEAL — SHA-256: {data_hash.hex()[:16]}… save #{self.save_count}")
        return content + seal

    def _phase4_verify(self, full_data: bytes) -> bool:
        """
        NMP Phase 4 — VERIFY:
        Re-read, recompute checksum, compare to seal.
        """
        # Extract content (everything except last 64 bytes) and seal
        content = full_data[:-SEAL_SIZE]
        seal_bytes = full_data[-SEAL_SIZE:]

        # Parse seal and verify
        seal_info = parse_seal(seal_bytes)
        is_valid = verify_checksum(content, seal_info["data_hash"])

        # Remove lock
        if os.path.exists(self.lock_path):
            os.remove(self.lock_path)

        if is_valid:
            self._nmp_log("PHASE4 VERIFY — ✓ integrity confirmed, file unlocked")
        else:
            self._nmp_log("PHASE4 VERIFY — ✗ INTEGRITY FAIL — rolling back to backup")
            # Rollback
            if os.path.exists(self.backup_path):
                shutil.copy2(self.backup_path, self.filepath)

        return is_valid

    def save(self) -> bool:
        """
        NRNLANG-Ω: >> SOMA — Full NMP write protocol.
        Returns True if save succeeded.
        """
        try:
            # Phase 1: Prepare
            self._phase1_prepare()

            # Phase 2: Write
            content = self._phase2_write()

            # Phase 3: Seal
            full_data = self._phase3_seal(content)

            # Write to disk
            with open(self.filepath, "wb") as f:
                f.write(full_data)

            # Phase 4: Verify
            with open(self.filepath, "rb") as f:
                written_data = f.read()

            success = self._phase4_verify(written_data)

            if success:
                logger.info(
                    f"SOMA SAVED — {len(self.engrams)} engrams, "
                    f"{len(self.axons)} axons, "
                    f"{len(full_data)} bytes"
                )
            return success

        except Exception as e:
            logger.error(f"SOMA SAVE FAILED: {e}")
            self._nmp_log(f"SAVE FAILED — {e}")

            # Cleanup lock
            if os.path.exists(self.lock_path):
                os.remove(self.lock_path)

            # Rollback
            if os.path.exists(self.backup_path):
                shutil.copy2(self.backup_path, self.filepath)

            return False

    def load(self) -> bool:
        """
        NRNLANG-Ω: << INVOKE — Load brain from SOMA file.
        Returns True if load succeeded.
        """
        if not os.path.exists(self.filepath):
            logger.info("SOMA file not found — starting with empty brain")
            return True

        try:
            with open(self.filepath, "rb") as f:
                full_data = f.read()

            if len(full_data) < HEADER_SIZE + SEAL_SIZE:
                logger.warning("SOMA file too small — starting fresh")
                return True

            # Extract content and seal
            content = full_data[:-SEAL_SIZE]
            seal_bytes = full_data[-SEAL_SIZE:]

            # Verify integrity
            seal_info = parse_seal(seal_bytes)
            if not verify_checksum(content, seal_info["data_hash"]):
                logger.warning("SOMA integrity check failed — attempting backup restore")
                if os.path.exists(self.backup_path):
                    shutil.copy2(self.backup_path, self.filepath)
                    return self.load()  # Retry with backup
                return False

            self.save_count = seal_info["save_count"]

            # Parse header
            pos = 0
            header_info = parse_header(content[pos:pos + HEADER_SIZE])
            pos += HEADER_SIZE
            self.created_at = header_info["created_at"]
            self.modified_at = header_info["modified_at"]

            total_engrams = header_info["total_engrams"]
            hot_count = header_info["hot_count"]
            warm_count = header_info["warm_count"]
            cold_count = header_info["cold_count"]
            silent_count = header_info["silent_count"]

            # Parse zone index
            zone_index_len = int.from_bytes(content[pos:pos + 4], "big")
            pos += 4
            zone_index = json.loads(content[pos:pos + zone_index_len].decode("utf-8"))
            pos += zone_index_len

            # Determine which engrams need decompression
            cold_ids = set(zone_index.get("C", []))
            silent_ids = set(zone_index.get("S", []))

            # Parse engram store
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

                # Decompress if needed
                if eid in cold_ids or eid in silent_ids:
                    try:
                        raw_data = zlib.decompress(raw_data)
                    except zlib.error:
                        pass  # Already decompressed or invalid

                engram_dict = json.loads(raw_data.decode("utf-8"))
                engram = Engram.from_dict(engram_dict)
                self.engrams[engram.id] = engram

            # Parse axon map
            axon_data_len = int.from_bytes(content[pos:pos + 4], "big")
            pos += 4
            axon_json = content[pos:pos + axon_data_len].decode("utf-8")
            axon_list = json.loads(axon_json)
            self.axons = [AxonRecord.from_dict(a) for a in axon_list]

            logger.info(
                f"SOMA LOADED — {len(self.engrams)} engrams, "
                f"{len(self.axons)} axons, "
                f"save #{self.save_count}"
            )
            return True

        except Exception as e:
            logger.error(f"SOMA LOAD FAILED: {e}")
            # Try backup
            if os.path.exists(self.backup_path):
                logger.info("Attempting restore from backup...")
                shutil.copy2(self.backup_path, self.filepath)
                try:
                    return self.load()
                except Exception:
                    pass
            return False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Statistics
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_stats(self) -> dict:
        """Get brain statistics for reporting."""
        file_size = 0
        if os.path.exists(self.filepath):
            file_size = os.path.getsize(self.filepath)

        return {
            "total_engrams": len(self.engrams),
            "hot_count": len(self.hot_engrams),
            "warm_count": len(self.warm_engrams),
            "cold_count": len(self.cold_engrams),
            "silent_count": len(self.silent_engrams),
            "active_count": len(self.active_engrams),
            "total_axons": len(self.axons),
            "conflict_count": sum(
                1 for e in self.engrams.values() if len(e.contradicts) > 0
            ),
            "anchor_count": sum(
                1 for e in self.engrams.values() if e.is_anchor
            ),
            "file_size_kb": file_size / 1024,
            "save_count": self.save_count,
            "brain_age_days": (time.time() - self.created_at) / 86400,
            "last_saved": time.strftime(
                "%Y.%m.%d %H:%M:%S", time.localtime(self.modified_at)
            ),
        }

    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"SOMA-DB [{stats['total_engrams']} engrams | "
            f"{stats['total_axons']} axons | "
            f"{stats['file_size_kb']:.1f} KB | "
            f"save #{stats['save_count']}]"
        )
