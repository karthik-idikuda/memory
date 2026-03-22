# NEURON-X Omega

The world's first self-sovereign permanent AI memory system. NEURON-X Omega implements a biologically-inspired memory architecture with a custom language (NRNLANG-Omega), a custom database format (SOMA-DB), and a neural memory protocol (NMP) for storing, retrieving, and evolving memories with configurable forgetting curves, thermal zones, and contradiction resolution.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Memory Model](#memory-model)
- [Configuration](#configuration)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

---

## Overview

NEURON-X Omega provides:

- **Permanent memory storage** in SOMA-DB format with configurable persistence
- **Surprise-based routing** -- new information is classified as ECHO (reinforcement), NOVEL, or CLASH (contradiction)
- **Thermal zone management** -- memories are tagged as HOT, WARM, COLD, SILENT, or FOSSIL based on access patterns
- **Bond engine** -- automatic relationship discovery between memories via time proximity, word overlap, and emotional similarity
- **Ebbinghaus decay curves** -- mathematically derived forgetting rates per memory type (emotion, opinion, event, fact, identity)
- **WSRA-X retrieval** -- weighted scoring combining word resonance, zone heat, spark legacy, recency, bond centrality, and confidence
- **Contradiction engine** -- handles conflicting memories with supersession, contestation, and confidence adjustment
- **Claude API integration** -- optional AI-enhanced memory processing via Anthropic Claude

---

## Architecture

```
+------------------------------------------+
|         Chat Interface                   |
|  interface/chat.py                       |
|  Interactive REPL for memory operations  |
+------------------------------------------+
              |
              v
+------------------------------------------+
|         NeuronBrain                      |
|  brain/neuron.py                         |
|  Memory ingestion, retrieval, evolution  |
+------------------------------------------+
    |         |          |          |
    v         v          v          v
+--------+ +--------+ +--------+ +--------+
| Surprise| | Bond   | | Thermal| | WSRA-X |
| Engine  | | Engine | | Zones  | | Retri- |
| ECHO/   | | TIME/  | | HOT/   | | eval   |
| NOVEL/  | | WORD/  | | WARM/  | | Engine |
| CLASH   | | EMOTION| | COLD/  | |        |
+--------+ +--------+ | SILENT | +--------+
                       +--------+
              |
              v
+------------------------------------------+
|         SOMA-DB                          |
|  data/<brain_name>.soma                  |
|  Custom binary memory database           |
+------------------------------------------+
              |
              v (optional)
+------------------------------------------+
|         Anthropic Claude API             |
|  AI-enhanced memory classification       |
+------------------------------------------+
```

---

## Technology Stack

| Component        | Technology                    |
|------------------|-------------------------------|
| Language         | Python 3.10+                  |
| AI Integration   | Anthropic Claude SDK          |
| Storage Format   | SOMA-DB (custom binary)       |
| Query Language   | NRNLANG-Omega (custom DSL)    |
| Configuration    | python-dotenv                 |
| Logging          | Python logging (file + console)|

---

## Project Structure

```
memory/
|
|-- main.py                       # Entry point with CLI argument parsing
|-- config.py                     # Central configuration (all thresholds)
|-- requirements.txt              # Python dependencies
|-- .env.example                  # Environment variable template
|
|-- brain/
|   +-- neuron.py                 # NeuronBrain core engine
|
|-- interface/
|   +-- chat.py                   # Interactive REPL interface
|
|-- core/                         # Core memory primitives
|-- api/                          # API layer (REST endpoints)
|-- utils/                        # Utility modules
|-- scripts/                      # Operational scripts
|-- data/                         # SOMA-DB memory files
|-- docs/                         # Technical documentation
|-- examples/                     # Usage examples
|-- packages/                     # Installable packages
|-- tests/                        # Test suite
+-- web/                          # Web dashboard
```

---

## Memory Model

### Thermal Zones

| Zone   | Heat Threshold | Description                              |
|--------|---------------|------------------------------------------|
| HOT    | >= 0.70       | Frequently accessed, highly relevant     |
| WARM   | >= 0.30       | Moderately active memories               |
| COLD   | >= 0.05       | Rarely accessed but retained             |
| SILENT | < 0.05        | Dormant for 90+ days                     |
| FOSSIL | --            | Cold for 180+ days, archived             |

### Decay Rates (Ebbinghaus-derived)

| Memory Type | Decay Rate | Half-Life     |
|-------------|-----------|---------------|
| Emotion     | 0.010     | ~69 days      |
| Opinion     | 0.005     | ~139 days     |
| Event       | 0.003     | ~231 days     |
| Fact        | 0.001     | ~693 days     |
| Identity    | 0.0001    | ~6,931 days   |

### WSRA-X Retrieval Weights

| Factor            | Weight | Purpose                        |
|-------------------|--------|--------------------------------|
| Word Resonance    | 2.5    | Direct content relevance       |
| Zone Heat         | 2.0    | Hot memories prioritized       |
| Spark Legacy      | 1.8    | Surprising memories retained   |
| Recency Curve     | 1.5    | Recent memories weighted       |
| Decay Debt        | 1.3    | Penalty for unused memories    |
| Bond Centrality   | 1.2    | Connected memories boosted     |
| Confidence        | 1.0    | Trust level factor             |
| Clash Penalty     | 0.8    | Contested memories penalized   |

---

## Configuration

All tunable parameters are centralized in `config.py`. Key thresholds:

| Parameter                    | Default | Description                       |
|------------------------------|---------|-----------------------------------|
| SURPRISE_ECHO_THRESHOLD      | 0.25    | Below this: reinforce existing    |
| SURPRISE_CLASH_THRESHOLD     | 0.85    | Above this: potential conflict    |
| ANCHOR_CONFIDENCE_THRESHOLD  | 0.95    | Required for crystallization      |
| DEFAULT_TOP_K                | 7       | Memories returned per query       |
| AUTO_SAVE_INTERVAL           | 5       | Auto-save every N interactions    |

---

## Installation

```bash
git clone https://github.com/karthik-idikuda/NEURON-X-Omega.git
cd NEURON-X-Omega

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add ANTHROPIC_API_KEY for AI-enhanced mode (optional)
```

---

## Usage

```bash
# Start interactive memory session
python main.py

# Specify a named brain
python main.py --brain research

# Enable debug logging
python main.py --debug

# Custom data directory
python main.py --data /path/to/data
```

---

## License

This project is released for educational and research purposes.
