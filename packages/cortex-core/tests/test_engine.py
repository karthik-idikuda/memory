"""Tests for Phases 4-8: Engine, Bridges, CORTEXLANG-Ω, Utils, Packaging."""
import os
import json
import tempfile
import pytest

# ━━━ CONVERSATION ━━━
from cortex.engine.conversation import ConversationManager

def test_conversation_add_turn():
    c = ConversationManager()
    c.add_turn("hello", "hi there")
    assert c.turn_count == 1

def test_conversation_context():
    c = ConversationManager()
    c.add_turn("q1", "a1")
    c.add_turn("q2", "a2")
    msgs = c.get_context_messages()
    assert len(msgs) >= 2

def test_conversation_clear():
    c = ConversationManager()
    c.add_turn("q", "a")
    c.clear()
    assert c.message_count == 0

# ━━━ TOOLS ━━━
from cortex.engine.tools import ToolRegistry

def test_tool_register():
    r = ToolRegistry()
    r.register("add", lambda a, b: a + b, "Add two numbers")
    assert r.tool_count == 1

def test_tool_execute():
    r = ToolRegistry()
    r.register("add", lambda a, b: a + b)
    result = r.execute("add", a=2, b=3)
    assert result.success
    assert result.output == 5

def test_tool_not_found():
    r = ToolRegistry()
    with pytest.raises(Exception):
        r.execute("nonexistent")

def test_tool_list():
    r = ToolRegistry()
    r.register("t1", lambda: 1, "Tool 1")
    r.register("t2", lambda: 2, "Tool 2")
    assert len(r.list_tools()) == 2

def test_tool_has():
    r = ToolRegistry()
    r.register("x", lambda: None)
    assert r.has_tool("x")
    assert not r.has_tool("y")

# ━━━ GROWTH ━━━
from cortex.engine.growth import GrowthEngine

def test_growth_measure():
    g = GrowthEngine()
    g.measure(0.5, 0.5, 0.5, 0.5, 0.0)
    assert g.total_measurements == 1

def test_growth_trend():
    g = GrowthEngine()
    g.measure(0.5, 0.5, 0.5, 0.5, 0.0)
    g.measure(0.6, 0.6, 0.6, 0.6, 0.1)
    g.measure(0.7, 0.7, 0.7, 0.7, 0.2)
    assert g.trend in ("growing", "improving", "stable", "insufficient_data")

def test_growth_to_dict():
    g = GrowthEngine()
    d = g.to_dict()
    assert "current_score" in d

# ━━━ LLM ROUTER ━━━
from cortex.engine.router import LLMRouter

def test_router_create():
    r = LLMRouter()
    assert len(r.list_adapters()) > 0

def test_router_register():
    r = LLMRouter()
    class MockAdapter:
        def generate(self, messages, model, **kw): return "mock"
        def health_check(self): return True
        def list_models(self): return ["mock-1"]
    r.register_adapter("mock", MockAdapter())
    assert r.health_check("mock")

def test_router_generate_mock():
    r = LLMRouter()
    class MockAdapter:
        def generate(self, messages, model, **kw): return "response"
        def health_check(self): return True
        def list_models(self): return []
    r.register_adapter("mock", MockAdapter())
    result = r.generate([{"role": "user", "content": "hi"}], "mock", "m1")
    assert result == "response"

# ━━━ BRIDGES ━━━
from cortex.bridges.neuronx_bridge import NeuronXBridge
from cortex.bridges.sigmax_bridge import SigmaXBridge

def test_neuronx_bridge_not_connected():
    b = NeuronXBridge()
    assert not b.is_connected

def test_neuronx_bridge_recall_empty():
    b = NeuronXBridge()
    assert b.recall("test") == []

def test_neuronx_bridge_custom_fn():
    b = NeuronXBridge()
    b.configure(recall_fn=lambda q, k: [{"id": "1", "content": q}])
    assert b.is_connected
    result = b.recall("hello")
    assert result[0]["content"] == "hello"

def test_sigmax_bridge_not_connected():
    b = SigmaXBridge()
    assert not b.is_connected

def test_sigmax_bridge_custom_fn():
    b = SigmaXBridge()
    b.configure(recall_fn=lambda q, k: [{"id": "c1", "content": "chain"}])
    result = b.recall_chains("test")
    assert len(result) == 1

# ━━━ ADAPTER BASE ━━━
from cortex.bridges.adapter_base import BaseLLMAdapter

def test_adapter_abstract():
    with pytest.raises(TypeError):
        BaseLLMAdapter()

# ━━━ CORTEXLANG SYMBOLS ━━━
from cortex.language.symbols import symbol, name_of, is_valid_symbol, ALL_SYMBOLS

def test_symbol_lookup():
    s = symbol("CONFIDENCE_HIGH")
    assert s != "?"

def test_name_lookup():
    s = symbol("CONFIDENCE_HIGH")
    n = name_of(s)
    assert n == "CONFIDENCE_HIGH"

def test_valid_symbol():
    s = symbol("CONFIDENCE_HIGH")
    assert is_valid_symbol(s)

def test_invalid_symbol():
    assert not is_valid_symbol("xyz_not_real")

def test_all_symbols_nonempty():
    assert len(ALL_SYMBOLS) > 20

