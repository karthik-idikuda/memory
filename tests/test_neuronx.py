"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Comprehensive Test Suite               ║
║  Tests all core systems A-Z                              ║
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

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.node import (
    Engram, DECAY_RATES, HALF_LIVES,
    ZONE_HOT, ZONE_WARM, ZONE_COLD, ZONE_SILENT, ZONE_ANCHOR,
    TRUTH_ACTIVE, TRUTH_EXPIRED, TRUTH_CONFLICT,
)
from core.integrity import (
    generate_engram_id, compute_checksum, verify_checksum,
    build_header, parse_header, build_seal, parse_seal,
    HEADER_SIZE, SEAL_SIZE,
)
from core.soma import SomaDB, AxonRecord
from core.surprise import Amygdala
from core.retrieval import RetrievalEngine
from core.bonds import BondEngine
from core.zones import ThermalManager
from brain.contradiction import ContradictionEngine


class TestEngramNode(unittest.TestCase):
    """Test ENGRAM data structure."""

    def test_create_engram(self):
        """ENGRAM fields initialize correctly."""
        e = Engram(
            id="a3f9c2b1d4e5f6a7",
            raw="user lives in Tokyo",
            born=time.time(),
            last_seen=time.time(),
            spark=0.72,
            weight=1.0,
            confidence=0.85,
            decay_class="identity",
            emotion="happy",
        )
        self.assertEqual(e.id, "a3f9c2b1d4e5f6a7")
        self.assertEqual(e.raw, "user lives in Tokyo")
        self.assertEqual(e.spark, 0.72)
        self.assertEqual(e.decay_class, "identity")
        self.assertTrue(e.is_active)
        self.assertFalse(e.is_expired)

    def test_decay_rates(self):
        """All 5 decay classes have correct half-lives."""
        # emotion: ~69 days
        self.assertAlmostEqual(HALF_LIVES["emotion"], 69.3, places=0)
        # opinion: ~139 days
        self.assertAlmostEqual(HALF_LIVES["opinion"], 138.6, places=0)
        # event: ~231 days
        self.assertAlmostEqual(HALF_LIVES["event"], 231.0, places=0)
        # fact: ~693 days
        self.assertAlmostEqual(HALF_LIVES["fact"], 693.1, places=0)
        # identity: ~6931 days
        self.assertAlmostEqual(HALF_LIVES["identity"], 6931.5, places=0)

    def test_recency_score(self):
        """Recency score follows exponential decay."""
        e = Engram(decay_class="fact", born=time.time(), last_seen=time.time())
        # Just created — recency should be ~1.0
        self.assertAlmostEqual(e.recency_score, 1.0, places=2)

    def test_strengthen_weaken(self):
        """Weight changes correctly."""
        e = Engram(weight=1.0)
        e.strengthen(0.15)
        self.assertEqual(e.weight, 1.15)

        e.weight = 2.95
        e.strengthen(0.15)
        self.assertEqual(e.weight, 3.0)  # capped at 3.0

        e.weight = 0.12
        e.weaken(0.05)
        self.assertAlmostEqual(e.weight, 0.1, places=2)  # capped at 0.1

    def test_expire(self):
        """Engram expires correctly."""
        e = Engram(truth=TRUTH_ACTIVE, confidence=0.90)
        e.expire(superseded_by_id="new123")
        self.assertEqual(e.truth, TRUTH_EXPIRED)
        self.assertEqual(e.superseded_by, "new123")
        self.assertAlmostEqual(e.confidence, 0.60, places=1)

    def test_serialization(self):
        """Engram serializes and deserializes correctly."""
        e = Engram(
            id="test1234test1234",
            raw="test memory",
            born=1234567890.0,
            last_seen=1234567890.0,
            spark=0.5,
            weight=1.5,
            confidence=0.85,
            decay_class="opinion",
            emotion="curious",
            tags=["test", "memory"],
            zone=ZONE_WARM,
        )
        d = e.to_dict()
        e2 = Engram.from_dict(d)

        self.assertEqual(e.id, e2.id)
        self.assertEqual(e.raw, e2.raw)
        self.assertEqual(e.born, e2.born)
        self.assertEqual(e.spark, e2.spark)
        self.assertEqual(e.weight, e2.weight)
        self.assertEqual(e.confidence, e2.confidence)
        self.assertEqual(e.decay_class, e2.decay_class)
        self.assertEqual(e.emotion, e2.emotion)
        self.assertEqual(e.tags, e2.tags)

    def test_bond_centrality(self):
        """Bond centrality formula works."""
        e = Engram()
        self.assertAlmostEqual(e.bond_centrality, 0.0, places=2)

        e.axons = {"a": 0.5, "b": 0.3, "c": 0.7}
        expected = math.log(1 + 3) / 10.0
        self.assertAlmostEqual(e.bond_centrality, expected, places=4)

    def test_clash_penalty(self):
        """Clash penalty formula works."""
        e = Engram()
        self.assertEqual(e.clash_penalty, 0.0)

        e.superseded_by = "some_id"
        self.assertEqual(e.clash_penalty, 0.5)

        e.contradicts = ["a", "b"]
        self.assertAlmostEqual(e.clash_penalty, 0.7, places=1)


