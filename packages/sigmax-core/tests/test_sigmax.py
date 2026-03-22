"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Complete Test Suite                      ║
║  100+ tests covering every component                      ║
╚══════════════════════════════════════════════════════════╝
"""

import json
import math
import os
import sys
import tempfile
import time

import pytest

# Add parent path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sigmax.config import *
from sigmax.exceptions import *
from sigmax.core.causenode import CauseNode
from sigmax.core.tokenizer import (
    tokenize, tokenize_unique, jaccard_similarity, word_overlap,
    causal_resonance, detect_causal_signals, has_causal_language,
    split_causal_text, extract_subjects, normalize_text, compute_text_hash,
)
from sigmax.core.integrity import (
    generate_node_id, generate_brain_id, generate_prediction_id,
    sha256_bytes, sha256_hex, sha256_dict, sha256_nodes,
    IntegritySeal, NMPLock,
)
from sigmax.core.causadb import CausaDB
from sigmax.core.sigma import sigma_score, sigma_rank, sigma_score_breakdown
from sigmax.core.evidence import EvidenceEngine, EvidenceRecord
from sigmax.core.zones import ZoneManager
from sigmax.utils.compressor import (
    zlib_compress, zlib_decompress, lzma_compress, lzma_decompress,
    auto_compress, compression_ratio, COMPRESS_NONE, COMPRESS_ZLIB,
)
from sigmax.brain.chain_builder import ChainBuilder
from sigmax.brain.predictor import PredictionEngine, Prediction
from sigmax.brain.counterfactual import CounterfactualEngine, Counterfactual
from sigmax.brain.multihop import MultiHopBuilder, CausalPath
from sigmax.brain.axiom_engine import AxiomEngine
from sigmax.brain.neuronx_bridge import NeuronXBridge
from sigmax.brain.injector import ContextInjector
from sigmax.brain.scheduler import Scheduler
from sigmax.brain.sigma_brain import SigmaBrain
from sigmax.language.symbols import get_symbol, lookup_symbol, ALL_SYMBOLS
from sigmax.language.keywords import is_keyword, get_category
from sigmax.language.grammar import validate_chain_notation, CaulangEmitter
from sigmax.utils.exporter import export_json, export_markdown, export_csv, import_json
from sigmax.utils.events import EventBus, SigmaEvent
from sigmax.utils.metrics import compute_brain_health, compute_file_metrics
from sigmax.utils.crypto import encrypt, decrypt, hash_passphrase, verify_passphrase
from sigmax.language.caulang import parse_chain, parse_chains, parse_session, to_causenode, ParsedChain


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIXTURES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.fixture
def sample_node():
    return CauseNode(cause="rain", effect="wet roads", cause_type="direct",
                     confidence=0.75, tags=["weather"])


@pytest.fixture
def tmp_sigma(tmp_path):
    return str(tmp_path / "test_brain.sigma")


@pytest.fixture
def brain(tmp_path):
    path = str(tmp_path / "test.sigma")
    return SigmaBrain(path)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. CONFIG TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_config_magic_bytes():
    assert CAUSADB_MAGIC == b'\x53\x49\x47\xCE'
    assert len(CAUSADB_MAGIC) == 4

def test_config_sigma_weights():
    assert SIGMA_CAUSAL_RESONANCE == 3.0
    assert SIGMA_EVIDENCE_WEIGHT == 2.5
    assert SIGMA_TOTAL_WEIGHT > 0

def test_config_decay_rates():
    assert CAUSAL_DECAY_RATES["permanent"] == 0.0
    assert CAUSAL_DECAY_RATES["fast"] > CAUSAL_DECAY_RATES["medium"]

def test_config_zones():
    assert ZONE_ACTIVE == "ACTIVE"
    assert ZONE_AXIOM == "AXIOM"

def test_config_caulang_symbols():
    assert "~>~" in CAULANG_CHAIN_SYMBOLS.values()
    assert len(CAULANG_KEYWORDS) > 20

def test_config_signal_words():
    assert "because" in CAUSAL_SIGNAL_WORDS
    assert "the" not in CAUSAL_SIGNAL_WORDS


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. EXCEPTION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_exception_hierarchy():
    assert issubclass(CausaDBError, SigmaXError)
    assert issubclass(CausaDBCorruptionError, CausaDBError)
    assert issubclass(CauseNodeValidationError, CauseNodeError)
    assert issubclass(PredictionNotFoundError, PredictionError)
    assert issubclass(IntegritySealError, IntegrityError)

def test_exception_catchable():
    with pytest.raises(SigmaXError):
        raise CausaDBCorruptionError("test")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. CAUSENODE TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_causenode_creation(sample_node):
    assert sample_node.cause == "rain"
    assert sample_node.effect == "wet roads"
    assert sample_node.cause_type == "direct"
    assert sample_node.confidence == 0.75

def test_causenode_25_fields():
    node = CauseNode(cause="a", effect="b")
    fields = list(node.__dataclass_fields__.keys())
    assert len(fields) == 25
    assert 'chain_id' in fields

def test_causenode_validation_empty_cause():
    with pytest.raises(CauseNodeValidationError):
        CauseNode(cause="", effect="test")

def test_causenode_validation_bad_type():
    with pytest.raises(CauseNodeValidationError):
        CauseNode(cause="a", effect="b", cause_type="invalid")

def test_causenode_validation_bad_decay():
    with pytest.raises(CauseNodeValidationError):
        CauseNode(cause="a", effect="b", decay_class="invalid")

def test_causenode_confidence_clamp():
    n = CauseNode(cause="a", effect="b", confidence=5.0)
    assert n.confidence == 1.0
    n2 = CauseNode(cause="a", effect="b", confidence=-1.0)
    assert n2.confidence == 0.01

def test_causenode_weight_clamp():
    n = CauseNode(cause="a", effect="b", weight=99.0)
    assert n.weight == MAX_CHAIN_WEIGHT

def test_causenode_evidence(sample_node):
    sample_node.add_evidence(is_support=True)
    assert sample_node.evidence_for == 1
    assert sample_node.evidence_net == 1
    sample_node.add_evidence(is_support=False)
    assert sample_node.evidence_against == 1

def test_causenode_predictions(sample_node):
    sample_node.record_prediction(correct=True)
    assert sample_node.predictions_made == 1
    assert sample_node.predictions_correct == 1
    assert sample_node.prediction_accuracy == 1.0

def test_causenode_heat(sample_node):
    heat = sample_node.get_heat()
    assert 0.0 <= heat <= 1.0

def test_causenode_zone_compute(sample_node):
    zone = sample_node.compute_zone()
    assert zone in [ZONE_ACTIVE, ZONE_WARM, ZONE_DORMANT, ZONE_AXIOM, ZONE_ARCHIVED]

def test_causenode_touch(sample_node):
    old_count = sample_node.access_count
    sample_node.touch()
    assert sample_node.access_count == old_count + 1

def test_causenode_strengthen(sample_node):
    old_weight = sample_node.weight
    sample_node.strengthen(0.5)
    assert sample_node.weight > old_weight

def test_causenode_caulang(sample_node):
    notation = sample_node.to_caulang()
    assert "rain" in notation
    assert "wet roads" in notation
    assert "~>~" in notation

def test_causenode_serialization(sample_node):
    d = sample_node.to_dict()
    restored = CauseNode.from_dict(d)
    assert restored.cause == sample_node.cause
    assert restored.effect == sample_node.effect
    assert restored.confidence == sample_node.confidence

def test_causenode_summary(sample_node):
    s = sample_node.to_summary()
    assert "rain" in s
    assert "wet roads" in s

def test_causenode_crystallize():
    n = CauseNode(cause="gravity", effect="objects fall", confidence=0.96,
                  access_count=20, evidence_for=12, decay_class="slow")
    assert n.crystallize() is True
    assert n.zone == ZONE_AXIOM
    assert n.decay_class == "permanent"

def test_causenode_crystallize_fail():
    n = CauseNode(cause="maybe", effect="perhaps", confidence=0.30)
    assert n.crystallize() is False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. TOKENIZER TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_tokenize_basic():
    tokens = tokenize("Rain causes wet roads")
    assert "rain" in tokens
    assert "wet" in tokens
    assert "roads" in tokens

def test_tokenize_stops_removed():
    tokens = tokenize("The rain and the wind")
    assert "the" not in tokens
    assert "and" not in tokens
    assert "rain" in tokens

def test_tokenize_empty():
    assert tokenize("") == []
    assert tokenize(None) == []

def test_jaccard():
    a = {"rain", "wet", "road"}
    b = {"rain", "wet", "car"}
    j = jaccard_similarity(a, b)
    assert 0.0 < j < 1.0
    assert jaccard_similarity(a, a) == 1.0
    assert jaccard_similarity(set(), set()) == 0.0

def test_word_overlap():
    sim = word_overlap("rain causes wet roads", "heavy rain makes roads wet")
    assert sim > 0.0

def test_causal_resonance_score():
    score = causal_resonance("why is road wet", "rain", "wet road")
    assert score > 0.0

def test_detect_signals():
    signals = detect_causal_signals("Rain causes flooding because of drainage")
    assert "because" in signals
    assert "causes" in signals

def test_has_causal():
    assert has_causal_language("rain causes wet roads") is True
    assert has_causal_language("hello world") is False

def test_normalize():
    assert normalize_text("  Hello,  World! ") == "hello world"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. INTEGRITY TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_generate_ids():
    nid = generate_node_id()
    assert len(nid) == 32
    bid = generate_brain_id()
    assert len(bid) == 16

def test_sha256():
    h = sha256_hex(b"test")
    assert len(h) == 64
    assert sha256_hex(b"test") == h  # deterministic

def test_sha256_dict():
    d = {"key": "value"}
    h = sha256_dict(d)
    assert len(h) == 64

def test_integrity_seal():
    data = b"test node data"
    seal = IntegritySeal.create(data, node_count=5)
    assert seal.node_count == 5
    assert seal.verify(data) is True
    assert seal.verify(b"tampered") is False

def test_integrity_seal_pack_unpack():
    data = b"roundtrip test"
    seal = IntegritySeal.create(data, 10)
    packed = seal.pack()
    assert len(packed) == CAUSADB_SEAL_SIZE
    restored = IntegritySeal.unpack(packed)
    assert restored.node_count == 10
    assert restored.verify(data) is True

def test_nmp_lock(tmp_path):
    path = str(tmp_path / "test.sigma")
    lock = NMPLock(path)
    assert lock.acquire() is True
    assert lock.is_locked is True
    lock.release()
    assert lock.is_locked is False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. CAUSADB TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_causadb_save_load(tmp_sigma):
    nodes = [
        CauseNode(cause="rain", effect="wet roads"),
        CauseNode(cause="sun", effect="dry roads"),
    ]
    CausaDB.save(tmp_sigma, nodes)
    loaded, edges, preds = CausaDB.load(tmp_sigma)
    assert len(loaded) == 2
    assert loaded[0].cause == "rain"

def test_causadb_verify(tmp_sigma):
    nodes = [CauseNode(cause="test", effect="verify")]
    CausaDB.save(tmp_sigma, nodes)
    assert CausaDB.verify(tmp_sigma) is True

def test_causadb_empty(tmp_sigma):
    CausaDB.save(tmp_sigma, [])
    loaded, _, _ = CausaDB.load(tmp_sigma)
    assert len(loaded) == 0

def test_causadb_info(tmp_sigma):
    nodes = [CauseNode(cause="a", effect="b")]
    CausaDB.save(tmp_sigma, nodes)
    info = CausaDB.get_info(tmp_sigma)
    assert info['node_count'] == 1
    assert info['magic_valid'] is True

def test_causadb_corruption(tmp_sigma):
    with open(tmp_sigma, 'wb') as f:
        f.write(b"garbage data here!!!")
    with pytest.raises(CausaDBCorruptionError):
        CausaDB.load(tmp_sigma)

def test_causadb_ensure_path():
    assert CausaDB.ensure_path("brain").endswith(".sigma")
    assert CausaDB.ensure_path("brain.sigma") == "brain.sigma"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. SIGMA SCORING TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_sigma_score_basic(sample_node):
    score = sigma_score(sample_node, "rain wet roads")
    assert 0.0 <= score <= 1.0

def test_sigma_score_irrelevant(sample_node):
    high = sigma_score(sample_node, "rain wet roads")
    low = sigma_score(sample_node, "quantum physics dark matter")
    assert high > low

def test_sigma_rank():
    nodes = [
        CauseNode(cause="rain", effect="wet roads"),
        CauseNode(cause="sun", effect="dry roads"),
        CauseNode(cause="ice", effect="slippery roads"),
    ]
    ranked = sigma_rank(nodes, "why is road wet from rain")
    assert len(ranked) > 0
    assert ranked[0][1] >= ranked[-1][1]

def test_sigma_breakdown(sample_node):
    bd = sigma_score_breakdown(sample_node, "rain causes wet roads")
    assert 'total_score' in bd
    assert 'components' in bd
    assert len(bd['components']) == 9


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. EVIDENCE ENGINE TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_evidence_support(sample_node):
    engine = EvidenceEngine()
    record = engine.add_support(sample_node, "Observed rain → wet road")
    assert record.is_support is True
    assert sample_node.evidence_for == 1

def test_evidence_contradiction(sample_node):
    engine = EvidenceEngine()
    engine.add_contradiction(sample_node, "Road was dry in rain")
    assert sample_node.evidence_against == 1

def test_evidence_score(sample_node):
    engine = EvidenceEngine()
    for _ in range(5):
        engine.add_support(sample_node, "support")
    score = engine.compute_evidence_score(sample_node)
    assert score > 0.0

def test_evidence_summary(sample_node):
    engine = EvidenceEngine()
    engine.add_support(sample_node, "yes")
    summary = engine.get_evidence_summary(sample_node)
    assert summary['support_count'] == 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. ZONE MANAGER TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_zone_assignment(sample_node):
    zm = ZoneManager()
    zone = zm.assign_zone(sample_node)
    assert zone in [ZONE_ACTIVE, ZONE_WARM, ZONE_DORMANT, ZONE_AXIOM, ZONE_ARCHIVED]

def test_zone_distribution():
    zm = ZoneManager()
    nodes = [CauseNode(cause=f"c{i}", effect=f"e{i}") for i in range(10)]
    dist = zm.assign_zones_bulk(nodes)
    assert sum(dist.values()) == 10

def test_zone_summary():
    zm = ZoneManager()
    nodes = [CauseNode(cause="a", effect="b")]
    summary = zm.get_zone_summary(nodes)
    assert "ZONE DISTRIBUTION" in summary


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. COMPRESSOR TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_zlib_roundtrip():
    data = b"test data " * 100
    compressed = zlib_compress(data)
    assert len(compressed) < len(data)
    assert zlib_decompress(compressed) == data

def test_lzma_roundtrip():
    data = b"test data " * 100
    compressed = lzma_compress(data)
    assert lzma_decompress(compressed) == data

def test_auto_compress_small():
    data = b"tiny"
    compressed, method = auto_compress(data)
    assert method == COMPRESS_NONE


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 11. CHAIN BUILDER TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_chain_extract_direct():
    builder = ChainBuilder()
    nodes = builder.extract("Rain causes wet roads")
    assert len(nodes) >= 1
    assert any("rain" in n.cause.lower() for n in nodes)

def test_chain_extract_because():
    builder = ChainBuilder()
    nodes = builder.extract("The road is wet because it rained heavily")
    assert len(nodes) >= 1

def test_chain_extract_prevents():
    builder = ChainBuilder()
    nodes = builder.extract("Sunscreen prevents sunburn effectively")
    assert len(nodes) >= 1
    assert any(n.cause_type == "inhibitory" for n in nodes)

def test_chain_extract_conditional():
    builder = ChainBuilder()
    nodes = builder.extract("If temperature drops below zero, then water freezes")
    assert len(nodes) >= 1

def test_chain_extract_empty():
    builder = ChainBuilder()
    assert builder.extract("") == []
    assert builder.extract("Hello world") == []

def test_chain_find_duplicates():
    builder = ChainBuilder()
    n1 = [CauseNode(cause="rain", effect="wet roads")]
    n2 = [CauseNode(cause="heavy rain", effect="wet road surfaces")]
    dups = builder.find_duplicates(n2, n1, threshold=0.30)
    assert len(dups) >= 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 12. PREDICTION ENGINE TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_prediction_create(sample_node):
    engine = PredictionEngine()
    pred = engine.generate(sample_node, "Roads will flood", horizon="short")
    assert pred.status == "pending"
    assert pred.horizon == "short"

def test_prediction_verify(sample_node):
    engine = PredictionEngine()
    pred = engine.generate(sample_node, "test prediction")
    result = engine.verify(pred.id, True, "confirmed", sample_node)
    assert result.status == "verified"
    assert sample_node.predictions_correct == 1

def test_prediction_falsify(sample_node):
    engine = PredictionEngine()
    pred = engine.generate(sample_node, "wrong prediction")
    result = engine.verify(pred.id, False, "wrong", sample_node)
    assert result.status == "falsified"

def test_prediction_accuracy(sample_node):
    engine = PredictionEngine()
    for _ in range(3):
        p = engine.generate(sample_node, "p")
        engine.verify(p.id, True, "", sample_node)
    p = engine.generate(sample_node, "p")
    engine.verify(p.id, False, "", sample_node)
    assert 0.5 < engine.get_accuracy() < 1.0

def test_prediction_not_found():
    engine = PredictionEngine()
    with pytest.raises(PredictionNotFoundError):
        engine.verify("nonexistent", True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 13. COUNTERFACTUAL TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_counterfactual_create(sample_node):
    engine = CounterfactualEngine()
    cf = engine.generate(sample_node, "no rain", "dry roads", 0.80)
    assert cf.plausibility == 0.80
    assert sample_node.counterfactual_count == 1

def test_counterfactual_limit(sample_node):
    engine = CounterfactualEngine()
    for i in range(COUNTERFACTUAL_MAX_PER_CHAIN):
        engine.generate(sample_node, f"cf{i}", f"eff{i}")
    with pytest.raises(CounterfactualLimitError):
        engine.generate(sample_node, "one more", "fail")

def test_counterfactual_min_confidence():
    node = CauseNode(cause="maybe", effect="perhaps", confidence=0.10)
    engine = CounterfactualEngine()
    with pytest.raises(CounterfactualError):
        engine.generate(node)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 14. MULTI-HOP TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_multihop_build_graph():
    nodes = [
        CauseNode(cause="rain", effect="wet ground"),
        CauseNode(cause="wet ground", effect="mud"),
        CauseNode(cause="mud", effect="dirty shoes"),
    ]
    builder = MultiHopBuilder(link_threshold=0.30)
    graph = builder.build_graph(nodes)
    assert len(graph) == 3

def test_multihop_find_paths():
    nodes = [
        CauseNode(cause="rain", effect="wet ground"),
        CauseNode(cause="wet ground", effect="flooding"),
    ]
    builder = MultiHopBuilder(link_threshold=0.30)
    paths = builder.find_paths(nodes)
    # May find paths if word overlap is sufficient
    assert isinstance(paths, list)

def test_causal_path():
    nodes = [
        CauseNode(cause="rain", effect="wet"),
        CauseNode(cause="wet", effect="mud"),
    ]
    path = CausalPath(nodes)
    assert path.depth == 2
    assert path.cause == "rain"
    assert path.effect == "mud"
    d = path.to_dict()
    assert d['depth'] == 2


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 15. AXIOM ENGINE TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_axiom_check_candidate():
    engine = AxiomEngine()
    node = CauseNode(cause="gravity", effect="fall", confidence=0.96,
                     access_count=20, evidence_for=12)
    eligible, unmet = engine.check_candidate(node)
    assert eligible is True

def test_axiom_check_unmet():
    engine = AxiomEngine()
    node = CauseNode(cause="maybe", effect="perhaps", confidence=0.30)
    eligible, unmet = engine.check_candidate(node)
    assert eligible is False
    assert len(unmet) > 0

def test_axiom_scan():
    engine = AxiomEngine()
    nodes = [
        CauseNode(cause="gravity", effect="fall", confidence=0.96,
                  access_count=20, evidence_for=12),
        CauseNode(cause="maybe", effect="no", confidence=0.30),
    ]
    crystallized = engine.scan_and_crystallize(nodes)
    assert len(crystallized) == 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 16. BRIDGE TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_bridge_not_connected():
    bridge = NeuronXBridge()
    assert bridge.is_connected is False
    with pytest.raises(BridgeNotConnectedError):
        bridge.pull_memories("test")

def test_bridge_connect():
    bridge = NeuronXBridge()
    mock_brain = type('MockBrain', (), {'recall': lambda s, q, **k: []})()
    bridge.connect(mock_brain)
    assert bridge.is_connected is True
    bridge.disconnect()
    assert bridge.is_connected is False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 17. INJECTOR TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_injector_format():
    inj = ContextInjector()
    node = CauseNode(cause="rain", effect="flood", confidence=0.80)
    context = inj.format_context([(node, 0.85)])
    assert "rain" in context
    assert "flood" in context

def test_injector_system_prompt():
    inj = ContextInjector()
    node = CauseNode(cause="a", effect="b")
    prompt = inj.build_system_prompt([(node, 0.5)])
    assert "SIGMA-X" in prompt


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 18. SCHEDULER TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_scheduler_tick():
    s = Scheduler(audit_interval=5)
    for _ in range(4):
        assert s.tick() is False
    assert s.tick() is True

def test_scheduler_audit():
    s = Scheduler()
    zm = ZoneManager()
    nodes = [CauseNode(cause="a", effect="b")]
    result = s.run_audit(nodes, zone_manager=zm)
    assert 'zone_audit' in result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 19. CAULANG TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_caulang_symbols():
    assert len(ALL_SYMBOLS) > 30
    assert get_symbol("chain", "DIRECT") == "~>~"

def test_caulang_keywords():
    assert is_keyword("CAUSENODE") is True
    assert is_keyword("hello") is False
    assert get_category("PREDICT") == "reasoning"

def test_caulang_validate():
    valid, err = validate_chain_notation('"rain" ~>~ "wet roads"')
    assert valid is True

def test_caulang_validate_bad():
    valid, err = validate_chain_notation("no chain here")
    assert valid is False

def test_caulang_emitter():
    emitter = CaulangEmitter()
    node = CauseNode(cause="rain", effect="flood")
    notation = emitter.emit_chain(node)
    assert "rain" in notation


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 20. EXPORTER TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_export_json():
    nodes = [CauseNode(cause="rain", effect="wet")]
    j = export_json(nodes)
    data = json.loads(j)
    assert data['chain_count'] == 1

def test_export_markdown():
    nodes = [CauseNode(cause="rain", effect="wet")]
    md = export_markdown(nodes)
    assert "rain" in md

def test_export_csv():
    nodes = [CauseNode(cause="rain", effect="wet")]
    c = export_csv(nodes)
    assert "rain" in c

def test_import_json():
    nodes = [CauseNode(cause="rain", effect="wet")]
    j = export_json(nodes)
    imported = import_json(j)
    assert len(imported) == 1
    assert imported[0].cause == "rain"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 21. EVENT BUS TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_event_bus():
    bus = EventBus()
    received = []
    bus.on("test", lambda e: received.append(e))
    bus.emit("test", {"key": "value"})
    assert len(received) == 1
    assert received[0].data['key'] == "value"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 22. METRICS TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_brain_health_empty():
    health = compute_brain_health([])
    assert health['status'] == 'EMPTY'

def test_brain_health():
    nodes = [CauseNode(cause=f"c{i}", effect=f"e{i}",
                       confidence=0.70) for i in range(10)]
    health = compute_brain_health(nodes)
    assert health['health_score'] > 0
    assert health['total_chains'] == 10


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 23. SIGMA BRAIN TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_brain_creation(brain):
    assert brain.node_count == 0
    assert brain.brain_id is not None

def test_brain_add_chain(brain):
    node = brain.add_chain("rain", "wet roads")
    assert node.cause == "rain"
    assert brain.node_count == 1

def test_brain_duplicate_detection(brain):
    brain.add_chain("rain", "wet roads")
    with pytest.raises(CauseNodeDuplicateError):
        brain.add_chain("rain", "wet roads")

def test_brain_think(brain):
    nodes = brain.think("Rain causes wet roads")
    assert len(nodes) >= 1
    assert brain.node_count >= 1

def test_brain_reason(brain):
    brain.add_chain("rain", "wet roads")
    brain.add_chain("sun", "dry roads")
    results = brain.reason("why is road wet")
    assert len(results) > 0

def test_brain_save_load(brain):
    brain.add_chain("rain", "wet roads")
    brain.add_chain("sun", "dry roads")
    brain.save()
    brain2 = SigmaBrain(brain.path)
    assert brain2.node_count == 2

def test_brain_get_chain(brain):
    node = brain.add_chain("fire", "smoke")
    retrieved = brain.get_chain(node.id)
    assert retrieved.cause == "fire"

def test_brain_delete_chain(brain):
    node = brain.add_chain("test", "delete")
    assert brain.delete_chain(node.id) is True
    assert brain.node_count == 0

def test_brain_predict(brain):
    node = brain.add_chain("rain", "wet roads")
    pred = brain.predict(node.id, "flooding will occur", horizon="short")
    assert pred['status'] == "pending"

def test_brain_stats(brain):
    brain.add_chain("a", "b")
    stats = brain.stats
    assert stats['node_count'] == 1
    assert 'predictions' in stats

def test_brain_integrity(brain):
    brain.add_chain("test", "integrity")
    brain.save()
    assert brain.verify_integrity() is True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 24. CRYPTO TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_crypto_encrypt_decrypt():
    data = b"SIGMA-X causal chain data for encryption"
    passphrase = "sigma-secret-key"
    encrypted = encrypt(data, passphrase)
    assert encrypted != data
    decrypted = decrypt(encrypted, passphrase)
    assert decrypted == data

def test_crypto_wrong_passphrase():
    data = b"sensitive causal data"
    encrypted = encrypt(data, "correct-password")
    with pytest.raises(ValueError, match="wrong passphrase"):
        decrypt(encrypted, "wrong-password")

def test_crypto_empty():
    assert encrypt(b"", "pass") == b""
    assert decrypt(b"", "pass") == b""

def test_crypto_large_data():
    data = b"causal chain " * 10000  # 130KB
    encrypted = encrypt(data, "key123")
    decrypted = decrypt(encrypted, "key123")
    assert decrypted == data

def test_crypto_passphrase_hash():
    stored = hash_passphrase("my-secret")
    assert ':' in stored
    assert verify_passphrase("my-secret", stored) is True
    assert verify_passphrase("wrong", stored) is False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 25. CAULANG PARSER TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_parse_chain_basic():
    pc = parse_chain('"rain" ~>~ "wet roads"')
    assert pc.cause == "rain"
    assert pc.effect == "wet roads"
    assert pc.cause_type == "direct"

def test_parse_chain_with_confidence():
    pc = parse_chain('"study" ~>~ "good grades" (!)')
    assert pc.confidence_label == "strong"

def test_parse_chain_with_evidence():
    pc = parse_chain('"rain" ~>~ "flood" (~) [+5/-2]')
    assert pc.evidence_for == 5
    assert pc.evidence_against == 2

def test_parse_chain_with_predictions():
    pc = parse_chain('"fire" ~>~ "smoke" (!) [+3/-0] {4/5 80%}')
    assert pc.predictions_correct == 4
    assert pc.predictions_total == 5

def test_parse_chain_inhibitory():
    pc = parse_chain('"vaccine" ~|~ "disease"')
    assert pc.cause_type == "inhibitory"

def test_parse_chains_multi():
    text = '''"rain" ~>~ "flood" (!)
"sun" ~>~ "dry" (~)
# this is a comment
"cold" ~|~ "growth" (?)'''
    chains = parse_chains(text)
    assert len(chains) == 3

def test_parse_chain_empty():
    with pytest.raises(CaulangParseError):
        parse_chain("")

def test_parse_to_causenode():
    pc = parse_chain('"gravity" ~>~ "objects fall" (!)')
    node = to_causenode(pc)
    assert node.cause == "gravity"
    assert node.effect == "objects fall"
    assert node.confidence >= 0.80

def test_parse_round_trip():
    node = CauseNode(cause="rain", effect="flood", confidence=0.85)
    notation = node.to_caulang()
    pc = parse_chain(notation)
    assert pc.cause == "rain"
    assert pc.effect == "flood"

def test_parse_session():
    text = """╔══╗ SESSION_BEGIN
"rain" ~>~ "flood" (!)
"sun" ~>~ "dry" (~)
╚══╝ SESSION_END"""
    session = parse_session(text)
    assert len(session.chains) == 2


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 26. PUBLIC API IMPORT TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_public_api_imports():
    import sigmax
    assert hasattr(sigmax, 'SigmaBrain')
    assert hasattr(sigmax, 'CauseNode')
    assert hasattr(sigmax, 'CausaDB')
    assert hasattr(sigmax, 'sigma_score')
    assert hasattr(sigmax, 'encrypt')
    assert hasattr(sigmax, 'parse_chain')

def test_causenode_chain_id():
    node = CauseNode(cause="a", effect="b", chain_id="chain_001")
    assert node.chain_id == "chain_001"
    d = node.to_dict()
    assert d['chain_id'] == "chain_001"
