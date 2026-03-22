# NRNLANG-Ω — Complete Language Specification
## Neural Record Node Language — Omega Edition

---

## Origin

NRNLANG-Ω is a completely invented memory description language created specifically for NEURON-X Omega. Every symbol, keyword, and grammar rule was designed from scratch. It combines:

1. **Neuroscience terms** (real brain biology)
2. **Mathematical notation** (formulas and functions)
3. **Human thought patterns** (how ideas form)
4. **Temporal logic** (truth that changes over time)
5. **Invented symbols** (no existing meaning anywhere)
6. **Emotional notation** (feelings as first-class data)

---

## Symbol Table

### Group A — Existence Symbols

| Symbol | Name | Meaning |
|--------|------|---------|
| `╔══╗` | ENGRAM_BORN | New memory created |
| `╚══╝` | ENGRAM_DIED | Memory expires |
| `◈` | ENGRAM_LIVE | Currently active and true |
| `◇` | ENGRAM_SLEEP | Silent/dormant |
| `◆` | ENGRAM_ANCHOR | Permanent core memory |
| `○` | ENGRAM_GHOST | Silent but reawakenable |
| `●` | ENGRAM_ECHO | Being reinforced |
| `⊕` | ENGRAM_FORGE | Creating a new memory |
| `⊖` | ENGRAM_EXPIRE | Marking as historical |

### Group B — Flow Symbols

| Symbol | Name | Meaning |
|--------|------|---------|
| `~>` | FIRE | Memory activates |
| `<~` | SUPPRESS | Memory weakens |
| `>>` | STORE | Write to SOMA |
| `<<` | INVOKE | Retrieve from SOMA |
| `^^` | REAWAKEN | Dormant memory revives |
| `~~` | DECAY | Memory fading |
| `=>` | IMPLIES | Suggests another memory |
| `<=>` | LINKS | Bidirectional bond |
| `->>` | DEEP_STORE | Compress to COLD |
| `<<-` | DEEP_RECALL | Decompress from COLD |

### Group C — Comparison Symbols

| Symbol | Name | Meaning |
|--------|------|---------|
| `===` | SAME | Too similar, reinforce |
| `=/=` | UNIQUE | New, must store |
| `~=` | DRIFT | Similar but shifted |
| `##` | CLASH | Contradiction detected |
| `\|?\|` | CONTESTED | Competing truths |
| `!!=` | SUPERSEDE | New replaces old |

### Group D — Strength Symbols

| Symbol | Name | Meaning |
|--------|------|---------|
| `+++` | GROW | Increasing |
| `---` | SHRINK | Decreasing |
| `***` | PEAK | Maximum reached |
| `:::` | REINFORCE | Bond strengthening |
| `¦¦¦` | FAINT | Barely alive |
| `\|\|\|` | STRONG | Very powerful |
| `-x-` | SEVERED | Bond cut |
| `⚡` | SPARK | High surprise (>0.85) |

### Group E — Zone Symbols

| Symbol | Zone | Description |
|--------|------|-------------|
| `🔥 [H]` | HOT | Constantly used |
| `🌡 [W]` | WARM | Recently used |
| `❄  [C]` | COLD | Rarely used, compressed |
| `👻 [S]` | SILENT | Dormant |
| `◆  [A]` | ANCHOR | Permanent |

### Group F — Truth Symbols

| Symbol | State | Meaning |
|--------|-------|---------|
| `◈ \|-` | TRUE_NOW | Currently true |
| `◇ -\|` | TRUE_WAS | Was true, expired |
| `○ \|?\|` | TRUE_MAYBE | Uncertain |
| `● \|!\|` | TRUE_CONFLICT | Conflicted |
| `T[x]` | TIMESTAMP | Exact moment |

### Group H — Emotion Symbols

| Symbol | Emotion |
|--------|---------|
| `:+:` | Happy |
| `:-:` | Sad |
| `:!:` | Excited |
| `:?:` | Curious |
| `:x:` | Angry |
| `:~:` | Neutral |
| `:*:` | Love |
| `:/:`  | Fear |

---

## Grammar Rules

### Rule 1 — Memory Operation

```
VERB  subject  [type]  {properties}  SYMBOL  destination
```

Examples:
```
FORGE  engram("user loves pizza")  [opinion]  {conf:0.9}  >>  SOMA
INVOKE  CORTEX  ??  "food preferences"  @7  AI
WEAVE  engram[A]  <=>  engram[B]  {synapse:0.45}  :::
TEMPER  engram[X]  ~~  [C]  {heat:0.18, age:47d}
AUDIT  SOMA  ~>  TEMPER[all]  +  REAWAKEN[ghosts]
```

### Rule 2 — Formula Syntax

```
FORMULA_NAME {
  INPUT:    what goes in
  PROCESS:  (component × weight) + ...
  NORMALIZE: to range [min, max]
  MULTIPLY:  × modifier
  OUTPUT:   what comes out
}
```

### Rule 3 — Condition Syntax

```
WHEN  [condition]  ::  [action]  |  [alternative]
UNLESS  [condition]  ::  [skip]
```

Examples:
```
WHEN  surprise < 0.25  ::  engram ===  +++weight(+0.15)
WHEN  surprise > 0.85  AND  jaccard >= 0.15  ::  CLASH ##
WHEN  heat < 0.05  AND  age > 90d  ::  engram ~>  [S]
WHEN  confidence > 0.95  AND  access_count > 20  ::  CRYSTALLIZE ◆
```

### Rule 4 — Engram Node Notation

```
ENGRAM {
  id        : "fingerprint_16chars"
  raw       : "the actual memory text"
  born      : T[YYYY.MM.DD:HH:MM:SS]
  heat      : 0.0-1.0  ~>  [ZONE]
  spark     : 0.0-1.0  (⚡ if > 0.85)
  weight    : 0.1-3.0  (*** if at 3.0)
  decay     : fact/opinion/emotion/event/identity
  axons     : [id:strength  |||  id:strength  ¦¦¦]
  truth     : ◈ |- or ◇ -| or ○ |?| or ● |!|
  emotion   : :+: or :-: or :!: or :?: or :x: or :~:
  confidence: 0.0-1.0
  tags      : [person, place, preference, fact, event]
}
```

### Rule 5 — Session Flow

```
PULSE begins T[timestamp]
  INPUT ~> AMYGDALA
  AMYGDALA ~> HIPPOCAMPUS
  HIPPOCAMPUS ~> SOMA
  CORTEX << SOMA @7 AI
PULSE ends
```

---

## File Format (.nrn)

```
# Comments start with #
# Commands one per line
# Properties in {curly braces}
# Types in [square brackets]

FORGE engram("user loves pizza") [opinion] {conf:0.9, emotion:happy}
WEAVE engram[Nw7p] :: engram[Pq2r] {synapse:0.55}
AUDIT SOMA
INVOKE CORTEX "food preferences" @7 AI
```

---

## Running NRNLANG-Ω

```bash
# Execute a .nrn script
python utils/nrnlang.py examples/demo.nrn

# Validate syntax
python utils/nrnlang.py --validate examples/demo.nrn

# Inside NEURON-X chat:
/nrn <engram_id>    — show engram in NRNLANG-Ω notation
/nrn session        — current session as .nrn script
/nrn brain          — full brain export
/nrn run <file.nrn> — execute a script
/nrn validate       — validate syntax
```