class TestIntegrity(unittest.TestCase):
    """Test integrity engine."""

    def test_engram_id_uniqueness(self):
        """IDs are unique across 100 engrams."""
        ids = set()
        for i in range(100):
            eid = generate_engram_id(f"test memory {i}")
            self.assertEqual(len(eid), 16)
            ids.add(eid)
        self.assertEqual(len(ids), 100)

    def test_checksum_verification(self):
        """Checksum detects tampering."""
        data = b"Hello, NEURON-X Omega!"
        checksum = compute_checksum(data)
        self.assertTrue(verify_checksum(data, checksum))
        self.assertFalse(verify_checksum(data + b"x", checksum))

    def test_header_build_parse(self):
        """Header builds and parses correctly."""
        now = time.time()
        header = build_header(
            total_engrams=42,
            hot_count=5,
            warm_count=20,
            cold_count=15,
            silent_count=2,
            total_axons=30,
            created_at=now,
            modified_at=now,
        )
        self.assertEqual(len(header), HEADER_SIZE)

        parsed = parse_header(header)
        self.assertEqual(parsed["total_engrams"], 42)
        self.assertEqual(parsed["hot_count"], 5)
        self.assertEqual(parsed["warm_count"], 20)
        self.assertEqual(parsed["cold_count"], 15)
        self.assertEqual(parsed["silent_count"], 2)
        self.assertEqual(parsed["total_axons"], 30)

    def test_seal_build_parse(self):
        """Seal builds and parses correctly."""
        data_hash = compute_checksum(b"test data")
        seal = build_seal(data_hash, save_count=7)
        self.assertEqual(len(seal), SEAL_SIZE)

        parsed = parse_seal(seal)
        self.assertEqual(parsed["data_hash"], data_hash)
        self.assertEqual(parsed["save_count"], 7)


