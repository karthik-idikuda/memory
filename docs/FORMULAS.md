# NEURON-X Omega — Formulas Reference

## 1. Surprise Score

```
surprise(input, memory_pool) =
    best_match = max(jaccard(input_tokens, engram_tokens) for each engram)
    base = 1.0 - best_match
    conf_mod = best_match × (1 - best_engram.confidence)
    rec_mod = best_match × (1 - best_engram.recency)
    score = base + conf_mod + rec_mod
    return clamp(score, 0.0, 1.0)
```

## 2. Action Decision

```
if surprise < ECHO_THRESHOLD (0.25):         → ECHO
elif surprise ≥ CLASH_THRESHOLD (0.85)
     AND best_jaccard ≥ CLASH_GATE (0.15):   → CLASH  (BUG-003 fix)
else:                                         → FORGE
```

## 3. Recency Score

```
recency(engram) = exp(-λ × days_since_last_seen)
where λ = DECAY_RATES[engram.decay_class]
```

| Decay Class | λ | Half-life |
|-------------|---|-----------|
| emotion | 0.010 | 69 days |
| opinion | 0.005 | 139 days |
| event | 0.003 | 231 days |
| fact | 0.001 | 693 days |
| identity | 0.0001 | 6931 days |

## 4. Heat Score

```
heat(engram) = recency × weight × confidence
```

## 5. WSRA-X Retrieval Score

```
SCORE = Σ wi × ci for i = 1..8:

  c₁ = jaccard(query_tokens, engram_tokens)          w₁ = 2.5  (Word Resonance)
  c₂ = ZONE_HEAT_VALUES[zone]                        w₂ = 2.0  (Zone Heat)
  c₃ = surprise_score × weight                       w₃ = 1.8  (Spark Legacy)
  c₄ = recency                                       w₄ = 1.5  (Recency Curve)
  c₅ = log₁₀(num_bonds + 1) / 3.0                   w₅ = 1.2  (Bond Centrality)
  c₆ = confidence × truth_mult                       w₆ = 1.0  (Confidence)
  c₇ = 1.0 - (1.0 - recency) × 0.5                  w₇ = 1.3  (Decay Debt)
  c₈ = 0.5 if truth == contested else 1.0            w₈ = 0.8  (Clash Penalty)
```

## 6. Bond Strength (Synapse)

```
TIME bond:    synapse = min(dt_seconds / TIME_WINDOW, TIME_MAX)
WORD bond:    synapse = min(shared_words × 0.10, WORD_MAX)
EMOTION bond: synapse = EMOTION_VALUE (0.10) if same emotion
HERALD bond:  synapse = source_synapse × HERALD_DECAY (0.5)
```

## 7. Zone Assignment

```
if heat > HOT_THRESHOLD (0.70):    → HOT
elif heat > WARM_THRESHOLD (0.30): → WARM
elif heat > COLD_THRESHOLD (0.05): → COLD
else:                               → SILENT
```

## 8. Anchor Detection

```
is_anchor = (confidence ≥ 0.95) AND (access_count ≥ 20)
```

## 9. Contradiction Resolution

```
OLD_SCORE = old.confidence × old.recency
NEW_SCORE = new.confidence × 1.0

if NEW_SCORE > OLD_SCORE × SUPERSEDE_MARGIN (1.10):  → SUPERSEDED
elif OLD_SCORE > NEW_SCORE × SUPERSEDE_MARGIN:        → CONTESTED
else:                                                  → TIE_CONTESTED
```

## 10. Reawakening

```
cold_engram should reawaken if:
  jaccard(current_context, engram_tokens) ≥ REAWAKEN_WARM (0.50)
  → zone = WARM, access_count += 1
```
