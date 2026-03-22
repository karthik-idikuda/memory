"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — CORTEX-DB                                  ║
║  8-Layer Custom Binary Storage Format (.cortex)              ║
╚══════════════════════════════════════════════════════════════╝

CORTEX-DB stores the entire metacognitive brain state in one file:

  LAYER 1: HEADER     — Magic, version, counts (fixed size)
  LAYER 2: ZONE_IDX   — Zone → [thought offsets] (variable)
  LAYER 3: THOUGHTS   — zlib-compressed ThoughtNode list
  LAYER 4: EDGES      — parent→child + memory→thought mappings
  LAYER 5: METACOG    — metacognitive state snapshot
  LAYER 6: STRATEGIES — strategy evolution history
  LAYER 7: GROWTH     — growth measurements log
  LAYER 8: SEAL       — SHA-256 integrity seal (fixed size)

Uses CMP (Cortex Memory Protocol) for safe writes.
"""

from __future__ import annotations

import json
import struct
import time
import zlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from cortex.config import (
    CORTEXDB_MAGIC, CORTEXDB_VERSION,
    CORTEXDB_HEADER_FORMAT, CORTEXDB_HEADER_SIZE,
    CORTEXDB_SEAL_SIZE, COMPRESSION_LEVEL,
)
from cortex.exceptions import (
    CortexDBError, CortexDBCorruptionError,
    CortexDBVersionError, CortexDBWriteError,
)
from cortex.core.integrity import (
    IntegritySeal, CMPLock, sha256_bytes,
)
from cortex.core.thought_node import ThoughtNode


class CortexDB:
    """8-layer binary storage for the metacognitive brain.

    File format: .cortex
    One file = one complete brain snapshot.

    Usage:
        db = CortexDB("brain.cortex")
        db.add_thought(thought)
        db.save()
        db = CortexDB.load("brain.cortex")
    """

    def __init__(self, path: str):
        self.path = path
        self.thoughts: Dict[str, ThoughtNode] = {}
        self.edges: Dict[str, List[str]] = {}      # parent_id → [child_ids]
        self.memory_edges: Dict[str, List[str]] = {}  # memory_id → [thought_ids]
        self.metacog_state: Dict[str, Any] = {}
        self.strategies: List[Dict[str, Any]] = []
        self.growth_log: List[Dict[str, Any]] = []
        self.created_at: float = time.time()
        self.modified_at: float = time.time()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # THOUGHT OPERATIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def add_thought(self, thought: ThoughtNode) -> str:
        """Add a ThoughtNode to the database.

        Returns the thought ID.
        """
        self.thoughts[thought.id] = thought

        # Update edge graph
        if thought.parent_id:
            if thought.parent_id not in self.edges:
                self.edges[thought.parent_id] = []
            if thought.id not in self.edges[thought.parent_id]:
                self.edges[thought.parent_id].append(thought.id)

        # Update memory edges
        for mem_id in thought.memory_ids:
            if mem_id not in self.memory_edges:
                self.memory_edges[mem_id] = []
            if thought.id not in self.memory_edges[mem_id]:
                self.memory_edges[mem_id].append(thought.id)

        self.modified_at = time.time()
        return thought.id

    def get_thought(self, thought_id: str) -> Optional[ThoughtNode]:
        """Retrieve a ThoughtNode by ID."""
        thought = self.thoughts.get(thought_id)
        if thought:
            thought.touch()
        return thought

    def delete_thought(self, thought_id: str) -> bool:
        """Remove a ThoughtNode from the database."""
        if thought_id not in self.thoughts:
            return False

        thought = self.thoughts.pop(thought_id)

        # Clean up edges
        if thought.parent_id and thought.parent_id in self.edges:
            try:
                self.edges[thought.parent_id].remove(thought_id)
            except ValueError:
                pass

        # Clean up memory edges
        for mem_id in thought.memory_ids:
            if mem_id in self.memory_edges:
                try:
                    self.memory_edges[mem_id].remove(thought_id)
                except ValueError:
                    pass

        self.modified_at = time.time()
        return True

    def get_thoughts_by_zone(self, zone: str) -> List[ThoughtNode]:
        """Get all thoughts in a specific cognitive zone."""
        return [t for t in self.thoughts.values() if t.zone == zone]

    def get_thoughts_by_type(self, thought_type: str) -> List[ThoughtNode]:
        """Get all thoughts of a specific type."""
        return [t for t in self.thoughts.values() if t.thought_type == thought_type]

    def get_thoughts_by_domain(self, domain: str) -> List[ThoughtNode]:
        """Get all thoughts in a specific domain."""
        return [t for t in self.thoughts.values() if t.domain == domain]

    def get_thoughts_by_session(self, session_id: str) -> List[ThoughtNode]:
        """Get all thoughts from a specific session."""
        return [t for t in self.thoughts.values() if t.session_id == session_id]

    def get_children(self, thought_id: str) -> List[ThoughtNode]:
        """Get all child thoughts of a given thought."""
        child_ids = self.edges.get(thought_id, [])
        return [self.thoughts[cid] for cid in child_ids if cid in self.thoughts]

    def get_thoughts_by_memory(self, memory_id: str) -> List[ThoughtNode]:
        """Get all thoughts linked to a NEURON-X memory."""
        thought_ids = self.memory_edges.get(memory_id, [])
        return [self.thoughts[tid] for tid in thought_ids if tid in self.thoughts]

    def search_thoughts(self, query: str, top_k: int = 10) -> List[ThoughtNode]:
        """Search thoughts by content similarity.

        Uses simple token overlap scoring.
        """
        from cortex.core.tokenizer import tokenize_filtered, jaccard_similarity
        query_tokens = tokenize_filtered(query)
        if not query_tokens:
            return []

        scored = []
        for thought in self.thoughts.values():
            thought_tokens = tokenize_filtered(thought.content)
            score = jaccard_similarity(query_tokens, thought_tokens)
            if score > 0.0:
                scored.append((score, thought))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:top_k]]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # METACOG STATE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def set_metacog_state(self, state: Dict[str, Any]) -> None:
        """Update the metacognitive state snapshot."""
        self.metacog_state = state
        self.modified_at = time.time()

    def get_metacog_state(self) -> Dict[str, Any]:
        """Get current metacognitive state."""
        return self.metacog_state

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STRATEGIES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def add_strategy(self, strategy: Dict[str, Any]) -> None:
        """Add a strategy to the evolution history."""
        self.strategies.append(strategy)
        self.modified_at = time.time()

    def get_strategies(self) -> List[Dict[str, Any]]:
        """Get all strategy records."""
        return self.strategies

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GROWTH LOG
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def add_growth_entry(self, entry: Dict[str, Any]) -> None:
        """Add a growth measurement to the log."""
        self.growth_log.append(entry)
        self.modified_at = time.time()

    def get_growth_log(self) -> List[Dict[str, Any]]:
        """Get growth measurement history."""
        return self.growth_log

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STATS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def thought_count(self) -> int:
        return len(self.thoughts)

    @property
    def edge_count(self) -> int:
        return sum(len(v) for v in self.edges.values())

    @property
    def strategy_count(self) -> int:
        return len(self.strategies)

    @property
    def growth_entry_count(self) -> int:
        return len(self.growth_log)

    @property
    def wisdom_count(self) -> int:
        return sum(1 for t in self.thoughts.values() if t.is_wisdom)

    @property
    def zone_distribution(self) -> Dict[str, int]:
        """Count of thoughts per cognitive zone."""
        dist: Dict[str, int] = {}
        for t in self.thoughts.values():
            dist[t.zone] = dist.get(t.zone, 0) + 1
        return dist

    def stats(self) -> Dict[str, Any]:
        """Full statistics snapshot."""
        return {
            "thought_count": self.thought_count,
            "edge_count": self.edge_count,
            "strategy_count": self.strategy_count,
            "growth_entries": self.growth_entry_count,
            "wisdom_count": self.wisdom_count,
            "zones": self.zone_distribution,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SERIALIZATION — 8-LAYER BINARY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _pack_header(self) -> bytes:
        """Pack Layer 1: Header."""
        return struct.pack(
            CORTEXDB_HEADER_FORMAT,
            CORTEXDB_MAGIC,
            CORTEXDB_VERSION,
            self.modified_at,
            self.thought_count,
            self.edge_count,
            self.strategy_count,
            self.wisdom_count,
            len(self.metacog_state),
            len(self.growth_log),
            0,                 # reserved count
            b'\x00' * 32,      # reserved bytes
        )

    def _pack_zone_index(self) -> bytes:
        """Pack Layer 2: Zone index."""
        index: Dict[str, List[str]] = {}
        for thought in self.thoughts.values():
            if thought.zone not in index:
                index[thought.zone] = []
            index[thought.zone].append(thought.id)
        data = json.dumps(index).encode("utf-8")
        return zlib.compress(data, COMPRESSION_LEVEL)

    def _pack_thoughts(self) -> bytes:
        """Pack Layer 3: Compressed thoughts."""
        thoughts_list = [t.to_dict() for t in self.thoughts.values()]
        data = json.dumps(thoughts_list, default=str).encode("utf-8")
        return zlib.compress(data, COMPRESSION_LEVEL)

    def _pack_edges(self) -> bytes:
        """Pack Layer 4: Edge mappings."""
        edge_data = {
            "parent_child": self.edges,
            "memory_thought": self.memory_edges,
        }
        data = json.dumps(edge_data).encode("utf-8")
        return zlib.compress(data, COMPRESSION_LEVEL)

    def _pack_metacog(self) -> bytes:
        """Pack Layer 5: Metacognitive state."""
        data = json.dumps(self.metacog_state, default=str).encode("utf-8")
        return zlib.compress(data, COMPRESSION_LEVEL)

    def _pack_strategies(self) -> bytes:
        """Pack Layer 6: Strategy evolution."""
        data = json.dumps(self.strategies, default=str).encode("utf-8")
        return zlib.compress(data, COMPRESSION_LEVEL)

    def _pack_growth(self) -> bytes:
        """Pack Layer 7: Growth log."""
        data = json.dumps(self.growth_log, default=str).encode("utf-8")
        return zlib.compress(data, COMPRESSION_LEVEL)

    def save(self) -> None:
        """Save the brain to .cortex binary file using CMP protocol.

        4-phase write: PREPARE → WRITE → SEAL → VERIFY
        """
        lock = CMPLock(self.path)

        try:
            # Phase 1: PREPARE
            lock.acquire()
            lock.create_backup()

            # Phase 2: WRITE layers 1-7
            header = self._pack_header()
            zone_idx = self._pack_zone_index()
            thoughts = self._pack_thoughts()
            edges = self._pack_edges()
            metacog = self._pack_metacog()
            strategies = self._pack_strategies()
            growth = self._pack_growth()

            # Build layer offset table
            # Format: 7 × (offset:Q, size:Q) = 112 bytes
            offset_format = '<7Q7Q'
            layers = [zone_idx, thoughts, edges, metacog, strategies, growth]

            current_offset = CORTEXDB_HEADER_SIZE + struct.calcsize(offset_format)
            offsets = []
            sizes = []
            for layer in layers:
                offsets.append(current_offset)
                sizes.append(len(layer))
                current_offset += len(layer)

            # Add dummy offset/size for seal
            offsets.append(current_offset)
            sizes.append(CORTEXDB_SEAL_SIZE)

            offset_table = struct.pack(offset_format, *offsets, *sizes)

            # Combine layers 1-7
            body = header + offset_table
            for layer in layers:
                body += layer

            # Phase 3: SEAL
            seal = IntegritySeal.create(
                body, self.thought_count, "1.0.0"
            )
            full_data = body + seal.pack()

            # Write atomically
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "wb") as f:
                f.write(full_data)

            # Phase 4: VERIFY
            with open(self.path, "rb") as f:
                written = f.read()
            written_body = written[:-CORTEXDB_SEAL_SIZE]
            written_seal = IntegritySeal.unpack(written[-CORTEXDB_SEAL_SIZE:])

            if not written_seal.verify(written_body):
                lock.restore_backup()
                raise CortexDBWriteError("Integrity verification failed after write")

            lock.cleanup_backup()

        except CortexDBWriteError:
            raise
        except Exception as e:
            lock.restore_backup()
            raise CortexDBWriteError(f"CMP write failed: {e}") from e
        finally:
            lock.release()

    @classmethod
    def load(cls, path: str) -> "CortexDB":
        """Load a brain from .cortex binary file.

        Verifies magic bytes, version, and integrity seal.
        """
        if not Path(path).exists():
            raise CortexDBError(f"File not found: {path}")

        with open(path, "rb") as f:
            data = f.read()

        # Verify minimum size
        if len(data) < CORTEXDB_HEADER_SIZE + CORTEXDB_SEAL_SIZE:
            raise CortexDBCorruptionError("File too small to be a valid .cortex file")

        # Verify magic bytes
        magic = data[:4]
        if magic != CORTEXDB_MAGIC:
            raise CortexDBCorruptionError(
                f"Invalid magic bytes: expected {CORTEXDB_MAGIC!r}, got {magic!r}"
            )

        # Verify integrity seal
        body = data[:-CORTEXDB_SEAL_SIZE]
        seal = IntegritySeal.unpack(data[-CORTEXDB_SEAL_SIZE:])
        if not seal.verify(body):
            raise CortexDBCorruptionError("Integrity seal verification failed — data may be tampered")

        # Parse header
        header_data = struct.unpack(
            CORTEXDB_HEADER_FORMAT,
            data[:CORTEXDB_HEADER_SIZE],
        )
        _magic, version, modified_at = header_data[0], header_data[1], header_data[2]

        if version != CORTEXDB_VERSION:
            raise CortexDBVersionError(f"Unsupported version: {version}")

        # Parse offset table
        offset_format = '<7Q7Q'
        offset_size = struct.calcsize(offset_format)
        offset_start = CORTEXDB_HEADER_SIZE
        offset_data = struct.unpack(
            offset_format,
            data[offset_start:offset_start + offset_size],
        )
        offsets = list(offset_data[:7])
        sizes = list(offset_data[7:])

        # Create db instance
        db = cls(path)
        db.modified_at = modified_at

        # Decompress Layer 2: Zone index (skip — reconstructed from thoughts)
        # Decompress Layer 3: Thoughts
        thoughts_raw = zlib.decompress(
            data[offsets[1]:offsets[1] + sizes[1]]
        )
        thoughts_list = json.loads(thoughts_raw.decode("utf-8"))
        for td in thoughts_list:
            thought = ThoughtNode.from_dict(td)
            db.thoughts[thought.id] = thought

        # Decompress Layer 4: Edges
        edges_raw = zlib.decompress(
            data[offsets[2]:offsets[2] + sizes[2]]
        )
        edge_data = json.loads(edges_raw.decode("utf-8"))
        db.edges = edge_data.get("parent_child", {})
        db.memory_edges = edge_data.get("memory_thought", {})

        # Decompress Layer 5: Metacog
        metacog_raw = zlib.decompress(
            data[offsets[3]:offsets[3] + sizes[3]]
        )
        db.metacog_state = json.loads(metacog_raw.decode("utf-8"))

        # Decompress Layer 6: Strategies
        strat_raw = zlib.decompress(
            data[offsets[4]:offsets[4] + sizes[4]]
        )
        db.strategies = json.loads(strat_raw.decode("utf-8"))

        # Decompress Layer 7: Growth
        growth_raw = zlib.decompress(
            data[offsets[5]:offsets[5] + sizes[5]]
        )
        db.growth_log = json.loads(growth_raw.decode("utf-8"))

        return db

    def __repr__(self) -> str:
        return (
            f"CortexDB(path='{self.path}', "
            f"thoughts={self.thought_count}, "
            f"edges={self.edge_count}, "
            f"strategies={self.strategy_count})"
        )