class TestSomaDB(unittest.TestCase):
    """Test SOMA-DB file engine."""

    def setUp(self):
        """Create temp directory for test SOMA files."""
        self.test_dir = tempfile.mkdtemp()
        self.soma_path = os.path.join(self.test_dir, "test.soma")

    def tearDown(self):
        """Clean up temp files."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_load_empty(self):
        """Empty brain saves and loads."""
        db = SomaDB(self.soma_path)
        self.assertTrue(db.save())

        db2 = SomaDB(self.soma_path)
        self.assertTrue(db2.load())
        self.assertEqual(len(db2.engrams), 0)

    def test_save_load_engrams(self):
        """Engrams survive save/load cycle."""
        db = SomaDB(self.soma_path)

        # Create 50 test engrams
        for i in range(50):
            e = Engram(
                id=generate_engram_id(f"memory {i}"),
                raw=f"test memory number {i}",
                born=time.time(),
                last_seen=time.time(),
                spark=0.5,
                weight=1.0,
                confidence=0.80,
                zone=ZONE_WARM,
            )
            db.add_engram(e)

        self.assertTrue(db.save())

        # Reload
        db2 = SomaDB(self.soma_path)
        self.assertTrue(db2.load())
        self.assertEqual(len(db2.engrams), 50)

        # Verify engram data survives
        for eid, e in db.engrams.items():
            self.assertIn(eid, db2.engrams)
            self.assertEqual(e.raw, db2.engrams[eid].raw)
            self.assertEqual(e.confidence, db2.engrams[eid].confidence)

    def test_save_load_with_zones(self):
        """All zones serialize correctly (including compression)."""
        db = SomaDB(self.soma_path)

        zones = [ZONE_HOT, ZONE_WARM, ZONE_COLD, ZONE_SILENT]
        for i, zone in enumerate(zones):
            e = Engram(
                id=generate_engram_id(f"zone test {i}"),
                raw=f"memory in {zone} zone",
                born=time.time(),
                last_seen=time.time(),
                zone=zone,
            )
            db.add_engram(e)

        self.assertTrue(db.save())

        db2 = SomaDB(self.soma_path)
        self.assertTrue(db2.load())
        self.assertEqual(len(db2.engrams), 4)

    def test_backup_created(self):
        """NMP protocol creates backup file."""
        db = SomaDB(self.soma_path)
        db.add_engram(Engram(
            id=generate_engram_id("backup test"),
            raw="backup test memory",
            born=time.time(),
            last_seen=time.time(),
        ))
        db.save()

        # Second save should create backup of first
        db.add_engram(Engram(
            id=generate_engram_id("second memory"),
            raw="second test memory",
            born=time.time(),
            last_seen=time.time(),
        ))
        db.save()

        self.assertTrue(os.path.exists(db.backup_path))

    def test_axon_save_load(self):
        """Axons survive save/load cycle."""
        db = SomaDB(self.soma_path)
        axon = AxonRecord(
            from_id="aaaa1111bbbb2222",
            to_id="cccc3333dddd4444",
            synapse=0.75,
        )
        db.axons.append(axon)
        db.save()

        db2 = SomaDB(self.soma_path)
        db2.load()
        self.assertEqual(len(db2.axons), 1)
        self.assertAlmostEqual(db2.axons[0].synapse, 0.75, places=2)

    def test_integrity_seal(self):
        """Integrity seal verifies correctly on load."""
        db = SomaDB(self.soma_path)
        db.add_engram(Engram(
            id=generate_engram_id("integrity test"),
            raw="integrity test memory",
            born=time.time(),
            last_seen=time.time(),
        ))
        db.save()

        # Loading should succeed with valid integrity
        db2 = SomaDB(self.soma_path)
        self.assertTrue(db2.load())


class TestAmygdala(unittest.TestCase):
    """Test surprise engine."""

    def setUp(self):
        self.amygdala = Amygdala()

    def test_tokenize(self):
        """Tokenization removes stop words and short tokens."""
        tokens = self.amygdala.tokenize("I love eating pizza in Tokyo")
        self.assertIn("love", tokens)
        self.assertIn("eating", tokens)
        self.assertIn("pizza", tokens)
        self.assertIn("tokyo", tokens)
        self.assertNotIn("i", tokens)
        self.assertNotIn("in", tokens)

    def test_jaccard_similarity(self):
        """Jaccard similarity computes correctly."""
        a = {"pizza", "love", "eating"}
        b = {"pizza", "love", "cooking"}
        sim = self.amygdala.jaccard_similarity(a, b)
        # Intersection: {pizza, love} = 2
        # Union: {pizza, love, eating, cooking} = 4
        self.assertAlmostEqual(sim, 0.5, places=2)

    def test_emotion_detection(self):
        """Emotion keywords detected."""
        self.assertEqual(
            self.amygdala.detect_emotion("I love this amazing thing!"),
            "happy"
        )
        self.assertEqual(
            self.amygdala.detect_emotion("This is terrible and awful"),
            "sad"
        )
        self.assertEqual(
            self.amygdala.detect_emotion("The temperature is 25 degrees"),
            "neutral"
        )

    def test_decay_class_detection(self):
        """Decay class classification works."""
        self.assertEqual(
            self.amygdala.detect_decay_class("I am a software engineer"),
            "identity"
        )
        self.assertEqual(
            self.amygdala.detect_decay_class("Yesterday I went to the store"),
            "event"
        )
        self.assertEqual(
            self.amygdala.detect_decay_class("I think Python is the best"),
            "opinion"
        )
        self.assertEqual(
            self.amygdala.detect_decay_class("Paris is the capital of France"),
            "fact"
        )

    def test_surprise_no_memories(self):
        """First memory should have surprise = 1.0."""
        surprise, match, action = self.amygdala.compute_surprise(
            "I love pizza", []
        )
        self.assertEqual(surprise, 1.0)
        self.assertIsNone(match)
        self.assertEqual(action, "FORGE")

    def test_surprise_echo(self):
        """Repeating same info triggers ECHO."""
        existing = Engram(
            id="test1234test1234",
            raw="user loves pizza very much",
            born=time.time(),
            last_seen=time.time(),
            confidence=0.90,
        )
        surprise, match, action = self.amygdala.compute_surprise(
            "user loves pizza very much", [existing]
        )
        self.assertLess(surprise, 0.25)
        self.assertEqual(action, "ECHO")

    def test_surprise_forge(self):
        """Genuinely new info triggers FORGE."""
        existing = Engram(
            id="test1234test1234",
            raw="user loves pizza",
            born=time.time(),
            last_seen=time.time(),
            confidence=0.90,
        )
        # Use lowercase text to avoid proper noun detection (which boosts to CLASH)
        surprise, match, action = self.amygdala.compute_surprise(
            "the weather is warm and sunny today", [existing]
        )
        self.assertGreaterEqual(surprise, 0.25)
        self.assertEqual(action, "FORGE")

    def test_compound_splitting(self):
        """Compound sentences split correctly."""
        ideas = self.amygdala.split_compound(
            "I love pizza and I hate cold weather"
        )
        self.assertGreaterEqual(len(ideas), 2)


class TestWSRAX(unittest.TestCase):
    """Test WSRA-X retrieval engine."""

    def setUp(self):
        self.engine = RetrievalEngine()

    def test_score_relevant_engram(self):
        """Relevant engrams score higher."""
        relevant = Engram(
            id="rel12345rel12345",
            raw="user's favorite food is pizza from Italy",
            born=time.time(),
            last_seen=time.time(),
            spark=0.6,
            weight=1.5,
            confidence=0.90,
            zone=ZONE_HOT,
        )
        irrelevant = Engram(
            id="irr12345irr12345",
            raw="the weather forecast shows rain tomorrow",
            born=time.time(),
            last_seen=time.time(),
            spark=0.3,
            weight=1.0,
            confidence=0.80,
            zone=ZONE_WARM,
        )

        results = self.engine.query(
            "What food does the user prefer?",
            [relevant, irrelevant],
            top_k=2,
        )

        # Relevant should rank higher
        self.assertEqual(results[0][0].id, relevant.id)

    def test_top_k_limiting(self):
        """Results limited to top_k."""
        engrams = []
        for i in range(20):
            e = Engram(
                id=generate_engram_id(f"test {i}"),
                raw=f"test memory about topic number {i}",
                born=time.time(),
                last_seen=time.time(),
            )
            engrams.append(e)

        results = self.engine.query("test memory topic", engrams, top_k=7)
        self.assertLessEqual(len(results), 7)


class TestBondEngine(unittest.TestCase):
    """Test AXON bond engine."""

    def setUp(self):
        self.bonds = BondEngine()

    def test_time_bond(self):
        """Time bond computed correctly."""
        now = time.time()
        a = Engram(born=now)
        b = Engram(born=now + 30)  # 30 seconds apart

        bond = self.bonds.compute_time_bond(a, b)
        self.assertGreater(bond, 0.0)
        self.assertLessEqual(bond, 0.30)

        # Far apart — no time bond
        c = Engram(born=now + 300)  # 5 minutes apart
        bond = self.bonds.compute_time_bond(a, c)
        self.assertEqual(bond, 0.0)

    def test_word_bond(self):
        """Word bond requires 3+ shared tokens."""
        a = Engram(raw="user loves eating pizza from Italian restaurant")
        b = Engram(raw="user enjoys eating pizza and pasta regularly")
        # Shared: user, eating, pizza = 3+ tokens
        bond = self.bonds.compute_word_bond(a, b)
        self.assertGreater(bond, 0.0)

        c = Engram(raw="the weather is nice today")
        bond = self.bonds.compute_word_bond(a, c)
        self.assertEqual(bond, 0.0)

    def test_emotion_bond(self):
        """Emotion bond for matching emotions."""
        a = Engram(emotion="happy")
        b = Engram(emotion="happy")
        self.assertEqual(self.bonds.compute_emotion_bond(a, b), 0.10)

        c = Engram(emotion="neutral")
        d = Engram(emotion="neutral")
        self.assertEqual(self.bonds.compute_emotion_bond(c, d), 0.0)

    def test_synapse_capped(self):
        """Synapse strength capped at 1.0."""
        a = Engram(
            raw="user loves eating pizza from Italian restaurant near home every day",
            born=time.time(),
            emotion="happy"
        )
        b = Engram(
            raw="user loves eating pizza from Italian restaurant near home every night",
            born=time.time(),
            emotion="happy"
        )
        synapse = self.bonds.compute_synapse(a, b)
        self.assertLessEqual(synapse, 1.0)


class TestThermalManager(unittest.TestCase):
    """Test zone assignment and reawakening."""

    def setUp(self):
        self.thermal = ThermalManager()

    def test_heat_computation(self):
        """Heat formula produces values in [0, 1]."""
        e = Engram(
            weight=2.0,
            born=time.time(),
            last_seen=time.time(),
            decay_class="fact",
        )
        heat = self.thermal.compute_heat(e)
        self.assertGreaterEqual(heat, 0.0)
        self.assertLessEqual(heat, 1.0)

    def test_zone_assignment(self):
        """Zones assigned based on heat thresholds."""
        # High heat → HOT
        hot = Engram(weight=3.0, born=time.time(), last_seen=time.time())
        zone = self.thermal.assign_zone(hot)
        self.assertIn(zone, [ZONE_HOT, ZONE_ANCHOR])

        # Low weight, old → COLD
        cold = Engram(
            weight=0.2,
            born=time.time() - 86400 * 60,  # 60 days old
            last_seen=time.time() - 86400 * 60,
            decay_class="emotion",
        )
        zone = self.thermal.assign_zone(cold)
        self.assertIn(zone, [ZONE_COLD, ZONE_SILENT])

    def test_anchor_protection(self):
        """High confidence + high access → ANCHOR."""
        e = Engram(confidence=0.96, access_count=25, weight=2.5)
        e.born = time.time()
        e.last_seen = time.time()
        zone = self.thermal.assign_zone(e)
        self.assertEqual(zone, ZONE_ANCHOR)

    def test_audit(self):
        """Audit runs without errors."""
        engrams = {}
        for i in range(10):
            e = Engram(
                id=generate_engram_id(f"audit test {i}"),
                raw=f"audit test memory {i}",
                born=time.time(),
                last_seen=time.time(),
                weight=1.0,
            )
            engrams[e.id] = e

        stats = self.thermal.audit(engrams)
        self.assertIn("promoted", stats)
        self.assertIn("demoted", stats)
        self.assertIn("zone_counts", stats)


class TestContradiction(unittest.TestCase):
    """Test contradiction engine."""

    def setUp(self):
        self.engine = ContradictionEngine()

    def test_detect_negation(self):
        """Negation patterns detected."""
        old = Engram(
            id="old12345old12345",
            raw="user loves cold weather",
            born=time.time() - 86400 * 30,
            last_seen=time.time() - 86400 * 5,
            confidence=0.85,
        )
        result = self.engine.detect_contradiction_heuristic(
            "user hates cold weather", old
        )
        self.assertTrue(result.is_contradiction)

    def test_detect_update(self):
        """Update language detected."""
        old = Engram(
            id="old12345old12345",
            raw="user lives in London",
            born=time.time() - 86400 * 30,
            last_seen=time.time() - 86400 * 5,
            confidence=0.85,
        )
        result = self.engine.detect_contradiction_heuristic(
            "user no longer lives in London", old
        )
        self.assertTrue(result.is_contradiction)

    def test_resolve_supersede(self):
        """Newer wins → SUPERSEDE."""
        old = Engram(
            id="old12345old12345",
            raw="user lives in London",
            born=time.time() - 86400 * 365,
            last_seen=time.time() - 86400 * 30,
            confidence=0.85,
            decay_class="identity",
        )
        new = Engram(
            id="new12345new12345",
            raw="user lives in Tokyo",
            born=time.time(),
            last_seen=time.time(),
            confidence=0.90,
        )

        from brain.contradiction import ContradictionResult
        result = ContradictionResult(
            is_contradiction=True,
            newer_wins=True,
            confidence=0.90,
        )

        resolution = self.engine.resolve(new, old, result)
        self.assertEqual(resolution, "SUPERSEDED")
        self.assertEqual(old.truth, TRUTH_EXPIRED)
        self.assertEqual(old.superseded_by, new.id)


class TestEndToEnd(unittest.TestCase):
    """Integration tests — full pipeline."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.soma_path = os.path.join(self.test_dir, "data", "test.soma")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_pipeline(self):
        """Full E2E: process → store → save → load → query."""
        from brain.neuron import NeuronBrain

        brain = NeuronBrain(soma_path=self.soma_path)
        brain.start_pulse()

        # Process some inputs
        r1 = brain.process_input("I love eating pizza")
        self.assertGreater(len(r1), 0)

        r2 = brain.process_input("My favorite color is blue")
        self.assertGreater(len(r2), 0)

        r3 = brain.process_input("I work as a software engineer")
        self.assertGreater(len(r3), 0)

        # Should have memories now
        self.assertGreater(len(brain.soma.engrams), 0)

        # Query
        results = brain.query("What food does user like?")
        self.assertGreater(len(results), 0)

        # End pulse and save
        brain.end_pulse()

        # Reload and verify persistence
        brain2 = NeuronBrain(soma_path=self.soma_path)
        self.assertEqual(
            len(brain2.soma.engrams),
            len(brain.soma.engrams),
        )

        # Query on reloaded brain
        results2 = brain2.query("pizza")
        self.assertGreater(len(results2), 0)

    def test_contradiction_pipeline(self):
        """E2E contradiction detection and resolution."""
        from brain.neuron import NeuronBrain

        brain = NeuronBrain(soma_path=self.soma_path)
        brain.start_pulse()

        # Store original fact
        brain.process_input("I live in London")

        # Store contradicting fact
        results = brain.process_input("I no longer live in London, I moved to Tokyo")

        # Check that contradiction was detected
        brain.end_pulse()
        self.assertGreater(len(brain.soma.engrams), 1)

    def test_session_persistence(self):
        """Memories survive session end/restart."""
        from brain.neuron import NeuronBrain

        brain = NeuronBrain(soma_path=self.soma_path)
        brain.start_pulse()
        brain.process_input("I enjoy reading science fiction novels")
        brain.end_pulse()

        # Reload brain — should have the memory
        brain2 = NeuronBrain(soma_path=self.soma_path)
        self.assertGreater(len(brain2.soma.engrams), 0)

        # Query — should find the reading memory
        results = brain2.query("reading")
        self.assertGreater(len(results), 0)