# ━━━ CORTEXLANG KEYWORDS ━━━
from cortex.language.keywords import is_keyword, category_of, all_categories

def test_is_keyword():
    assert is_keyword("METACOG_SCORE")

def test_not_keyword():
    assert not is_keyword("RANDOM_WORD")

def test_category():
    cat = category_of("METACOG_SCORE")
    assert cat == "metacognition"

def test_all_categories():
    cats = all_categories()
    assert "metacognition" in cats
    assert "confidence" in cats

# ━━━ CORTEXLANG GRAMMAR ━━━
from cortex.language.grammar import validate_notation, is_valid_notation, validate_command, parse_command

def test_validate_empty():
    errors = validate_notation("")
    assert len(errors) > 0

def test_validate_unbalanced_quotes():
    errors = validate_notation('◎ "unclosed')
    assert any("quote" in e.lower() for e in errors)

def test_parse_command_valid():
    keyword, args = parse_command("METACOG_SCORE()")
    assert keyword == "METACOG_SCORE"
    assert args == []

def test_parse_command_with_args():
    keyword, args = parse_command('WISDOM_SEARCH("python patterns")')
    assert keyword == "WISDOM_SEARCH"
    assert "python patterns" in args

# ━━━ CORTEXLANG EMITTER ━━━
from cortex.language.emitter import emit_thought, emit_trace, emit_growth

def test_emit_thought():
    n = emit_thought("RESPONSE", "FOCUSED", 0.9, 0.8, "Test content")
    assert '"' in n

def test_emit_trace():
    t = emit_trace(["recall", "generate"], 100.0)
    assert "100ms" in t

def test_emit_growth_up():
    g = emit_growth(0.05)
    assert g != ""

def test_emit_growth_down():
    g = emit_growth(-0.05)
    assert g != ""

# ━━━ CORTEXLANG PARSER ━━━
from cortex.language.parser import parse_cortexlang, ParsedCommand

def test_parse_command_line():
    results = parse_cortexlang("METACOG_SCORE()")
    assert len(results) >= 1
    assert isinstance(results[0], ParsedCommand)

# ━━━ UTILS: CRYPTO ━━━
from cortex.utils.crypto import encrypt_data, decrypt_data, derive_key

def test_encrypt_decrypt():
    data = b"secret message from CORTEX-X"
    password = "test123"
    encrypted = encrypt_data(data, password)
    decrypted = decrypt_data(encrypted, password)
    assert decrypted == data

def test_encrypt_wrong_password():
    data = b"secret"
    encrypted = encrypt_data(data, "correct")
    with pytest.raises(ValueError):
        decrypt_data(encrypted, "wrong")

def test_derive_key():
    key, salt = derive_key("password")
    assert len(key) == 32
    assert len(salt) == 16

def test_derive_key_deterministic():
    key1, salt = derive_key("pass", salt=b"0" * 16)
    key2, _ = derive_key("pass", salt=b"0" * 16)
    assert key1 == key2

# ━━━ UTILS: COMPRESSOR ━━━
from cortex.utils.compressor import compress, decompress, compress_json, decompress_json, compression_ratio

def test_compress_roundtrip():
    data = b"hello world" * 100
    c = compress(data)
    assert decompress(c) == data

def test_compress_json_roundtrip():
    obj = {"key": "value", "num": 42}
    c = compress_json(obj)
    assert decompress_json(c) == obj

def test_compression_ratio():
    data = b"a" * 1000
    c = compress(data)
    ratio = compression_ratio(data, c)
    assert ratio > 0.5

# ━━━ UTILS: EVENTS ━━━
from cortex.utils.events import CortexEvent, EVENT_THOUGHT_CREATED

def test_event_emit():
    ev = CortexEvent()
    results = []
    ev.on("test", lambda **kw: results.append(kw))
    ev.emit("test", data=42)
    assert len(results) == 1
    assert results[0]["data"] == 42

def test_event_off():
    ev = CortexEvent()
    handler = lambda **kw: None
    ev.on("test", handler)
    ev.off("test", handler)
    ev.emit("test")

def test_event_constants():
    assert EVENT_THOUGHT_CREATED == "thought.created"

# ━━━ UTILS: METRICS ━━━
from cortex.utils.metrics import brain_health, format_metrics_line

def test_brain_health():
    h = brain_health(100, 10, 2, 0.8, 0.9, 0.7, 0.5)
    assert 0 <= h["score"] <= 1
    assert h["label"] in ("excellent", "healthy", "developing", "needs_attention", "critical")

def test_format_metrics():
    stats = {"total_thoughts": 50, "wisdom_count": 5, "label": "healthy", "score": 0.75}
    line = format_metrics_line(stats)
    assert "thoughts" in line
    assert "wisdom" in line

# ━━━ PUBLIC API ━━━
def test_public_import():
    from cortex import CortexAgent, ThoughtNode, CortexDB, metacog_score
    assert CortexAgent is not None
    assert ThoughtNode is not None
    assert CortexDB is not None

def test_version():
    import cortex
    assert cortex.__version__ == "1.0.0"

def test_codename():
    import cortex
    assert cortex.__codename__ == "CORTEX-X Omega"
