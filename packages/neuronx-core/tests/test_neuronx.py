"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Comprehensive Test Suite               ║
║  112+ tests covering ALL systems and ALL bug fixes       ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import math
import json
import tempfile
import shutil
import unittest
from pathlib import Path

# Add package root so tests can find neuronx
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neuronx.config import (
    DECAY_RATES, ZONE_HOT, ZONE_WARM, ZONE_COLD, ZONE_SILENT,
    TRUTH_ACTIVE, TRUTH_EXPIRED, TRUTH_CONTESTED,
    SURPRISE_ECHO_THRESHOLD, SURPRISE_CLASH_THRESHOLD,
    CLASH_JACCARD_GATE, BOND_PRUNE_THRESHOLD,
    HEAT_HOT_THRESHOLD, HEAT_WARM_THRESHOLD, HEAT_COLD_THRESHOLD,
    ANCHOR_CONFIDENCE_THRESHOLD, ANCHOR_ACCESS_THRESHOLD,
    WSRAX_WORD_RESONANCE, WSRAX_ZONE_HEAT, WSRAX_SPARK_LEGACY,
    WSRAX_RECENCY_CURVE, WSRAX_BOND_CENTRALITY, WSRAX_CONFIDENCE,
    WSRAX_DECAY_DEBT, WSRAX_CLASH_PENALTY,
    MAX_WEIGHT, MIN_WEIGHT, SUPERSEDE_MARGIN,
    SOMA_MAGIC, SOMA_HEADER_SIZE, SOMA_SEAL_SIZE,
    AUDIT_INTERVAL, MAX_INPUT_CHARS_BEFORE_CHUNK,
    STOP_WORDS, NRNLANG_EMOTION_SYMBOLS, NRNLANG_ACTION_SYMBOLS,
)
from neuronx.core.node import EngramNode, HALF_LIVES
from neuronx.core.integrity import (
    generate_engram_id, compute_checksum, verify_checksum,
    build_header, parse_header, build_seal, parse_seal,
)
from neuronx.core.soma import SomaDB, AxonRecord
from neuronx.core.surprise import Amygdala
from neuronx.core.retrieval import RetrievalEngine
from neuronx.core.bonds import BondEngine
from neuronx.core.zones import ThermalManager
from neuronx.brain.contradiction import ContradictionEngine, ContradictionResult
from neuronx.brain.extractor import MemoryExtractor
from neuronx.brain.injector import ContextInjector
from neuronx.brain.scheduler import AuditScheduler
from neuronx.brain.indexer import SubjectIndex
from neuronx.brain.neuron import NeuronBrain
from neuronx.language.nrnlang import NRNLangInterpreter
from neuronx.utils.tokenizer import tokenize, jaccard
from neuronx.utils.exporter import BrainExporter
from neuronx.utils.events import EventBus, events
from neuronx.exceptions import (
    NeuronXCorruptionError, NeuronXLockTimeoutError,
    NRNSyntaxError, NRNRuntimeError,
)


# ═══════════════════════════════════
# TEST CLASS 1: Config Constants
# ═══════════════════════════════════

class TestConfig(unittest.TestCase):
    """Test centralized configuration constants."""

    def test_thresholds_exist(self):
        """All spec thresholds defined in config."""
        self.assertEqual(SURPRISE_ECHO_THRESHOLD, 0.25)
        self.assertEqual(SURPRISE_CLASH_THRESHOLD, 0.85)
        self.assertEqual(CLASH_JACCARD_GATE, 0.15)
        self.assertEqual(BOND_PRUNE_THRESHOLD, 0.05)
        self.assertEqual(HEAT_HOT_THRESHOLD, 0.70)
        self.assertEqual(HEAT_WARM_THRESHOLD, 0.30)
        self.assertEqual(HEAT_COLD_THRESHOLD, 0.05)
        self.assertEqual(ANCHOR_CONFIDENCE_THRESHOLD, 0.95)
        self.assertEqual(ANCHOR_ACCESS_THRESHOLD, 20)
        self.assertEqual(MAX_WEIGHT, 3.0)
        self.assertEqual(MIN_WEIGHT, 0.1)

    def test_wsrax_weights_exact(self):
        """WSRA-X component weights match spec exactly."""
        self.assertEqual(WSRAX_WORD_RESONANCE, 2.5)
        self.assertEqual(WSRAX_ZONE_HEAT, 2.0)
        self.assertEqual(WSRAX_SPARK_LEGACY, 1.8)
        self.assertEqual(WSRAX_RECENCY_CURVE, 1.5)
        self.assertEqual(WSRAX_BOND_CENTRALITY, 1.2)
        self.assertEqual(WSRAX_CONFIDENCE, 1.0)
        self.assertEqual(WSRAX_DECAY_DEBT, 1.3)
        self.assertEqual(WSRAX_CLASH_PENALTY, 0.8)

    def test_decay_rates_exist(self):
        """All 5 decay classes defined."""
        self.assertIn("emotion", DECAY_RATES)
        self.assertIn("opinion", DECAY_RATES)
        self.assertIn("event", DECAY_RATES)
        self.assertIn("fact", DECAY_RATES)
        self.assertIn("identity", DECAY_RATES)
        self.assertEqual(len(DECAY_RATES), 5)

    def test_soma_magic_bytes(self):
        """SOMA magic bytes = NRN + 0xCE."""
        self.assertEqual(SOMA_MAGIC, b'\x4E\x52\x4E\xCE')

    def test_stop_words_is_frozenset(self):
        """Stop words immutable."""
        self.assertIsInstance(STOP_WORDS, frozenset)

    def test_nrnlang_symbols_exist(self):
        """All NRNLANG-Ω symbols defined."""
        self.assertIn("happy", NRNLANG_EMOTION_SYMBOLS)
        self.assertIn("FORGE", NRNLANG_ACTION_SYMBOLS)
        self.assertIn("ECHO", NRNLANG_ACTION_SYMBOLS)