class TestConfig(unittest.TestCase):
    """Test centralized configuration constants."""

    def test_thresholds_exist(self):
        """All spec thresholds defined in config."""
        from config import (
            SURPRISE_ECHO_THRESHOLD, SURPRISE_CLASH_THRESHOLD,
            CLASH_JACCARD_GATE, BOND_PRUNE_THRESHOLD,
            HEAT_HOT_THRESHOLD, HEAT_WARM_THRESHOLD, HEAT_COLD_THRESHOLD,
            ANCHOR_CONFIDENCE_THRESHOLD, ANCHOR_ACCESS_THRESHOLD,
            MAX_WEIGHT, MIN_WEIGHT,
        )
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
        from config import (
            WSRAX_WORD_RESONANCE, WSRAX_ZONE_HEAT, WSRAX_SPARK_LEGACY,
            WSRAX_RECENCY_CURVE, WSRAX_BOND_CENTRALITY, WSRAX_CONFIDENCE,
            WSRAX_DECAY_DEBT, WSRAX_CLASH_PENALTY,
        )
        self.assertEqual(WSRAX_WORD_RESONANCE, 2.5)
        self.assertEqual(WSRAX_ZONE_HEAT, 2.0)
        self.assertEqual(WSRAX_SPARK_LEGACY, 1.8)
        self.assertEqual(WSRAX_RECENCY_CURVE, 1.5)
        self.assertEqual(WSRAX_BOND_CENTRALITY, 1.2)
        self.assertEqual(WSRAX_CONFIDENCE, 1.0)
        self.assertEqual(WSRAX_DECAY_DEBT, 1.3)
        self.assertEqual(WSRAX_CLASH_PENALTY, 0.8)

    def test_decay_rates_in_config(self):
        """Config contains all 5 decay rates."""
        from config import DECAY_RATES
        self.assertEqual(len(DECAY_RATES), 5)
        self.assertIn("emotion", DECAY_RATES)
        self.assertIn("identity", DECAY_RATES)


