"""Tests for Phase 1-2: Foundation + Storage (config, exceptions, thought_node, integrity, tokenizer, cortexdb)."""
import os
import time
import tempfile
import pytest

# ━━━ CONFIG ━━━
from cortex.config import (
    CORTEXDB_MAGIC, CORTEXDB_VERSION, CORTEXDB_HEADER_FORMAT,
    METACOG_CONFIDENCE_CALIBRATION, METACOG_TOTAL_WEIGHT,
    CONFIDENCE_WINDOW_SIZE, HALLUCINATION_EVIDENCE_THRESHOLD,
    STOP_WORDS, ZONE_FOCUSED, ZONE_EXPLORING,
    CORTEXLANG_META_SYMBOLS, CORTEXLANG_KEYWORDS,
    SUPPORTED_LLMS, GROWTH_DIMENSION_WEIGHTS,
)

def test_magic_bytes():
    assert CORTEXDB_MAGIC == b'\x43\x54\x58\xCE'

def test_version_format():
    assert CORTEXDB_VERSION == 1

def test_metacog_weights_positive():
    assert METACOG_CONFIDENCE_CALIBRATION > 0
    assert METACOG_TOTAL_WEIGHT > 0

def test_stop_words_is_frozenset():
    assert isinstance(STOP_WORDS, frozenset)
    assert "the" in STOP_WORDS

def test_zones_defined():
    assert ZONE_FOCUSED == "FOCUSED"
    assert ZONE_EXPLORING == "EXPLORING"

def test_symbols_nonempty():
    assert len(CORTEXLANG_META_SYMBOLS) > 10

def test_keywords_categories():
    assert "metacognition" in CORTEXLANG_KEYWORDS
    assert "confidence" in CORTEXLANG_KEYWORDS

def test_supported_llms():
    assert "ollama" in SUPPORTED_LLMS
    assert "anthropic" in SUPPORTED_LLMS

def test_growth_weights():
    assert "accuracy_delta" in GROWTH_DIMENSION_WEIGHTS

# ━━━ EXCEPTIONS ━━━
from cortex.exceptions import (
    CortexError, CortexDBError, CortexDBCorruptionError,
    ThoughtNodeError, MetacogError, CortexLangError,
    LLMAdapterError, ToolNotFoundError, NeuronXSyncError,
)

def test_exception_hierarchy():
    assert issubclass(CortexDBError, CortexError)
    assert issubclass(CortexDBCorruptionError, CortexDBError)
    assert issubclass(ThoughtNodeError, CortexError)
    assert issubclass(MetacogError, CortexError)

def test_exception_message():
    e = CortexDBError("test")
    assert str(e) == "test"

def test_llm_exception():
    assert issubclass(LLMAdapterError, CortexError)

def test_tool_exception():
    assert issubclass(ToolNotFoundError, CortexError)

def test_bridge_exception():
    assert issubclass(NeuronXSyncError, CortexError)

# ━━━ THOUGHT NODE ━━━
from cortex.core.thought_node import ThoughtNode

def test_thought_creation():
    t = ThoughtNode(content="hello world", context="test")
    assert t.content == "hello world"
    assert t.id != ""
    assert t.confidence == 0.6

def test_thought_id_unique():
    t1 = ThoughtNode(content="a", context="b")
    t2 = ThoughtNode(content="a", context="b")
    assert t1.id != t2.id

def test_thought_defaults():
    t = ThoughtNode(content="x")
    assert t.zone == ZONE_FOCUSED
    assert t.thought_type == "response"
    assert t.version == 1
    assert t.was_corrected is False

def test_thought_correct():
    t = ThoughtNode(content="wrong answer")
    t.correct("fixed", 0.9)
    assert t.was_corrected is True
    assert t.version == 2
    assert t.correction_note == "fixed"

def test_thought_verify():
    t = ThoughtNode(content="test")
    t.verify(0.8)
    assert t.actual_accuracy == 0.8
    assert t.is_verified is True

def test_thought_crystallize():
    t = ThoughtNode(content="wisdom")
    t.crystallize()
    assert t.is_wisdom is True

