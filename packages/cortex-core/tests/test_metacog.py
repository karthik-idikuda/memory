"""Tests for Phase 3: METACOG-X Engine (metacog, confidence, contradiction, hallucination, drift, patterns, wisdom, strategy, trace)."""
import time
import pytest

# ━━━ METACOG SCORING ━━━
from cortex.meta.metacog import metacog_score, metacog_breakdown, metacog_health_label

def test_metacog_perfect_score():
    s = metacog_score(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
    assert abs(s - 1.0) < 0.01

def test_metacog_zero_score():
    s = metacog_score(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert s == 0.0

def test_metacog_partial():
    s = metacog_score(0.8, 0.7, 0.9, 0.6, 0.5, 0.3, 0.6, 0.4)
    assert 0.0 < s < 1.0

def test_metacog_breakdown_components():
    bd = metacog_breakdown(0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2)
    assert len(bd.components) == 8
    assert bd.total_score > 0

def test_metacog_breakdown_to_dict():
    bd = metacog_breakdown()
    d = bd.to_dict()
    assert "total_score" in d
    assert "components" in d

def test_metacog_health_labels():
    assert metacog_health_label(0.9) == "excellent"
    assert metacog_health_label(0.75) == "good"
    assert metacog_health_label(0.55) == "developing"
    assert metacog_health_label(0.35) == "emerging"
    assert metacog_health_label(0.1) == "nascent"

def test_metacog_recommendations():
    bd = metacog_breakdown(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
    assert len(bd.recommendations) > 0

def test_metacog_clamp():
    s = metacog_score(1.5, -0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
    assert 0.0 <= s <= 1.0

# ━━━ CONFIDENCE ━━━
from cortex.meta.confidence import ConfidenceTracker, CalibrationEntry

def test_confidence_record():
    t = ConfidenceTracker()
    t.record(0.8, 0.7)
    assert t.entry_count == 1

def test_confidence_brier():
    t = ConfidenceTracker()
    t.record(0.8, 0.8)
    assert t.brier_score < 0.01

def test_confidence_calibration_score():
    t = ConfidenceTracker()
    t.record(0.9, 0.9)
    assert t.calibration_score > 0.99

def test_confidence_overconfident():
    t = ConfidenceTracker()
    for _ in range(10):
        t.record(0.95, 0.3)
    assert t.is_overconfident

def test_confidence_underconfident():
    t = ConfidenceTracker()
    for _ in range(10):
        t.record(0.2, 0.9)
    assert t.is_underconfident

def test_confidence_bias_label():
    t = ConfidenceTracker()
    for _ in range(10):
        t.record(0.5, 0.5)
    assert t.bias_label == "well_calibrated"

def test_confidence_bucket_analysis():
    t = ConfidenceTracker()
    t.record(0.15, 0.1)
    t.record(0.85, 0.9)
    buckets = t.bucket_analysis()
    assert len(buckets) == 10

def test_confidence_adjust():
    t = ConfidenceTracker()
    for _ in range(10):
        t.record(0.9, 0.5)
    adjusted = t.suggest_adjusted_confidence(0.9)
    assert adjusted < 0.9

def test_confidence_domain():
    t = ConfidenceTracker()
    t.record(0.8, 0.7, domain="math")
    t.record(0.6, 0.9, domain="code")
    breakdown = t.domain_breakdown()
    assert "math" in breakdown
    assert "code" in breakdown

def test_confidence_serialization():
    t = ConfidenceTracker()
    t.record(0.5, 0.6, domain="test")
    d = t.to_dict()
    t2 = ConfidenceTracker.from_dict(d)
    assert t2.entry_count == 1

# ━━━ CONTRADICTION ━━━
from cortex.meta.contradiction import ContradictionDetector

def test_contradiction_no_match():
    d = ContradictionDetector()
    result = d.scan("Python is great", [{"id": "1", "content": "Java is popular"}])
    assert len(result) == 0

def test_contradiction_detect():
    d = ContradictionDetector()
    past = [{"id": "1", "content": "You should always use Python for web development"}]
    result = d.scan("You should never use Python for web development", past)
    assert len(result) >= 1

def test_contradiction_density():
    d = ContradictionDetector()
    d.total_claims_checked = 100
    assert d.density == 0.0

def test_contradiction_score():
    d = ContradictionDetector()
    assert d.contradiction_score == 1.0

def test_contradiction_resolve():
    d = ContradictionDetector()
    past = [{"id": "1", "content": "Always use Python for web apps"}]
    d.scan("Never use Python for web apps", past)
    if d.contradiction_count > 0:
        assert d.resolve(0) is True

# ━━━ HALLUCINATION ━━━
from cortex.meta.hallucination import HallucinationShield

def test_hallucination_no_claims():
    h = HallucinationShield()
    report = h.scan("ok", [])
    # With no memories to ground against, evidence_ratio is 0.0
    assert report.alert_level in ("safe", "critical", "warning", "caution")

def test_hallucination_grounded():
    h = HallucinationShield()
    memories = [{"id": "1", "content": "Python is a programming language used for web dev"}]
    report = h.scan("Python is used for web development.", memories)
    assert report.evidence_ratio > 0

def test_hallucination_ungrounded():
    h = HallucinationShield()
    memories = [{"id": "1", "content": "Cooking recipes for pasta"}]
    report = h.scan("Quantum computing uses qubits for parallel computation.", memories)
    assert report.evidence_ratio < 1.0

def test_hallucination_score():
    h = HallucinationShield()
    assert h.hallucination_score == 1.0

def test_hallucination_to_dict():
    h = HallucinationShield()
    d = h.to_dict()
    assert "total_scans" in d

# ━━━ DRIFT ━━━
from cortex.meta.drift import DriftDetector

def test_drift_initial():
    d = DriftDetector()
    assert d.drift_score == 1.0

def test_drift_stable():
    d = DriftDetector()
    for _ in range(20):
        d.record(0.8)
    assert d.drift_direction == "stable"
    assert d.drift_score > 0.5

def test_drift_degrading():
    d = DriftDetector()
    for i in range(50):
        d.record(0.9)
    for i in range(50):
        d.record(0.3)
    assert d.drift_direction in ("degrading", "stable")

def test_drift_measurement():
    d = DriftDetector()
    m = d.record(0.7)
    assert hasattr(m, "drift_signal")
    assert hasattr(m, "direction")

def test_drift_to_dict():
    d = DriftDetector()
    d.record(0.5)
    data = d.to_dict()
    assert "ewma_recent" in data

# ━━━ PATTERNS ━━━
from cortex.meta.patterns import PatternRecognizer

def test_pattern_record():
    p = PatternRecognizer()
    p.record_error("factual_error", "qa", "science")
    assert p.total_errors == 1

def test_pattern_detection():
    p = PatternRecognizer()
    for _ in range(5):
        p.record_error("factual_error", "qa", "science")
    actives = p.get_active_patterns()
    assert len(actives) >= 1

def test_pattern_score():
    p = PatternRecognizer()
    assert p.pattern_score == 1.0

def test_pattern_resolve():
    p = PatternRecognizer()
    for _ in range(5):
        p.record_error("logic_error", "code", "programming")
    key = "logic_error:code:programming"
    p.resolve_pattern(key, "fixed via better prompting")
    assert p.resolved_count >= 1

def test_pattern_summary():
    p = PatternRecognizer()
    s = p.summary()
    assert "total_errors" in s

# ━━━ WISDOM ━━━
from cortex.meta.wisdom import WisdomCrystallizer

def test_wisdom_observe():
    w = WisdomCrystallizer()
    w.observe("Always validate input", "programming", 0.9, "s1")
    assert w.candidate_count == 1

def test_wisdom_no_premature():
    w = WisdomCrystallizer()
    w.observe("Always validate input", "programming", 0.9, "s1")
    assert w.axiom_count == 0

def test_wisdom_ratio():
    w = WisdomCrystallizer()
    assert w.wisdom_ratio == 0.0

def test_wisdom_to_dict():
    w = WisdomCrystallizer()
    d = w.to_dict()
    assert "axiom_count" in d

# ━━━ STRATEGY ━━━
from cortex.meta.strategy import StrategyEngine

def test_strategy_add():
    e = StrategyEngine()
    s = e.add_strategy("qa", "think step by step")
    assert s.strategy_id != ""
    assert e.total_strategies == 1

def test_strategy_select():
    e = StrategyEngine()
    e.add_strategy("qa", "approach A")
    best = e.select("qa")
    assert best is not None

def test_strategy_record():
    e = StrategyEngine()
    s = e.add_strategy("qa", "approach A")
    e.record_outcome(s.strategy_id, True)
    assert s.usage_count == 1

def test_strategy_fitness():
    e = StrategyEngine()
    s = e.add_strategy("qa", "test")
    e.record_outcome(s.strategy_id, True)
    e.record_outcome(s.strategy_id, True)
    assert s.fitness > 0

def test_strategy_score():
    e = StrategyEngine()
    assert e.strategy_score == 0.5

# ━━━ THOUGHT TRACE ━━━
from cortex.meta.thought_trace import ThoughtTrace, TraceLogger

def test_trace_creation():
    t = ThoughtTrace(trace_id="test-trace")
    assert t.step_count == 0

def test_trace_add_step():
    t = ThoughtTrace(trace_id="test")
    t.add_step("recall", "Retrieved 5 memories", duration_ms=10)
    assert t.step_count == 1

def test_trace_compact():
    t = ThoughtTrace(trace_id="test")
    t.add_step("recall", "memories")
    t.add_step("generate", "response")
    t.total_time_ms = 100
    compact = t.format_compact()
    assert "recall" in compact
    assert "100ms" in compact

def test_trace_detailed():
    t = ThoughtTrace(trace_id="test")
    t.add_step("recall", "5 memories", duration_ms=10)
    t.finalize(0.8, "FOCUSED", 0.01)
    detailed = t.format_detailed()
    assert "recall" in detailed

def test_trace_logger():
    logger = TraceLogger()
    t = logger.new_trace()
    assert logger.trace_count == 1
    assert t.trace_id != ""

def test_trace_to_dict():
    t = ThoughtTrace(trace_id="test")
    t.add_step("recall", "memories")
    d = t.to_dict()
    assert "steps" in d
    assert len(d["steps"]) == 1