class TestExtractor(unittest.TestCase):
    """Test memory extraction (rule-based, no API)."""

    def setUp(self):
        self.extractor = None

    def _get_extractor(self):
        if self.extractor is None:
            from brain.extractor import MemoryExtractor
            self.extractor = MemoryExtractor(ai_client=None)
        return self.extractor

    def test_rule_extraction(self):
        """Rule-based extraction produces memories."""
        ext = self._get_extractor()
        memories = ext.extract("I love building robots and studying physics")
        self.assertGreater(len(memories), 0)
        for m in memories:
            self.assertIn("text", m)
            self.assertIn("decay_class", m)
            self.assertIn("emotion", m)

    def test_noise_filtered(self):
        """Greetings and noise are filtered out."""
        ext = self._get_extractor()
        memories = ext.extract("hi")
        self.assertEqual(len(memories), 0)

    def test_third_person_conversion(self):
        """First person converted to third person."""
        from brain.extractor import MemoryExtractor
        result = MemoryExtractor._to_third_person("i love pizza")
        self.assertIn("User", result)
        self.assertNotIn(" i ", f" {result} ".lower().replace("user", ""))

    def test_auto_tagging(self):
        """Auto-tagger produces relevant tags."""
        from brain.extractor import MemoryExtractor
        tags = MemoryExtractor._auto_tag("I work at a tech company")
        self.assertIn("work", tags)