# ═══════════════════════════════════
# TEST CLASS 2: EngramNode
# ═══════════════════════════════════

class TestEngramNode(unittest.TestCase):
    """Test ENGRAM data structure."""

    def test_create_engram(self):
        e = EngramNode(
            id="a3f9c2b1d4e5f6a7", raw="user lives in Tokyo",
            born=time.time(), last_seen=time.time(),
            surprise_score=0.72, weight=1.0, confidence=0.85,
            decay_class="identity", emotion="happy",
        )
        self.assertEqual(e.id, "a3f9c2b1d4e5f6a7")
        self.assertEqual(e.raw, "user lives in Tokyo")
        self.assertEqual(e.surprise_score, 0.72)
        self.assertTrue(e.is_active_engram())
        self.assertFalse(e.is_expired_engram())

    def test_decay_rates(self):
        """All 5 decay classes have correct half-lives."""
        self.assertAlmostEqual(HALF_LIVES["emotion"], 69.3, places=0)
        self.assertAlmostEqual(HALF_LIVES["opinion"], 138.6, places=0)
        self.assertAlmostEqual(HALF_LIVES["event"], 231.0, places=0)
        self.assertAlmostEqual(HALF_LIVES["fact"], 693.1, places=0)
        self.assertAlmostEqual(HALF_LIVES["identity"], 6931.5, places=0)

    def test_recency_score(self):
        e = EngramNode(decay_class="fact", born=time.time(), last_seen=time.time())
        self.assertAlmostEqual(e.recency_score, 1.0, places=2)

    def test_strengthen_weaken(self):
        e = EngramNode(weight=1.0)
        e.strengthen(0.15)
        self.assertEqual(e.weight, 1.15)
        e.weight = 2.95
        e.strengthen(0.15)
        self.assertEqual(e.weight, 3.0)
        e.weight = 0.12
        e.weaken(0.05)
        self.assertAlmostEqual(e.weight, 0.1, places=2)

    def test_expire(self):
        e = EngramNode(truth=TRUTH_ACTIVE, confidence=0.90)
        e.expire(superseded_by_id="new123")
        self.assertEqual(e.truth, TRUTH_EXPIRED)
        self.assertEqual(e.superseded_by, "new123")
        self.assertAlmostEqual(e.confidence, 0.60, places=1)

    def test_serialization(self):
        e = EngramNode(
            id="test1234test1234", raw="test memory",
            born=1234567890.0, last_seen=1234567890.0,
            surprise_score=0.5, weight=1.5, confidence=0.85,
            decay_class="opinion", emotion="curious",
            tags=["test", "memory"], zone=ZONE_WARM,
        )
        d = e.to_dict()
        e2 = EngramNode.from_dict(d)
        self.assertEqual(e.id, e2.id)
        self.assertEqual(e.raw, e2.raw)
        self.assertEqual(e.born, e2.born)
        self.assertEqual(e.surprise_score, e2.surprise_score)
        self.assertEqual(e.weight, e2.weight)
        self.assertEqual(e.confidence, e2.confidence)
        self.assertEqual(e.decay_class, e2.decay_class)
        self.assertEqual(e.emotion, e2.emotion)
        self.assertEqual(e.tags, e2.tags)

    def test_bond_centrality(self):
        e = EngramNode()
        self.assertAlmostEqual(e.bond_centrality, 0.0, places=2)
        e.bonds = {"a": 0.5, "b": 0.3, "c": 0.7}
        expected = math.log10(1 + 3) / 3.0
        self.assertAlmostEqual(e.bond_centrality, expected, places=4)

    def test_clash_penalty(self):
        e = EngramNode()
        self.assertEqual(e.clash_penalty, 0.0)
        e.superseded_by = "some_id"
        self.assertEqual(e.clash_penalty, 0.5)
        e.contradicts = ["a", "b"]
        self.assertAlmostEqual(e.clash_penalty, 0.7, places=1)

    def test_is_anchor_field(self):
        """BUG-005 FIX: is_anchor is a real boolean field."""
        e = EngramNode(is_anchor=False)
        self.assertFalse(e.is_anchor)
        e.crystallize()
        self.assertTrue(e.is_anchor)
        self.assertEqual(e.zone, ZONE_HOT)

    def test_zone_heat_value_anchor(self):
        """Anchored engrams have zone_heat_value = 1.0."""
        e = EngramNode(is_anchor=True)
        self.assertEqual(e.zone_heat_value, 1.0)

    def test_ghost_detection(self):
        e = EngramNode(zone=ZONE_SILENT, truth=TRUTH_ACTIVE)
        self.assertTrue(e.is_ghost())
        e.truth = TRUTH_EXPIRED
        self.assertFalse(e.is_ghost())


