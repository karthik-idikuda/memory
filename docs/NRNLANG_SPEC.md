# NRNLANG-Ω Specification

## Overview

NRNLANG-Ω is the symbolic language of NEURON-X. Every event, command, and output has a symbolic representation.

## Symbols

### Action Symbols
| Symbol | Meaning |
|--------|---------|
| `⊕` | FORGE — new memory created |
| `●` | ECHO — existing memory reinforced |
| `##` | CLASH — contradiction detected |
| `!!=` | SUPERSEDE — new truth replaces old |
| `\|?\|` | CONTESTED — truth uncertain |
| `^^` | REAWAKEN — dormant memory revived |
| `:::` | WEAVE — bonds formed |
| `-x-` | PRUNE — weak bonds removed |
| `~~` | TEMPER — zone migration |
| `◆` | CRYSTALLIZE — memory frozen |
| `🔍` | AUDIT — thermal audit run |
| `>>` | NMP_WRITE — binary write protocol |

### Zone Symbols
| Symbol | Zone |
|--------|------|
| `🔥 [H]` | HOT |
| `🌡 [W]` | WARM |
| `❄  [C]` | COLD |
| `👻 [S]` | SILENT |

### Emotion Symbols
| Symbol | Emotion |
|--------|---------|
| `:+:` | happy |
| `:-:` | sad |
| `:!:` | excited |
| `:?:` | curious |
| `:x:` | angry |
| `:~:` | neutral |
| `:*:` | love |
| `:/: ` | fear |

### Truth Symbols
| Symbol | State |
|--------|-------|
| `\|-` | active |
| `-\|` | expired |
| `\|?\|` | contested |

### Existence Symbols
| Symbol | Meaning |
|--------|---------|
| `╔══╗` | BORN |
| `╚══╝` | DIED |
| `◈` | LIVE |
| `◇` | SLEEP |
| `◆` | ANCHOR |
| `○` | GHOST |

## Commands

### FORGE — Create Memory
```
FORGE engram("I love pizza")
FORGE engram("User works at Google", emotion=:+:, decay=identity)
```

### ECHO — Reinforce Memory
```
ECHO engram(id="abc12345")
```

### RECALL — Query Memories
```
RECALL query("What food does user like?")
RECALL query("work", top_k=10)
```

### AUDIT — Run Thermal Audit
```
AUDIT brain()
```

### STATS — Get Statistics
```
STATS brain()
```

### EXPORT — Export Brain
```
EXPORT brain(format="json")
EXPORT brain(format="markdown")
```

### EXPIRE — Expire Memory
```
EXPIRE engram(id="abc12345")
```

### CRYSTALLIZE — Freeze Memory
```
CRYSTALLIZE engram(id="abc12345")
```

## Output Format

Every NRNLANG-Ω output follows this pattern:

```
[SYMBOL] [ZONE] [EMOTION] [ID] — [MESSAGE]
```

Example:
```
⊕ 🔥 [H] :+: a1b2c3d4 — "I love pizza" (conf:0.85 wt:1.00)
● 🔥 [H] :~: b2c3d4e5 — ECHO reinforced (conf:0.90 wt:1.15)
## ❄  [C] :x: c3d4e5f6 — CLASH with d4e5f6a7 (resolve:SUPERSEDED)
```