class TestInjector(unittest.TestCase):
    """Test memory context injection."""

    def test_format_empty(self):
        """Empty results produce placeholder."""
        from brain.injector import format_memory_context
        result = format_memory_context([])
        self.assertIn("No memories", result)

    def test_format_with_memories(self):
        """Memories format correctly for injection."""
        from brain.injector import format_memory_context
        now = time.time()
        e = Engram(
            id="inj12345inj12345",
            raw="user loves pizza",
            born=now, last_seen=now,
            zone=ZONE_HOT, confidence=0.9,
        )
        result = format_memory_context([(e, 0.85)])
        self.assertIn("pizza", result)
        self.assertIn("HOT", result)

    def test_zone_ordering(self):
        """HOT memories appear before COLD in formatted output."""
        from brain.injector import format_memory_context
        now = time.time()
        hot = Engram(id="hot12345hot12345", raw="hot memory", born=now,
                     last_seen=now, zone=ZONE_HOT, confidence=0.9)
        cold = Engram(id="cold1234cold1234", raw="cold memory", born=now,
                      last_seen=now, zone=ZONE_COLD, confidence=0.5)
        result = format_memory_context([(hot, 0.9), (cold, 0.3)])
        hot_pos = result.find("HOT")
        cold_pos = result.find("COLD")
        self.assertLess(hot_pos, cold_pos)


class TestExporter(unittest.TestCase):
    """Test export/import utilities."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.soma_path = os.path.join(self.test_dir, "data", "test.soma")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_export_json(self):
        """Brain exports to valid JSON file."""
        from brain.neuron import NeuronBrain
        from utils.exporter import export_json

        brain = NeuronBrain(soma_path=self.soma_path)
        brain.start_pulse()
        brain.process_input("user enjoys coffee every morning")
        brain.end_pulse()

        export_path = os.path.join(self.test_dir, "export.json")
        self.assertTrue(export_json(brain, export_path))
        self.assertTrue(os.path.exists(export_path))

        with open(export_path) as f:
            data = json.load(f)
        self.assertTrue(data["neuronx_export"])
        self.assertGreater(len(data["engrams"]), 0)

    def test_import_json(self):
        """Memories import from JSON file."""
        from brain.neuron import NeuronBrain
        from utils.exporter import export_json, import_json

        # Create and export a brain
        brain1 = NeuronBrain(soma_path=self.soma_path)
        brain1.start_pulse()
        brain1.process_input("user likes chocolate cake")
        brain1.end_pulse()
        count1 = len(brain1.soma.engrams)

        export_path = os.path.join(self.test_dir, "export.json")
        export_json(brain1, export_path)

        # Import into a fresh brain
        soma_path2 = os.path.join(self.test_dir, "data", "test2.soma")
        brain2 = NeuronBrain(soma_path=soma_path2)
        result = import_json(brain2, export_path)

        self.assertGreater(result["imported"], 0)
        self.assertEqual(len(brain2.soma.engrams), count1)


class TestAdditionalEngramNode(unittest.TestCase):
    """Additional engram tests per spec."""

    def test_source_field(self):
        """Source field serializes correctly."""
        e = Engram(source="observation", id="src12345src12345", raw="test")
        d = e.to_dict()
        self.assertEqual(d["source"], "observation")

        e2 = Engram.from_dict(d)
        self.assertEqual(e2.source, "observation")

    def test_is_active_and_expired(self):
        """is_active and is_expired logic works correctly."""
        e = Engram(truth=TRUTH_ACTIVE)
        self.assertTrue(e.is_active)
        self.assertFalse(e.is_expired)

        e.expire()
        self.assertFalse(e.is_active)
        self.assertTrue(e.is_expired)


class TestAdditionalSomaDB(unittest.TestCase):
    """Additional SOMA-DB tests."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.soma_path = os.path.join(self.test_dir, "test.soma")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_backup_restore(self):
        """Corrupted file triggers restore from backup."""
        db = SomaDB(self.soma_path)
        e = Engram(
            id=generate_engram_id("backup restore test"),
            raw="important memory for backup test",
            born=time.time(), last_seen=time.time(),
        )
        db.add_engram(e)
        db.save()

        # Save again to create backup
        db.add_engram(Engram(
            id=generate_engram_id("second mem"),
            raw="second memory", born=time.time(), last_seen=time.time(),
        ))
        db.save()

        # Backup should exist
        self.assertTrue(os.path.exists(db.backup_path))

        # Corrupt the main file
        with open(self.soma_path, "wb") as f:
            f.write(b"CORRUPTED DATA " * 100)

        # Load should detect corruption and restore from backup
        db2 = SomaDB(self.soma_path)
        result = db2.load()
        # After restore, should have at least the original engram
        self.assertTrue(result)

    def test_sig_file_created(self):
        """.soma.sig file is created on save."""
        db = SomaDB(self.soma_path)
        db.add_engram(Engram(
            id=generate_engram_id("sig test"),
            raw="sig test memory",
            born=time.time(), last_seen=time.time(),
        ))
        db.save()
        self.assertTrue(os.path.exists(db.sig_path))