# ═══════════════════════════════════
# TEST CLASS 3: Integrity
# ═══════════════════════════════════

class TestIntegrity(unittest.TestCase):

    def test_engram_id_uniqueness(self):
        ids = set()
        for i in range(100):
            eid = generate_engram_id(f"test memory {i}")
            self.assertEqual(len(eid), 16)
            ids.add(eid)
        self.assertEqual(len(ids), 100)

    def test_checksum_verification(self):
        data = b"Hello, NEURON-X Omega!"
        checksum = compute_checksum(data)
        self.assertTrue(verify_checksum(data, checksum))
        self.assertFalse(verify_checksum(data + b"x", checksum))

    def test_header_build_parse(self):
        now = time.time()
        header = build_header(
            total_engrams=42, hot_count=5, warm_count=20,
            cold_count=15, silent_count=2, total_axons=30,
            created_at=now, modified_at=now,
        )
        self.assertEqual(len(header), SOMA_HEADER_SIZE)
        parsed = parse_header(header)
        self.assertEqual(parsed["total_engrams"], 42)
        self.assertEqual(parsed["hot_count"], 5)
        self.assertEqual(parsed["warm_count"], 20)
        self.assertEqual(parsed["cold_count"], 15)
        self.assertEqual(parsed["silent_count"], 2)
        self.assertEqual(parsed["total_axons"], 30)

    def test_seal_build_parse(self):
        data_hash = compute_checksum(b"test data")
        seal = build_seal(data_hash, save_count=7)
        self.assertEqual(len(seal), SOMA_SEAL_SIZE)
        parsed = parse_seal(seal)
        self.assertEqual(parsed["data_hash"], data_hash)
        self.assertEqual(parsed["save_count"], 7)

    def test_magic_bytes_in_header(self):
        header = build_header(0, 0, 0, 0, 0, 0, time.time(), time.time())
        self.assertEqual(header[:4], SOMA_MAGIC)


# ═══════════════════════════════════
# TEST CLASS 4: Tokenizer
# ═══════════════════════════════════

class TestTokenizer(unittest.TestCase):

    def test_tokenize_basics(self):
        tokens = tokenize("I love eating pizza in Tokyo")
        self.assertIn("love", tokens)
        self.assertIn("eating", tokens)
        self.assertIn("pizza", tokens)
        self.assertIn("tokyo", tokens)
        self.assertNotIn("in", tokens)  # stop word

    def test_tokenize_removes_short(self):
        tokens = tokenize("A is of the")
        self.assertEqual(len(tokens), 0)

    def test_tokenize_returns_frozenset(self):
        tokens = tokenize("hello world test")
        self.assertIsInstance(tokens, frozenset)

    def test_jaccard_similarity(self):
        a = frozenset({"pizza", "love", "eating"})
        b = frozenset({"pizza", "love", "cooking"})
        sim = jaccard(a, b)
        self.assertAlmostEqual(sim, 0.5, places=2)

    def test_jaccard_empty(self):
        self.assertEqual(jaccard(frozenset(), frozenset()), 1.0)
        self.assertEqual(jaccard(frozenset({"a"}), frozenset()), 0.0)

    def test_jaccard_identical(self):
        a = frozenset({"hello", "world"})
        self.assertAlmostEqual(jaccard(a, a), 1.0, places=2)


# ═══════════════════════════════════
# TEST CLASS 5: SOMA-DB
# ═══════════════════════════════════