def test_thought_to_dict():
    t = ThoughtNode(content="test", context="ctx")
    d = t.to_dict()
    assert d["content"] == "test"
    assert "id" in d

def test_thought_from_dict():
    t = ThoughtNode(content="roundtrip")
    d = t.to_dict()
    t2 = ThoughtNode.from_dict(d)
    assert t2.content == "roundtrip"
    assert t2.id == t.id

def test_thought_age():
    t = ThoughtNode(content="old")
    assert t.age_seconds >= 0

def test_thought_effective_confidence():
    t = ThoughtNode(content="test", confidence=0.8)
    ec = t.effective_confidence
    assert 0 <= ec <= 1

def test_thought_tags():
    t = ThoughtNode(content="test", tags=["python", "code"])
    assert "python" in t.tags

# ━━━ INTEGRITY ━━━
from cortex.core.integrity import (
    sha256_bytes, sha256_hex, sha256_str, sha256_dict,
    generate_id, thought_id, session_id, strategy_id,
    pattern_id, brain_id, wisdom_id,
    IntegritySeal, CMPLock,
)

def test_sha256_bytes():
    h = sha256_bytes(b"hello")
    assert len(h) == 32

def test_sha256_hex():
    h = sha256_hex(b"hello")
    assert len(h) == 64

def test_sha256_str():
    h = sha256_str("hello")
    assert len(h) == 64

def test_sha256_dict():
    h = sha256_dict({"a": 1, "b": 2})
    assert len(h) == 64
    h2 = sha256_dict({"b": 2, "a": 1})
    assert h == h2

def test_generate_id():
    i = generate_id("test", "a", "b")
    assert len(i) == 32

def test_thought_id_gen():
    i = thought_id("content", "context")
    assert len(i) == 32

def test_session_id_gen():
    i = session_id("brain")
    assert len(i) == 32

def test_strategy_id_gen():
    i = strategy_id("task", "approach")
    assert len(i) == 32

def test_pattern_id_gen():
    i = pattern_id("error", "context")
    assert len(i) == 32

def test_brain_id_gen():
    i = brain_id("mybrain")
    assert len(i) == 32

def test_wisdom_id_gen():
    i = wisdom_id("content", "domain")
    assert len(i) == 32

def test_integrity_seal_roundtrip():
    data = b"test data for sealing"
    seal = IntegritySeal.create(data, node_count=5)
    assert seal.verify(data)
    packed = seal.pack()
    seal2 = IntegritySeal.unpack(packed)
    assert seal2.verify(data)
    assert seal2.node_count == 5

def test_integrity_seal_tamper():
    data = b"original"
    seal = IntegritySeal.create(data, node_count=1)
    assert not seal.verify(b"tampered")

def test_cmp_lock_acquire_release():
    with tempfile.NamedTemporaryFile(suffix=".cortex", delete=False) as f:
        path = f.name
    try:
        lock = CMPLock(path)
        assert lock.acquire()
        assert lock.is_locked
        lock.release()
        assert not lock.is_locked
    finally:
        os.unlink(path) if os.path.exists(path) else None

def test_cmp_lock_context_manager():
    with tempfile.NamedTemporaryFile(suffix=".cortex", delete=False) as f:
        path = f.name
    try:
        lock = CMPLock(path)
        with lock:
            assert lock.is_locked
        assert not lock.is_locked
    finally:
        os.unlink(path) if os.path.exists(path) else None

# ━━━ TOKENIZER ━━━
from cortex.core.tokenizer import (
    tokenize, tokenize_filtered, extract_keywords, extract_claims,
    jaccard_similarity, cosine_similarity, semantic_overlap,
    detect_domain, ngrams, token_fingerprint,
)

def test_tokenize():
    assert tokenize("Hello World!") == ["hello", "world"]

def test_tokenize_filtered():
    tokens = tokenize_filtered("the quick brown fox")
    assert "the" not in tokens
    assert "quick" in tokens

def test_extract_keywords():
    kw = extract_keywords("python code function python class python")
    assert kw[0] == "python"

def test_extract_claims():
    claims = extract_claims("This is claim one. This is claim two. Short.")
    assert len(claims) == 2

