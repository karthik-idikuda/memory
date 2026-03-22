# NEURON-X OMEGA — Building the Complete Platform

## Project Build

The NEURON-X OMEGA platform is built as a monorepo under `packages/`:

```
packages/
├── neuronx-core/          ← Python Core Engine (THE BRAIN)
│   ├── neuronx/
│   │   ├── core/          ← Node, SOMA-DB, Surprise, Retrieval, Bonds, Zones
│   │   ├── brain/         ← NeuronBrain orchestrator, Contradiction, Extractor
│   │   ├── language/      ← NRNLANG-Ω interpreter
│   │   ├── utils/         ← Tokenizer, Exporter, Events
│   │   └── integrations/  ← OpenAI, Anthropic, LangChain, LiteLLM
│   └── tests/             ← 91 comprehensive tests
├── neuronx-server/        ← FastAPI REST API
│   └── app/
│       └── main.py        ← All endpoints + SSE + rate limiting
└── neuronx-web/           ← React Web Dashboard (TODO)
```

## Quick Start

```python
from neuronx import NeuronBrain

brain = NeuronBrain("my_brain")

# Store memories
brain.remember("I love eating pizza")
brain.remember("I work as a software engineer")
brain.remember("My favorite color is blue")

# Recall memories
results = brain.recall("What food does user like?")
for engram, score in results:
    print(f"  [{engram.zone[0]}] {engram.raw} (score={score:.3f})")

# Get context for AI injection
ctx = brain.get_context("What do you know about me?")
print(ctx.system_prompt_addition)

# End session (saves + bonds + audit)
brain.end_session()
```

## AI Integration (2 lines)

```python
from neuronx import NeuronBrain, OpenAIIntegration

brain = NeuronBrain("user_memory")
integration = OpenAIIntegration(brain=brain, top_k=7)

# Before sending to OpenAI:
enriched_messages = integration.pre_chat(messages)
# After receiving response:
integration.post_chat(assistant_response)
```

## API Server

```bash
pip install fastapi uvicorn
uvicorn packages.neuronx-server.app.main:app --host 0.0.0.0 --port 8000
```

## Run Tests

```bash
cd packages/neuronx-core
python3 -m pytest tests/ -v
```

## Bug Fixes Implemented

| Bug | Fix | File |
|-----|-----|------|
| BUG-001 | True binary SOMA format with magic bytes | `core/soma.py` |
| BUG-002 | All 8 WSRA-X components | `core/retrieval.py` |
| BUG-003 | CLASH Jaccard gate (≥0.15) | `core/surprise.py` |
| BUG-004 | .soma.bak restore on corruption | `core/soma.py` |
| BUG-005 | `is_anchor` as real boolean field | `core/node.py` |
| BUG-006 | NMP creates .nrnlock/.bak/.sig/.nrnlog | `core/soma.py` |
| BUG-007 | Reawakening runs at session start | `core/zones.py` |
| BUG-008 | Prune removes from BOTH bond sides | `core/bonds.py` |
| BUG-009 | Auto-audit at 100 interactions | `brain/scheduler.py` |
| BUG-010 | Rate limiting (60 req/min) | `app/main.py` |
| BUG-012 | All endpoints validated | `app/main.py` |
| BUG-013 | Long input chunking (>500 chars) | `brain/extractor.py` |
| BUG-014 | O(n×k) subject index | `brain/indexer.py` |
| BUG-015 | Pagination support | `core/retrieval.py` |
| BUG-016 | SSE streaming endpoint | `app/main.py` |
| BUG-017 | NRNLANG output to UI | `language/nrnlang.py` |
| BUG-018 | Export includes ALL fields | `utils/exporter.py` |
| BUG-019 | Real-time zone updates via SSE | `app/main.py` |
| BUG-020 | File lock with stale detection | `core/soma.py` |