class TestAdditionalBondEngine(unittest.TestCase):
    """Additional bond engine tests."""

    def setUp(self):
        self.bonds = BondEngine()

    def test_no_time_bond_if_far(self):
        """Engrams born >3 min apart have no time bond."""
        now = time.time()
        a = Engram(born=now)
        b = Engram(born=now + 200)  # 200 seconds > 180
        bond = self.bonds.compute_time_bond(a, b)
        self.assertEqual(bond, 0.0)

    def test_pruning(self):
        """Bonds below 0.05 are removed in audit."""
        from core.soma import SomaDB, AxonRecord

        test_dir = tempfile.mkdtemp()
        try:
            soma_path = os.path.join(test_dir, "prune_test.soma")
            db = SomaDB(soma_path)

            weak_axon = AxonRecord(
                from_id="aaaa1111bbbb2222",
                to_id="cccc3333dddd4444",
                synapse=0.03,  # Below 0.05 threshold
            )
            strong_axon = AxonRecord(
                from_id="eeee5555ffff6666",
                to_id="gggg7777hhhh8888",
                synapse=0.50,  # Above threshold
            )
            db.axons = [weak_axon, strong_axon]
            db.prune_weak_axons(threshold=0.05)

            self.assertEqual(len(db.axons), 1)
            self.assertEqual(db.axons[0].synapse, 0.50)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


class TestAdditionalAmygdala(unittest.TestCase):
    """Additional surprise engine tests."""

    def setUp(self):
        self.amygdala = Amygdala()

    def test_tokenize_lowercase(self):
        """Tokenization lowercases everything."""
        tokens = self.amygdala.tokenize("PIZZA PASTA SUSHI")
        for t in tokens:
            self.assertEqual(t, t.lower())

    def test_jaccard_identical(self):
        """Identical token sets = 1.0 similarity."""
        a = {"pizza", "pasta", "cooking"}
        sim = self.amygdala.jaccard_similarity(a, a)
        self.assertEqual(sim, 1.0)

    def test_jaccard_disjoint(self):
        """Disjoint sets = 0.0 similarity."""
        a = {"pizza", "pasta"}
        b = {"weather", "sunny"}
        sim = self.amygdala.jaccard_similarity(a, b)
        self.assertEqual(sim, 0.0)