def test_jaccard_similarity():
    assert jaccard_similarity(["a", "b", "c"], ["a", "b", "c"]) == 1.0
    assert jaccard_similarity(["a"], ["b"]) == 0.0

def test_cosine_similarity():
    assert cosine_similarity(["a", "b"], ["a", "b"]) == pytest.approx(1.0)
    assert cosine_similarity(["a"], ["b"]) == 0.0

def test_semantic_overlap():
    s = semantic_overlap("python programming code", "python code function")
    assert s > 0.3

def test_detect_domain_programming():
    assert detect_domain("python code function variable class") == "programming"

def test_detect_domain_science():
    assert detect_domain("experiment hypothesis data research") == "science"

def test_detect_domain_general():
    assert detect_domain("hello world") == "general"

def test_ngrams():
    result = ngrams(["a", "b", "c", "d"], 2)
    assert ("a", "b") in result
    assert len(result) == 3

def test_token_fingerprint():
    fp = token_fingerprint("hello world test")
    assert "|" in fp

# ━━━ CORTEX-DB ━━━
from cortex.core.cortexdb import CortexDB

def test_cortexdb_create():
    db = CortexDB("test.cortex")
    assert db.thought_count == 0

def test_cortexdb_add_thought():
    db = CortexDB("test.cortex")
    t = ThoughtNode(content="test thought")
    tid = db.add_thought(t)
    assert db.thought_count == 1
    assert db.get_thought(tid) is not None

def test_cortexdb_delete_thought():
    db = CortexDB("test.cortex")
    t = ThoughtNode(content="to delete")
    tid = db.add_thought(t)
    db.delete_thought(tid)
    assert db.thought_count == 0

def test_cortexdb_zones():
    db = CortexDB("test.cortex")
    t1 = ThoughtNode(content="a", zone=ZONE_FOCUSED)
    t2 = ThoughtNode(content="b", zone=ZONE_EXPLORING)
    db.add_thought(t1)
    db.add_thought(t2)
    focused = db.get_thoughts_by_zone(ZONE_FOCUSED)
    assert len(focused) == 1

def test_cortexdb_search():
    db = CortexDB("test.cortex")
    db.add_thought(ThoughtNode(content="python programming is great"))
    db.add_thought(ThoughtNode(content="cooking recipes are fun"))
    results = db.search_thoughts("python code", top_k=5)
    assert len(results) > 0
    assert "python" in results[0].content

def test_cortexdb_metacog_state():
    db = CortexDB("test.cortex")
    db.set_metacog_state({"score": 0.85})
    assert db.get_metacog_state()["score"] == 0.85

def test_cortexdb_strategies():
    db = CortexDB("test.cortex")
    db.add_strategy({"name": "s1", "fitness": 0.7})
    assert len(db.get_strategies()) == 1

def test_cortexdb_growth():
    db = CortexDB("test.cortex")
    db.add_growth_entry({"score": 0.01})
    assert len(db.get_growth_log()) == 1

def test_cortexdb_stats():
    db = CortexDB("test.cortex")
    db.add_thought(ThoughtNode(content="stat test"))
    s = db.stats()
    assert s["thought_count"] == 1

def test_cortexdb_save_load():
    with tempfile.NamedTemporaryFile(suffix=".cortex", delete=False) as f:
        path = f.name
    try:
        db = CortexDB(path)
        db.add_thought(ThoughtNode(content="persist me"))
        db.set_metacog_state({"test": True})
        db.save()
        db2 = CortexDB.load(path)
        assert db2.thought_count == 1
        assert db2.get_metacog_state()["test"] is True
    finally:
        for p in [path, path + ".lock", path + ".bak"]:
            if os.path.exists(p):
                os.unlink(p)

def test_cortexdb_save_load_multiple():
    with tempfile.NamedTemporaryFile(suffix=".cortex", delete=False) as f:
        path = f.name
    try:
        db = CortexDB(path)
        for i in range(10):
            db.add_thought(ThoughtNode(content=f"thought {i}"))
        db.save()
        db2 = CortexDB.load(path)
        assert db2.thought_count == 10
    finally:
        for p in [path, path + ".lock", path + ".bak"]:
            if os.path.exists(p):
                os.unlink(p)
