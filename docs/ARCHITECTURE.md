# NEURON-X Omega — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     NEURON-X OMEGA                          │
├─────────────┬─────────────────────┬────────────────────────┤
│  React Web  │   FastAPI Server    │   TypeScript SDK       │
│  Dashboard  │   REST + SSE        │   Client Library       │
├─────────────┴─────────────────────┴────────────────────────┤
│                  NeuronBrain Orchestrator                    │
├─────────┬──────────┬───────────┬──────────┬────────────────┤
│Amygdala │ WSRA-X   │ BondEngine│ Thermal  │ Contradiction  │
│Surprise │ Retrieval│ Axon Mgmt │ Manager  │ Engine         │
├─────────┴──────────┴───────────┴──────────┴────────────────┤
│                      SOMA-DB                                │
│              5-Layer Binary Format                           │
│  [Header | Zone Index | Engram Store | Axon Map | Seal]     │
└─────────────────────────────────────────────────────────────┘
```

## Package Structure

```
packages/
├── neuronx-core/              ← Python Core Engine
│   └── neuronx/
│       ├── config.py           Central constants
│       ├── exceptions.py       Custom exceptions
│       ├── cli.py              CLI entry point
│       ├── __init__.py         Public API
│       ├── core/
│       │   ├── node.py         EngramNode (20 fields)
│       │   ├── soma.py         SOMA-DB binary storage
│       │   ├── integrity.py    SHA-256, struct packing
│       │   ├── surprise.py     Amygdala surprise engine
│       │   ├── retrieval.py    WSRA-X 8-component scoring
│       │   ├── bonds.py        Axon bond management
│       │   └── zones.py        Thermal zone manager
│       ├── brain/
│       │   ├── neuron.py       NeuronBrain orchestrator
│       │   ├── contradiction.py  Clash detection + resolve
│       │   ├── extractor.py    Memory extraction
│       │   ├── injector.py     AI context injection
│       │   ├── scheduler.py    Auto-audit scheduler
│       │   └── indexer.py      Subject index
│       ├── language/
│       │   └── nrnlang.py      NRNLANG-Ω interpreter
│       ├── utils/
│       │   ├── tokenizer.py    Custom tokenizer + Jaccard
│       │   ├── exporter.py     JSON/MD/CSV/NRN export
│       │   └── events.py       Pub/sub event bus
│       └── integrations/
│           └── base.py         OpenAI/Anthropic/LangChain/LiteLLM
├── neuronx-server/            ← FastAPI Server
│   └── app/main.py            17 endpoints + SSE + rate limiting
├── neuronx-sdk-js/            ← TypeScript SDK
│   └── src/
│       ├── types.ts            All API type definitions
│       ├── client.ts           Full API client + SSE
│       └── index.ts            Barrel exports
└── neuronx-web/               ← React Dashboard
    └── src/
        ├── App.tsx             9 views (Dashboard→Settings)
        ├── api.ts              API client module
        ├── index.css           Biopunk dark theme
        └── main.tsx            React entry point
```

## Data Flow

1. **Input** → `NeuronBrain.remember(text)`
2. **Extract** → `MemoryExtractor` splits compound sentences (BUG-013)
3. **Surprise** → `Amygdala` calculates surprise score
4. **Action Decision**:
   - `surprise < 0.25` → **ECHO** (reinforce existing)
   - `surprise ≥ 0.85 && jaccard ≥ 0.15` → **CLASH** (contradiction)
   - Otherwise → **FORGE** (create new)
5. **If CLASH** → `ContradictionEngine` detects + resolves
6. **Store** → `SomaDB.add_engram()` in binary format
7. **Bond** → `BondEngine` creates TIME/WORD/EMOTION bonds
8. **Zone** → `ThermalManager` assigns HOT/WARM/COLD/SILENT

## SOMA-DB Binary Format

```
Offset     Layer              Content
0x0000     HEADER (72B)       Magic(4) + Version(2) + Counts + Timestamps
0x0048     ZONE INDEX         Zone offsets and sizes
Variable   ENGRAM STORE       JSON-serialized engrams (compressed for COLD/SILENT)
Variable   AXON MAP           struct-packed axon records (45B each)
EOF-64     SEAL (64B)         SHA-256 checksum + metadata
```

## WSRA-X Scoring (8 Components)

```
SCORE = Σ(wi × ci) for i in:
  ① Word Resonance    (w=2.5)  — Jaccard similarity
  ② Zone Heat         (w=2.0)  — HOT:1.0 WARM:0.6 COLD:0.2 SILENT:0.0
  ③ Spark Legacy      (w=1.8)  — surprise_score × weight
  ④ Recency Curve     (w=1.5)  — exp(-λ × days)
  ⑤ Bond Centrality   (w=1.2)  — log₁₀(bonds+1)/3.0
  ⑥ Confidence Factor (w=1.0)  — confidence × truth_multiplier
  ⑦ Decay Debt        (w=1.3)  — inverse decay pressure
  ⑧ Clash Penalty     (w=0.8)  — penalizes contested memories
```

## Thermal Zone Lifecycle

```
FORGE → HOT (heat>0.70) → WARM (heat>0.30) → COLD (heat>0.05) → SILENT
         ↑                                         ↑
         └── REAWAKEN (if similar input) ──────────┘
```