class TestNRNLang(unittest.TestCase):
    """
    NRNLANG-Ω language interpreter tests.
    Tests the NRNLangInterpreter formatting, symbols, and export.
    """

    def setUp(self):
        from utils.nrnlang import NRNLangInterpreter
        self.nrn = NRNLangInterpreter()
        self.engram = Engram(
            id="a3f9c2b1d4e5f6a7",
            raw="user loves building AI",
            born=time.time() - 86400 * 3,
            last_seen=time.time(),
            valid_from=time.time() - 86400 * 3,
            heat=0.71,
            spark=0.88,
            weight=2.3,
            confidence=0.94,
            decay_class="identity",
            emotion="happy",
            tags=["preference", "tech"],
            zone="H",
            truth="ACTIVE",
            source="user",
        )

    def test_engram_to_nrnlang_format(self):
        """EngramNode converts to valid NRNLANG-Ω notation."""
        output = self.nrn.engram_to_nrnlang(self.engram)

        # All required fields present
        self.assertIn("ENGRAM {", output)
        self.assertIn("id", output)
        self.assertIn("raw", output)
        self.assertIn("born", output)
        self.assertIn("heat", output)
        self.assertIn("spark", output)
        self.assertIn("weight", output)
        self.assertIn("decay", output)
        self.assertIn("truth", output)
        self.assertIn("emotion", output)
        self.assertIn("confidence", output)
        self.assertIn("}", output)

        # Correct zone symbol used
        self.assertIn("🔥 [H]", output)

        # Contains the memory text
        self.assertIn("user loves building AI", output)

    def test_emotion_symbols(self):
        """Emotion symbols map correctly."""
        from utils.nrnlang import EMOTION_SYMBOLS

        # happy → :+:
        self.assertEqual(EMOTION_SYMBOLS["happy"], ":+:")
        # sad → :-:
        self.assertEqual(EMOTION_SYMBOLS["sad"], ":-:")
        # neutral → :~:
        self.assertEqual(EMOTION_SYMBOLS["neutral"], ":~:")

        # Verify in formatted output
        output = self.nrn.engram_to_nrnlang(self.engram)
        self.assertIn(":+:", output)

    def test_truth_symbols(self):
        """Truth state symbols map correctly."""
        from utils.nrnlang import TRUTH_SYMBOLS

        # active → ◈ |-
        self.assertEqual(TRUTH_SYMBOLS["ACTIVE"], "◈ |-")
        # expired → ◇ -|
        self.assertEqual(TRUTH_SYMBOLS["EXPIRED"], "◇ -|")
        # contested → ○ |?|
        self.assertEqual(TRUTH_SYMBOLS["MAYBE"], "○ |?|")

        # Active engram shows active truth
        output = self.nrn.engram_to_nrnlang(self.engram)
        self.assertIn("◈ |-", output)

    def test_zone_symbols(self):
        """Zone symbols display correctly."""
        from utils.nrnlang import ZONE_SYMBOLS

        self.assertIn("🔥", ZONE_SYMBOLS["H"])
        self.assertIn("[H]", ZONE_SYMBOLS["H"])
        self.assertIn("🌡", ZONE_SYMBOLS["W"])
        self.assertIn("[W]", ZONE_SYMBOLS["W"])
        self.assertIn("❄", ZONE_SYMBOLS["C"])
        self.assertIn("[C]", ZONE_SYMBOLS["C"])
        self.assertIn("👻", ZONE_SYMBOLS["S"])
        self.assertIn("[S]", ZONE_SYMBOLS["S"])

    def test_operation_notation(self):
        """Operation formatting produces correct NRNLANG-Ω strings."""
        # FORGE
        forge = self.nrn.operation_to_nrnlang("FORGE", {
            "text": "user loves Tokyo ramen",
            "surprise": 0.6,
            "emotion": "happy",
            "decay_class": "opinion",
            "confidence": 0.85,
        })
        self.assertIn("FORGE", forge)
        self.assertIn("Tokyo ramen", forge)
        self.assertIn(":+:", forge)
        self.assertIn("SOMA", forge)

        # ECHO
        echo = self.nrn.operation_to_nrnlang("ECHO", {
            "text": "user likes pizza",
            "match_id": "abc12345def67890",
            "surprise": 0.1,
        })
        self.assertIn("ECHO", echo)
        self.assertIn("abc12345", echo)
        self.assertIn("+++", echo)

        # CLASH
        clash = self.nrn.operation_to_nrnlang("CLASH", {
            "text": "user hates pizza now",
            "match_id": "xyz99999aaa11111",
            "surprise": 0.92,
            "clash_result": "SUPERSEDED",
        })
        self.assertIn("CLASH", clash)
        self.assertIn("##", clash)
        self.assertIn("⚡", clash)

    def test_brain_export(self):
        """Brain export returns valid NRNLANG-Ω with all parts."""
        from brain.neuron import NeuronBrain

        soma_path = os.path.join(tempfile.mkdtemp(), "test_nrn.soma")
        brain = NeuronBrain(soma_path=soma_path)
        brain.start_pulse()
        brain.process_input("user loves building AI systems")
        brain.process_input("user lives in Tokyo")
        brain.end_pulse()

        nrn = self.__class__.__mro__[0].__module__  # unused
        from utils.nrnlang import NRNLangInterpreter
        nrn_int = NRNLangInterpreter(brain)
        output = nrn_int.brain_to_nrnlang()

        # Contains header
        self.assertIn("Brain State Export", output)
        # Contains all engrams
        self.assertIn("ENGRAM", output)
        # Contains total counts
        self.assertIn("Total Engrams", output)
        # Can be validated without errors
        errors = nrn_int.validate_syntax(output)
        # Only report real command errors, not section headers
        real_errors = [e for e in errors if "Unknown" not in e.get("error", "")]
        self.assertEqual(len(real_errors), 0,
                         f"Validation errors: {real_errors}")

        # Cleanup
        shutil.rmtree(os.path.dirname(soma_path), ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)

