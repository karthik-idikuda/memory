"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — CAUSADB Storage Engine                   ║
║  CAULANG-Ω: CAUSADB — the causal brain's file system     ║
╚══════════════════════════════════════════════════════════╝

CAUSADB is a custom 6-layer binary format for storing causal
reasoning graphs. Extension: .sigma

Sister to NEURON-X SOMA-DB (.soma) — same philosophy,
causal domain.

Layers:
 1. Header          — magic bytes, version, counts, timestamps
 2. Zone Index      — zone → node ID mapping
 3. CauseNode Store — JSON-serialized node data (zlib compressed)
 4. Causal Graph Map — edge entries (source → target, weight, type)
 5. Prediction Log  — prediction entries
 6. Integrity Seal  — SHA-256 seal over layers 2-5

NMP Write Protocol:
 1. PREPARE — lock, backup
 2. WRITE   — serialize all layers
 3. SEAL    — compute integrity seal
 4. VERIFY  — verify seal, unlock
"""

from __future__ import annotations

import json
import os
import struct
import time
import zlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sigmax.config import (
    CAUSADB_MAGIC,
    CAUSADB_VERSION,
    CAUSADB_EXTENSION,
    CAUSADB_HEADER_SIZE,
    CAUSADB_EDGE_FORMAT,
    CAUSADB_EDGE_SIZE,
    CAUSADB_PRED_FORMAT,
    CAUSADB_PRED_SIZE,
    CAUSADB_SEAL_SIZE,
    ZONE_ACTIVE, ZONE_WARM, ZONE_DORMANT, ZONE_AXIOM, ZONE_ARCHIVED,
)
from sigmax.core.causenode import CauseNode
from sigmax.core.integrity import (
    IntegritySeal,
    NMPLock,
    sha256_bytes,
    write_signature_file,
)
from sigmax.exceptions import (
    CausaDBError,
    CausaDBCorruptionError,
    CausaDBVersionError,
    CausaDBWriteError,
    CausaDBLockError,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAUSADB FILE MANAGER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CausaDB:
    """
    CAUSADB — 6-layer binary storage for causal reasoning.

    Public API:
     - save(path, nodes, edges, predictions) — full NMP write
     - load(path) → (nodes, edges, predictions) — read and verify
     - verify(path) → bool — integrity check only
     - get_info(path) → dict — read header without full load
    """

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SAVE (NMP Write Protocol)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def save(
        path: str,
        nodes: List[CauseNode],
        edges: Optional[List[Dict]] = None,
        predictions: Optional[List[Dict]] = None,
        brain_id: str = "",
    ) -> None:
        """
        Save causal data using NMP protocol.

        Phase 1: PREPARE — acquire lock, create backup
        Phase 2: WRITE  — serialize 6 layers
        Phase 3: SEAL   — compute integrity seal
        Phase 4: VERIFY — verify seal, release lock
        """
        if edges is None:
            edges = []
        if predictions is None:
            predictions = []

        # Ensure directory exists
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)

        lock = NMPLock(path)

        with lock:
            # Phase 1: PREPARE
            lock.create_backup()
            lock._log("NMP", "Phase 1: PREPARE complete")

            # Phase 2: WRITE
            try:
                raw_data = CausaDB._serialize(nodes, edges, predictions, brain_id)
                lock._log("NMP", f"Phase 2: WRITE serialized {len(raw_data)} bytes")
            except Exception as e:
                raise CausaDBWriteError(f"Serialization failed: {e}")

            # Phase 3: SEAL
            try:
                # Compute seal over all data after header
                seal_data = raw_data[CAUSADB_HEADER_SIZE:]
                seal = IntegritySeal.create(seal_data, len(nodes))
                full_data = raw_data + seal.pack()
                lock._log("NMP", f"Phase 3: SEAL computed ({len(nodes)} nodes)")
            except Exception as e:
                raise CausaDBWriteError(f"Seal computation failed: {e}")

            # Write to file
            try:
                with open(path, 'wb') as f:
                    f.write(full_data)
            except OSError as e:
                raise CausaDBWriteError(f"File write failed: {e}")

            # Phase 4: VERIFY
            try:
                # Re-read and verify
                with open(path, 'rb') as f:
                    written = f.read()

                if len(written) < CAUSADB_HEADER_SIZE + CAUSADB_SEAL_SIZE:
                    raise CausaDBCorruptionError("Written file too small")

                # Verify magic bytes
                magic = written[:4]
                if magic != CAUSADB_MAGIC:
                    raise CausaDBCorruptionError(
                        f"Magic bytes mismatch: expected {CAUSADB_MAGIC!r}, got {magic!r}"
                    )

                # Verify seal
                seal_bytes = written[-CAUSADB_SEAL_SIZE:]
                read_seal = IntegritySeal.unpack(seal_bytes)
                body = written[CAUSADB_HEADER_SIZE:-CAUSADB_SEAL_SIZE]
                if not read_seal.verify(body):
                    raise CausaDBCorruptionError("Post-write seal verification failed")

                lock._log("NMP", "Phase 4: VERIFY passed")

            except CausaDBError:
                raise
            except Exception as e:
                raise CausaDBWriteError(f"Verification failed: {e}")

            # Write companion signature file
            try:
                write_signature_file(path, seal)
            except OSError:
                pass  # sig file is optional

            lock._log("NMP", f"COMPLETE — {len(nodes)} nodes, {len(edges)} edges, "
                             f"{len(predictions)} predictions")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # LOAD
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def load(path: str) -> Tuple[List[CauseNode], List[Dict], List[Dict]]:
        """
        Load causal data from a .sigma file.
        Returns: (nodes, edges, predictions)
        Verifies integrity seal before returning data.
        """
        if not os.path.exists(path):
            return [], [], []

        with open(path, 'rb') as f:
            data = f.read()

        if len(data) < CAUSADB_HEADER_SIZE + CAUSADB_SEAL_SIZE:
            raise CausaDBCorruptionError(
                f"File too small: {len(data)} bytes "
                f"(min: {CAUSADB_HEADER_SIZE + CAUSADB_SEAL_SIZE})"
            )

        # Layer 1: Header
        header = CausaDB._parse_header(data[:CAUSADB_HEADER_SIZE])

        # Verify magic
        if header['magic'] != CAUSADB_MAGIC:
            raise CausaDBCorruptionError(
                f"Invalid magic bytes: {header['magic']!r}"
            )

        # Verify version
        if header['version'] > CAUSADB_VERSION:
            raise CausaDBVersionError(
                f"Unsupported version: {header['version']} "
                f"(max supported: {CAUSADB_VERSION})"
            )

        # Layer 6: Verify integrity seal
        seal_bytes = data[-CAUSADB_SEAL_SIZE:]
        seal = IntegritySeal.unpack(seal_bytes)
        body = data[CAUSADB_HEADER_SIZE:-CAUSADB_SEAL_SIZE]

        if not seal.verify(body):
            raise CausaDBCorruptionError(
                "Integrity seal verification failed — data may be corrupted"
            )

        # Deserialize body
        nodes, edges, predictions = CausaDB._deserialize_body(body, header)

        return nodes, edges, predictions

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # VERIFY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def verify(path: str) -> bool:
        """Quick integrity check without full deserialization."""
        try:
            if not os.path.exists(path):
                return False

            with open(path, 'rb') as f:
                data = f.read()

            if len(data) < CAUSADB_HEADER_SIZE + CAUSADB_SEAL_SIZE:
                return False

            # Check magic
            if data[:4] != CAUSADB_MAGIC:
                return False

            # Verify seal
            seal_bytes = data[-CAUSADB_SEAL_SIZE:]
            seal = IntegritySeal.unpack(seal_bytes)
            body = data[CAUSADB_HEADER_SIZE:-CAUSADB_SEAL_SIZE]

            return seal.verify(body)

        except Exception:
            return False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # INFO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def get_info(path: str) -> Dict[str, Any]:
        """Read header info without loading full data."""
        if not os.path.exists(path):
            return {}

        with open(path, 'rb') as f:
            header_data = f.read(CAUSADB_HEADER_SIZE)

        if len(header_data) < CAUSADB_HEADER_SIZE:
            return {}

        header = CausaDB._parse_header(header_data)

        file_size = os.path.getsize(path)
        return {
            'magic_valid': header['magic'] == CAUSADB_MAGIC,
            'version': header['version'],
            'node_count': header['node_count'],
            'edge_count': header['edge_count'],
            'prediction_count': header['prediction_count'],
            'created_at': header['created_at'],
            'modified_at': header['modified_at'],
            'file_size_bytes': file_size,
            'file_path': path,
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # INTERNAL: SERIALIZATION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def _serialize(
        nodes: List[CauseNode],
        edges: List[Dict],
        predictions: List[Dict],
        brain_id: str = "",
    ) -> bytes:
        """Serialize all 5 data layers (header + body, no seal yet)."""

        # ── Layer 2: Zone Index ──
        zone_index = {}
        for node in nodes:
            zone = node.zone or ZONE_ACTIVE
            if zone not in zone_index:
                zone_index[zone] = []
            zone_index[zone].append(node.id)

        zone_data = json.dumps(zone_index).encode('utf-8')
        zone_compressed = zlib.compress(zone_data, level=6)

        # ── Layer 3: CauseNode Store ──
        nodes_list = [n.to_dict() for n in nodes]
        nodes_json = json.dumps(nodes_list, default=str).encode('utf-8')
        nodes_compressed = zlib.compress(nodes_json, level=6)

        # ── Layer 4: Causal Graph Map ──
        edges_json = json.dumps(edges, default=str).encode('utf-8')
        edges_compressed = zlib.compress(edges_json, level=6)

        # ── Layer 5: Prediction Log ──
        pred_json = json.dumps(predictions, default=str).encode('utf-8')
        pred_compressed = zlib.compress(pred_json, level=6)

        # ── Layer 1: Header ──
        now = time.time()
        brain_id_bytes = brain_id.encode('utf-8')[:8].ljust(8, b'\x00')
        reserved = b'\x00' * 4

        # Compute offsets
        # After header: zone_index | nodes | edges | predictions
        zone_offset = CAUSADB_HEADER_SIZE
        zone_size = len(zone_compressed)
        nodes_offset = zone_offset + zone_size
        nodes_size = len(nodes_compressed)
        edges_offset = nodes_offset + nodes_size
        edges_size = len(edges_compressed)
        pred_offset = edges_offset + edges_size
        pred_size = len(pred_compressed)

        header = struct.pack(
            '>4sH'     # magic (4B), version (2B)
            'I'        # node_count (4B)
            'I'        # edge_count (4B)
            'I'        # prediction_count (4B)
            'I'        # zone_offset (4B)
            'I'        # zone_size (4B)
            'I'        # nodes_offset (4B)
            'I'        # nodes_size (4B)
            'd'        # created_at (8B)
            'd'        # modified_at (8B)
            'd'        # reserved_double (8B)
            '8s'       # brain_id (8B)
            'I'        # edges_offset (4B)
            '4s'       # reserved (4B)
            'H'        # flags (2B)
            'I',       # pred_offset (4B)
            CAUSADB_MAGIC,             # magic
            CAUSADB_VERSION,           # version
            len(nodes),                # node_count
            len(edges),                # edge_count
            len(predictions),          # prediction_count
            zone_offset,               # zone_offset
            zone_size,                 # zone_size
            nodes_offset,              # nodes_offset
            nodes_size,                # nodes_size
            now,                       # created_at
            now,                       # modified_at
            0.0,                       # reserved_double
            brain_id_bytes,            # brain_id
            edges_offset,              # edges_offset
            reserved,                  # reserved
            0,                         # flags
            pred_offset,               # pred_offset
        )

        # Combine all layers (seal added separately)
        return header + zone_compressed + nodes_compressed + edges_compressed + pred_compressed

    @staticmethod
    def _parse_header(data: bytes) -> Dict[str, Any]:
        """Parse the 84-byte header."""
        fmt = '>4sHIIIIIIIddd8sI4sHI'
        values = struct.unpack(fmt, data[:CAUSADB_HEADER_SIZE])

        return {
            'magic': values[0],
            'version': values[1],
            'node_count': values[2],
            'edge_count': values[3],
            'prediction_count': values[4],
            'zone_offset': values[5],
            'zone_size': values[6],
            'nodes_offset': values[7],
            'nodes_size': values[8],
            'created_at': values[9],
            'modified_at': values[10],
            'reserved_double': values[11],
            'brain_id': values[12],
            'edges_offset': values[13],
            'reserved': values[14],
            'flags': values[15],
            'pred_offset': values[16],
        }

    @staticmethod
    def _deserialize_body(
        body: bytes,
        header: Dict[str, Any]
    ) -> Tuple[List[CauseNode], List[Dict], List[Dict]]:
        """Deserialize body into nodes, edges, predictions."""

        # The body starts after the header, so offsets are relative
        # Body = zones | nodes | edges | predictions
        zone_start = 0
        zone_end = header['zone_size']
        nodes_start = zone_end
        nodes_end = nodes_start + header['nodes_size']

        # Remaining is edges + predictions
        remaining = body[nodes_end:]

        # ── Layer 3: CauseNode Store ──
        try:
            nodes_compressed = body[nodes_start:nodes_end]
            nodes_json = zlib.decompress(nodes_compressed)
            nodes_list = json.loads(nodes_json)
            nodes = [CauseNode.from_dict(n) for n in nodes_list]
        except (zlib.error, json.JSONDecodeError) as e:
            raise CausaDBCorruptionError(f"Failed to decompress/parse nodes: {e}")

        # ── Layer 4 + 5: edges and predictions from remaining ──
        edges = []
        predictions = []

        if remaining:
            try:
                # We need to figure out where edges end and predictions begin
                # Use the header offsets relative to start of body
                edge_body_start = header['edges_offset'] - CAUSADB_HEADER_SIZE - header['zone_offset']
                pred_body_start = header['pred_offset'] - CAUSADB_HEADER_SIZE - header['zone_offset']

                # Edges section
                if edge_body_start >= 0 and edge_body_start < len(body):
                    edges_compressed = body[edge_body_start:pred_body_start]
                    if edges_compressed:
                        edges_json = zlib.decompress(edges_compressed)
                        edges = json.loads(edges_json)

                # Predictions section
                if pred_body_start >= 0 and pred_body_start < len(body):
                    pred_compressed = body[pred_body_start:]
                    if pred_compressed:
                        pred_json = zlib.decompress(pred_compressed)
                        predictions = json.loads(pred_json)

            except (zlib.error, json.JSONDecodeError):
                # Best-effort: we got nodes at least
                pass

        return nodes, edges, predictions

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UTILITY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def ensure_path(path: str) -> str:
        """Ensure path has .sigma extension."""
        if not path.endswith(CAUSADB_EXTENSION):
            path += CAUSADB_EXTENSION
        return path

    @staticmethod
    def exists(path: str) -> bool:
        """Check if a .sigma file exists."""
        return os.path.exists(path)