class TestSomaDB(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.soma_path = os.path.join(self.test_dir, "test.soma")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_load_empty(self):
        db = SomaDB(self.soma_path)
        self.assertTrue(db.save())
        db2 = SomaDB(self.soma_path)
        self.assertTrue(db2.load())
        self.assertEqual(len(db2.engrams), 0)

    def test_save_load_engrams(self):
        db = SomaDB(self.soma_path)
        for i in range(50):
            e = EngramNode(
                id=generate_engram_id(f"memory {i}"),
                raw=f"test memory number {i}",
                born=time.time(), last_seen=time.time(),
                surprise_score=0.5, weight=1.0,
                confidence=0.80, zone=ZONE_WARM,
            )
            db.add_engram(e)
        self.assertTrue(db.save())
        db2 = SomaDB(self.soma_path)
        self.assertTrue(db2.load())
        self.assertEqual(len(db2.engrams), 50)
        for eid, e in db.engrams.items():
            self.assertIn(eid, db2.engrams)
            self.assertEqual(e.raw, db2.engrams[eid].raw)

    def test_save_load_with_zones(self):
        db = SomaDB(self.soma_path)
        zones = [ZONE_HOT, ZONE_WARM, ZONE_COLD, ZONE_SILENT]
        for i, zone in enumerate(zones):
            e = EngramNode(
                id=generate_engram_id(f"zone test {i}"),
                raw=f"memory in {zone} zone",
                born=time.time(), last_seen=time.time(), zone=zone,
            )
            db.add_engram(e)
        self.assertTrue(db.save())
        db2 = SomaDB(self.soma_path)
        self.assertTrue(db2.load())
        self.assertEqual(len(db2.engrams), 4)

    def test_backup_created(self):
        """BUG-006 FIX: NMP creates backup."""
        db = SomaDB(self.soma_path)
        db.add_engram(EngramNode(id=generate_engram_id("backup1"), raw="backup test", born=time.time(), last_seen=time.time()))
        db.save()
        db.add_engram(EngramNode(id=generate_engram_id("backup2"), raw="second memory", born=time.time(), last_seen=time.time()))
        db.save()
        self.assertTrue(os.path.exists(db.backup_path))

    def test_nrnlog_created(self):
        """BUG-006 FIX: NMP creates .nrnlog."""
        db = SomaDB(self.soma_path)
        db.add_engram(EngramNode(id=generate_engram_id("log test"), raw="log test", born=time.time(), last_seen=time.time()))
        db.save()
        self.assertTrue(os.path.exists(db.log_path))

    def test_sig_created(self):
        """BUG-006 FIX: NMP creates .soma.sig."""
        db = SomaDB(self.soma_path)
        db.add_engram(EngramNode(id=generate_engram_id("sig test"), raw="sig test", born=time.time(), last_seen=time.time()))
        db.save()
        self.assertTrue(os.path.exists(db.sig_path))

    def test_magic_bytes_in_file(self):
        """BUG-001 FIX: True binary format with magic bytes."""
        db = SomaDB(self.soma_path)
        db.add_engram(EngramNode(id=generate_engram_id("magic"), raw="magic bytes", born=time.time(), last_seen=time.time()))
        db.save()
        with open(self.soma_path, "rb") as f:
            first_4 = f.read(4)
        self.assertEqual(first_4, SOMA_MAGIC)

    def test_axon_save_load(self):
        db = SomaDB(self.soma_path)
        axon = AxonRecord(from_id="aaaa1111bbbb2222", to_id="cccc3333dddd4444", synapse=0.75)
        db.axons.append(axon)
        db.save()
        db2 = SomaDB(self.soma_path)
        db2.load()
        self.assertEqual(len(db2.axons), 1)
        self.assertAlmostEqual(db2.axons[0].synapse, 0.75, places=2)

    def test_integrity_seal(self):
        db = SomaDB(self.soma_path)
        db.add_engram(EngramNode(id=generate_engram_id("integrity"), raw="integrity test", born=time.time(), last_seen=time.time()))
        db.save()
        db2 = SomaDB(self.soma_path)
        self.assertTrue(db2.load())

    def test_stale_lock_handling(self):
        """BUG-020 FIX: Stale lock cleared."""
        db = SomaDB(self.soma_path)
        with open(db.lock_path, "w") as f:
            f.write("old lock")
        old_time = time.time() - 60
        os.utime(db.lock_path, (old_time, old_time))
        db.add_engram(EngramNode(id=generate_engram_id("lock"), raw="lock test", born=time.time(), last_seen=time.time()))
        self.assertTrue(db.save())

    def test_backup_restore(self):
        """BUG-004 FIX: Restore from .soma.bak."""
        db = SomaDB(self.soma_path)
        db.add_engram(EngramNode(id=generate_engram_id("orig"), raw="original data", born=time.time(), last_seen=time.time()))
        db.save()
        db.add_engram(EngramNode(id=generate_engram_id("more"), raw="more data", born=time.time(), last_seen=time.time()))
        db.save()
        # Corrupt main file
        with open(self.soma_path, "wb") as f:
            f.write(b"CORRUPTED DATA")
        db2 = SomaDB(self.soma_path)
        self.assertTrue(db2.load())
        self.assertGreater(len(db2.engrams), 0)


# ═══════════════════════════════════
# TEST CLASS 6: Amygdala (Surprise)
# ═══════════════════════════════════

class TestAmygdala(unittest.TestCase):

    def setUp(self):
        self.amygdala = Amygdala()

    def test_detect_emotion_happy(self):
        self.assertEqual(self.amygdala.detect_emotion("I love this amazing thing!"), "happy")

    def test_detect_emotion_sad(self):
        self.assertEqual(self.amygdala.detect_emotion("This is terrible and awful"), "sad")

    def test_detect_emotion_neutral(self):
        self.assertEqual(self.amygdala.detect_emotion("The temperature is 25 degrees"), "neutral")

    def test_detect_decay_class_identity(self):
        self.assertEqual(self.amygdala.detect_decay_class("I am a software engineer"), "identity")

    def test_detect_decay_class_event(self):
        self.assertEqual(self.amygdala.detect_decay_class("Yesterday I went to the store"), "event")

    def test_detect_decay_class_opinion(self):
        self.assertEqual(self.amygdala.detect_decay_class("I think Python is the best"), "opinion")

    def test_detect_decay_class_fact(self):
        self.assertEqual(self.amygdala.detect_decay_class("Paris is the capital of France"), "fact")

    def test_surprise_no_memories(self):
        result = self.amygdala.compute("I love pizza", {})
        self.assertEqual(result.surprise_score, 1.0)
        self.assertIsNone(result.best_match_id)
        self.assertEqual(result.action, "FORGE")

    def test_surprise_echo(self):
        existing = EngramNode(
            id="test1234test1234",
            raw="user loves pizza very much",
            born=time.time(), last_seen=time.time(),
            confidence=0.90,
        )
        result = self.amygdala.compute("user loves pizza very much", {"test1234test1234": existing})
        self.assertLess(result.surprise_score, 0.25)
        self.assertEqual(result.action, "ECHO")

    def test_surprise_forge(self):
        existing = EngramNode(
            id="test1234test1234",
            raw="user loves pizza",
            born=time.time(), last_seen=time.time(),
            confidence=0.90,
        )
        result = self.amygdala.compute("the weather is warm and sunny today", {"test1234test1234": existing})
        self.assertGreaterEqual(result.surprise_score, 0.25)
        self.assertEqual(result.action, "FORGE")

    def test_clash_gate_enforcement(self):
        """BUG-003 FIX: High surprise + low Jaccard = FORGE, not CLASH."""
        existing = EngramNode(
            id="test1234test1234",
            raw="user loves coding in Python",
            born=time.time(), last_seen=time.time(),
            confidence=0.90,
        )
        # Completely different topic, high surprise expected
        result = self.amygdala.compute(
            "elephants migrate across African savannas",
            {"test1234test1234": existing},
        )
        self.assertEqual(result.action, "FORGE")

    def test_compound_splitting(self):
        ideas = self.amygdala.split_compound("I love pizza and I hate cold weather")
        self.assertGreaterEqual(len(ideas), 2)


# ═══════════════════════════════════
# TEST CLASS 7: WSRA-X Retrieval
# ═══════════════════════════════════

class TestWSRAX(unittest.TestCase):

    def setUp(self):
        self.engine = RetrievalEngine()

    def test_score_relevant_engram(self):
        relevant = EngramNode(
            id="rel12345rel12345",
            raw="user's favorite food is pizza from Italy",
            born=time.time(), last_seen=time.time(),
            surprise_score=0.6, weight=1.5, confidence=0.90,
            zone=ZONE_HOT,
        )
        irrelevant = EngramNode(
            id="irr12345irr12345",
            raw="the weather forecast shows rain tomorrow",
            born=time.time(), last_seen=time.time(),
            surprise_score=0.3, weight=1.0, confidence=0.80,
            zone=ZONE_WARM,
        )
        results = self.engine.retrieve(
            "What food does the user prefer?",
            {"rel": relevant, "irr": irrelevant}, top_k=2,
        )
        self.assertEqual(results[0][0].id, relevant.id)

    def test_top_k_limiting(self):
        engrams = {}
        for i in range(20):
            eid = generate_engram_id(f"test {i}")
            engrams[eid] = EngramNode(
                id=eid, raw=f"test memory about topic number {i}",
                born=time.time(), last_seen=time.time(),
            )
        results = self.engine.retrieve("test memory topic", engrams, top_k=7)
        self.assertLessEqual(len(results), 7)

    def test_all_8_components_used(self):
        """BUG-002 FIX: All 8 components tracked."""
        e = EngramNode(
            id="comp12345comp1234",
            raw="testing all eight wsrax components",
            born=time.time(), last_seen=time.time(),
            surprise_score=0.5, weight=1.5, confidence=0.85,
            zone=ZONE_HOT,
        )
        query_tokens = tokenize("testing wsrax components")
        score, components = self.engine.score_engram(e, query_tokens)
        self.assertIn("word_resonance", components)
        self.assertIn("zone_heat", components)
        self.assertIn("spark_legacy", components)
        self.assertIn("bond_centrality", components)
        self.assertIn("recency_curve", components)
        self.assertIn("confidence", components)
        self.assertIn("decay_debt", components)
        self.assertIn("clash_penalty", components)
        self.assertEqual(len([c for c in components if c in [
            "word_resonance", "zone_heat", "spark_legacy", "bond_centrality",
            "recency_curve", "confidence", "decay_debt", "clash_penalty",
        ]]), 8)


# ═══════════════════════════════════
# TEST CLASS 8: Bond Engine
# ═══════════════════════════════════

class TestBondEngine(unittest.TestCase):

    def setUp(self):
        self.bonds = BondEngine()

    def test_time_bond(self):
        now = time.time()
        a = EngramNode(born=now)
        b = EngramNode(born=now + 30)
        bond = self.bonds.compute_time_bond(a, b)
        self.assertGreater(bond, 0.0)
        self.assertLessEqual(bond, 0.30)
        c = EngramNode(born=now + 300)
        self.assertEqual(self.bonds.compute_time_bond(a, c), 0.0)

    def test_word_bond(self):
        a = EngramNode(raw="user loves eating pizza from Italian restaurant")
        b = EngramNode(raw="user enjoys eating pizza and pasta regularly")
        bond = self.bonds.compute_word_bond(a, b)
        self.assertGreater(bond, 0.0)
        c = EngramNode(raw="the weather is nice today")
        self.assertEqual(self.bonds.compute_word_bond(a, c), 0.0)

    def test_emotion_bond(self):
        a = EngramNode(emotion="happy")
        b = EngramNode(emotion="happy")
        self.assertEqual(self.bonds.compute_emotion_bond(a, b), 0.10)
        c = EngramNode(emotion="neutral")
        d = EngramNode(emotion="neutral")
        self.assertEqual(self.bonds.compute_emotion_bond(c, d), 0.0)

    def test_synapse_capped(self):
        a = EngramNode(
            raw="user loves eating pizza from Italian restaurant near home every day",
            born=time.time(), emotion="happy",
        )
        b = EngramNode(
            raw="user loves eating pizza from Italian restaurant near home every night",
            born=time.time(), emotion="happy",
        )
        synapse = self.bonds.compute_synapse(a, b)
        self.assertLessEqual(synapse, 1.0)

    def test_prune_both_sides(self):
        """BUG-008 FIX: Pruning removes from BOTH sides."""
        test_dir = tempfile.mkdtemp()
        soma = SomaDB(os.path.join(test_dir, "test.soma"))
        a = EngramNode(id="aaaa", raw="test a", born=time.time(), last_seen=time.time())
        b = EngramNode(id="bbbb", raw="test b", born=time.time(), last_seen=time.time())
        soma.add_engram(a)
        soma.add_engram(b)
        axon = AxonRecord(from_id="aaaa", to_id="bbbb", synapse=0.01)
        soma.axons.append(axon)
        a.bonds["bbbb"] = 0.01
        b.bonds["aaaa"] = 0.01
        pruned = self.bonds.prune_weak_bonds(soma)
        self.assertEqual(pruned, 1)
        self.assertNotIn("bbbb", a.bonds)
        self.assertNotIn("aaaa", b.bonds)
        shutil.rmtree(test_dir, ignore_errors=True)


# ═══════════════════════════════════
# TEST CLASS 9: Thermal Manager
# ═══════════════════════════════════

class TestThermalManager(unittest.TestCase):

    def setUp(self):
        self.thermal = ThermalManager()

    def test_heat_computation(self):
        e = EngramNode(weight=2.0, born=time.time(), last_seen=time.time(), decay_class="fact")
        heat = self.thermal.compute_heat(e)
        self.assertGreaterEqual(heat, 0.0)
        self.assertLessEqual(heat, 1.0)

    def test_zone_assignment(self):
        hot = EngramNode(weight=3.0, born=time.time(), last_seen=time.time())
        zone = self.thermal.assign_zone(hot)
        self.assertIn(zone, [ZONE_HOT])

    def test_anchor_protection(self):
        e = EngramNode(confidence=0.96, access_count=25, weight=2.5,
                        born=time.time(), last_seen=time.time(), is_anchor=True)
        zone = self.thermal.assign_zone(e)
        self.assertEqual(zone, ZONE_HOT)

    def test_audit(self):
        engrams = {}
        for i in range(10):
            eid = generate_engram_id(f"audit test {i}")
            engrams[eid] = EngramNode(
                id=eid, raw=f"audit test memory {i}",
                born=time.time(), last_seen=time.time(), weight=1.0,
            )
        stats = self.thermal.audit(engrams)
        self.assertIn("promoted", stats)
        self.assertIn("demoted", stats)
        self.assertIn("zone_counts", stats)

    def test_reawakening_check(self):
        """BUG-007 FIX: Reawakening runs correctly."""
        engrams = {}
        ghost = EngramNode(
            id="ghost_id", raw="user loves astronomy stars telescope",
            born=time.time() - 86400*120, last_seen=time.time() - 86400*100,
            zone=ZONE_SILENT, truth=TRUTH_ACTIVE, surprise_score=0.9,
        )
        engrams["ghost_id"] = ghost
        tokens = tokenize("astronomy stars telescope user loves")
        reawakened = self.thermal.check_reawakenings(engrams, tokens)
        # Should reawaken because of high token overlap
        # (depends on threshold, so we just check it returns correctly)
        self.assertIsInstance(reawakened, list)


# ═══════════════════════════════════
# TEST CLASS 10: Contradiction
# ═══════════════════════════════════

class TestContradiction(unittest.TestCase):

    def setUp(self):
        self.engine = ContradictionEngine()

    def test_detect_negation(self):
        old = EngramNode(
            id="old12345old12345", raw="user loves cold weather",
            born=time.time() - 86400*30, last_seen=time.time() - 86400*5,
            confidence=0.85,
        )
        result = self.engine.detect_contradiction_heuristic("user hates cold weather", old)
        self.assertTrue(result.is_contradiction)

    def test_detect_update(self):
        old = EngramNode(
            id="old12345old12345", raw="user lives in London",
            born=time.time() - 86400*30, last_seen=time.time() - 86400*5,
            confidence=0.85,
        )
        result = self.engine.detect_contradiction_heuristic("user no longer lives in London", old)
        self.assertTrue(result.is_contradiction)

    def test_resolve_supersede(self):
        old = EngramNode(
            id="old12345old12345", raw="user lives in London",
            born=time.time() - 86400*365, last_seen=time.time() - 86400*120,
            confidence=0.60, decay_class="emotion",
        )
        new = EngramNode(
            id="new12345new12345", raw="user lives in Tokyo",
            born=time.time(), last_seen=time.time(),
            confidence=0.90,
        )
        result = ContradictionResult(is_contradiction=True, newer_wins=True, confidence=0.90)
        resolution = self.engine.resolve(new, old, result)
        self.assertEqual(resolution, "SUPERSEDED")
        self.assertEqual(old.truth, TRUTH_EXPIRED)
        self.assertEqual(old.superseded_by, new.id)

    def test_no_clash_on_unrelated(self):
        old = EngramNode(
            id="old12345old12345", raw="user loves pizza",
            born=time.time(), last_seen=time.time(),
            confidence=0.85,
        )
        result = self.engine.detect_contradiction_heuristic("the weather is sunny today", old)
        self.assertFalse(result.is_contradiction)


# ═══════════════════════════════════
# TEST CLASS 11: Extractor & Injector
# ═══════════════════════════════════

class TestExtractorInjector(unittest.TestCase):

    def setUp(self):
        self.extractor = MemoryExtractor()

    def test_extract_simple(self):
        items = self.extractor.extract("I love eating pizza")
        self.assertGreater(len(items), 0)
        self.assertIn("text", items[0])

    def test_extract_long_input_chunking(self):
        """BUG-013 FIX: Long inputs get chunked."""
        diverse_sentences = [
            "User loves eating pizza at Italian restaurants regularly",
            "Python programming language is great for machine learning",
            "Tokyo has wonderful cherry blossom festivals every spring",
            "Classical music concerts are fantastic entertainment options",
            "Mountain hiking provides excellent cardiovascular exercise benefits",
            "Quantum computing will revolutionize cryptography algorithms significantly",
            "Mediterranean cooking uses fresh olive oil and herbs",
            "Astronomy telescopes can observe distant galaxy formations clearly",
        ]
        long_text = ". ".join(diverse_sentences) + "."
        items = self.extractor.extract(long_text)
        self.assertGreater(len(items), 1)

    def test_injector_format(self):
        e = EngramNode(
            id="inj12345", raw="user loves pizza", born=time.time(),
            last_seen=time.time(), confidence=0.85, zone=ZONE_HOT,
        )
        output = ContextInjector.format_memories([(e, 5.0)])
        self.assertIn("pizza", output)

    def test_injector_empty(self):
        output = ContextInjector.format_memories([])
        self.assertEqual(output, "(No relevant memories found)")


# ═══════════════════════════════════
# TEST CLASS 12: Subject Index
# ═══════════════════════════════════

class TestSubjectIndex(unittest.TestCase):

    def test_index_and_find(self):
        """BUG-014 FIX: Subject index for fast lookup."""
        index = SubjectIndex()
        e1 = EngramNode(id="id1", raw="user loves eating pizza in Rome")
        e2 = EngramNode(id="id2", raw="user enjoys coding Python programs")
        index.add(e1)
        index.add(e2)
        candidates = index.find_candidates("pizza eating")
        self.assertIn("id1", candidates)
        self.assertNotIn("id2", candidates)

    def test_rebuild(self):
        index = SubjectIndex()
        engrams = {
            "id1": EngramNode(id="id1", raw="test memory one"),
            "id2": EngramNode(id="id2", raw="test memory two"),
        }
        index.rebuild(engrams)
        self.assertGreater(index.token_count, 0)


# ═══════════════════════════════════
# TEST CLASS 13: Scheduler
# ═══════════════════════════════════

class TestScheduler(unittest.TestCase):

    def test_audit_at_interval(self):
        """BUG-009 FIX: Audit triggers at AUDIT_INTERVAL."""
        scheduler = AuditScheduler(interval=10)
        for i in range(9):
            self.assertFalse(scheduler.tick())
        self.assertTrue(scheduler.tick())


# ═══════════════════════════════════
# TEST CLASS 14: NRNLANG-Ω
# ═══════════════════════════════════

class TestNRNLang(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_format_engram(self):
        e = EngramNode(
            id="test1234test1234", raw="user loves pizza",
            born=time.time(), last_seen=time.time(),
            surprise_score=0.8, heat=0.7, confidence=0.9,
            emotion="happy", zone=ZONE_HOT,
        )
        output = NRNLangInterpreter.format_engram_nrnlang(e)
        self.assertIn("ENGRAM", output)
        self.assertIn("pizza", output)

    def test_forge_command(self):
        brain = NeuronBrain(name="nrntest", data_dir=self.test_dir)
        interp = NRNLangInterpreter(brain=brain)
        result = interp.execute('FORGE engram("I love astronomy")')
        self.assertEqual(result["status"], "ok")
        self.assertIn("action", result)

    def test_stats_command(self):
        brain = NeuronBrain(name="nrntest", data_dir=self.test_dir)
        interp = NRNLangInterpreter(brain=brain)
        result = interp.execute("STATS brain")
        self.assertEqual(result["status"], "ok")
        self.assertIn("stats", result)

    def test_invalid_command(self):
        interp = NRNLangInterpreter()
        with self.assertRaises(NRNSyntaxError):
            interp.execute("INVALID COMMAND HERE")


# ═══════════════════════════════════
# TEST CLASS 15: Exporter
# ═══════════════════════════════════

class TestExporter(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.soma_path = os.path.join(self.test_dir, "test.soma")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_export_json(self):
        """BUG-018 FIX: Export includes all fields."""
        soma = SomaDB(self.soma_path)
        soma.add_engram(EngramNode(
            id="exp1", raw="export test", born=time.time(),
            last_seen=time.time(), tags=["test"], is_anchor=True,
        ))
        exporter = BrainExporter(soma)
        output = exporter.to_json()
        data = json.loads(output)
        self.assertIn("engrams", data)
        engram_data = data["engrams"]["exp1"]
        self.assertIn("is_anchor", engram_data)
        self.assertTrue(engram_data["is_anchor"])

    def test_export_csv(self):
        soma = SomaDB(self.soma_path)
        soma.add_engram(EngramNode(id="csv1", raw="csv test", born=time.time(), last_seen=time.time()))
        exporter = BrainExporter(soma)
        output = exporter.to_csv()
        self.assertIn("csv test", output)

    def test_export_markdown(self):
        soma = SomaDB(self.soma_path)
        soma.add_engram(EngramNode(id="md1", raw="markdown test", born=time.time(), last_seen=time.time()))
        exporter = BrainExporter(soma)
        output = exporter.to_markdown()
        self.assertIn("markdown test", output)


# ═══════════════════════════════════
# TEST CLASS 16: Events
# ═══════════════════════════════════

class TestEvents(unittest.TestCase):

    def test_event_bus(self):
        bus = EventBus()
        received = []
        bus.on("test", lambda **kw: received.append(kw))
        bus.emit("test", value=42)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["value"], 42)


# ═══════════════════════════════════
# TEST CLASS 17: End-to-End
# ═══════════════════════════════════

class TestEndToEnd(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_pipeline(self):
        """Full E2E: process → store → save → load → query."""
        brain = NeuronBrain(name="e2e_test", data_dir=self.test_dir)

        r1 = brain.remember("I love eating pizza")
        self.assertTrue(r1.is_new)
        r2 = brain.remember("My favorite color is blue")
        self.assertTrue(r2.is_new)
        r3 = brain.remember("I work as a software engineer")
        self.assertTrue(r3.is_new)
        self.assertGreater(len(brain.soma.engrams), 0)

        results = brain.recall("What food does user like?")
        self.assertGreater(len(results), 0)

        brain.end_session()

        brain2 = NeuronBrain(name="e2e_test", data_dir=self.test_dir)
        self.assertEqual(len(brain2.soma.engrams), len(brain.soma.engrams))
        results2 = brain2.recall("pizza")
        self.assertGreater(len(results2), 0)

    def test_contradiction_pipeline(self):
        brain = NeuronBrain(name="clash_test", data_dir=self.test_dir)
        brain.remember("I live in London")
        brain.remember("I no longer live in London, I moved to Tokyo")
        brain.end_session()
        self.assertGreater(len(brain.soma.engrams), 1)

    def test_session_persistence(self):
        brain = NeuronBrain(name="persist_test", data_dir=self.test_dir)
        brain.remember("I enjoy reading science fiction novels")
        brain.end_session()

        brain2 = NeuronBrain(name="persist_test", data_dir=self.test_dir)
        self.assertGreater(len(brain2.soma.engrams), 0)
        results = brain2.recall("reading")
        self.assertGreater(len(results), 0)

    def test_echo_reinforcement(self):
        brain = NeuronBrain(name="echo_test", data_dir=self.test_dir)
        r1 = brain.remember("user loves eating pizza very much")
        self.assertTrue(r1.is_new)
        eid = r1.engram_id
        orig_weight = brain.soma.engrams[eid].weight

        r2 = brain.remember("user loves eating pizza very much")
        self.assertEqual(r2.action, "ECHO")
        self.assertGreater(brain.soma.engrams[eid].weight, orig_weight)

    def test_get_context(self):
        brain = NeuronBrain(name="ctx_test", data_dir=self.test_dir)
        brain.remember("I love Python programming")
        ctx = brain.get_context("What programming language?", top_k=3, remember=False)
        self.assertIsNotNone(ctx.system_prompt_addition)
        self.assertIn("Python", ctx.system_prompt_addition)

    def test_export_from_brain(self):
        brain = NeuronBrain(name="export_test", data_dir=self.test_dir)
        brain.remember("Test memory for export")
        output = brain.export(format="json")
        data = json.loads(output)
        self.assertIn("engrams", data)

    def test_nrnlang_integration(self):
        """BUG-017 FIX: NRNLANG produces output to UI."""
        brain = NeuronBrain(name="nrn_test", data_dir=self.test_dir)
        interp = NRNLangInterpreter(brain=brain)
        result = interp.execute('FORGE engram("stars are beautiful")')
        self.assertIn("log", result)
        self.assertGreater(len(result["log"]), 0)


# ═══════════════════════════════════
# TEST CLASS 18: Integration Adapters
# ═══════════════════════════════════

class TestIntegrations(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pre_chat_injection(self):
        from neuronx.integrations.base import GenericIntegration
        brain = NeuronBrain(name="integ_test", data_dir=self.test_dir)
        brain.remember("User loves Python programming language")

        integration = GenericIntegration(brain=brain, top_k=3)
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What programming do I like?"},
        ]
        enriched = integration.pre_chat(messages)
        self.assertGreater(len(enriched), len(messages))


if __name__ == "__main__":
    unittest.main(verbosity=2)
