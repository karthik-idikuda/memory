"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — AMYGDALA (Surprise + Emotion Engine)   ║
║  NRNLANG-Ω: ⚡ SPARK — high surprise moment              ║
╚══════════════════════════════════════════════════════════╝

The AMYGDALA is the gatekeeper. Every incoming idea passes through
it for surprise scoring. It decides:
  SURPRISE < 0.25                          → ECHO   (already known)
  0.25 <= SURPRISE <= 0.85                 → FORGE  (genuinely new)
  SURPRISE > 0.85 AND best_jaccard >= 0.15 → CLASH  (contradicts)
  SURPRISE > 0.85 AND best_jaccard < 0.15  → FORGE  (BUG-003 FIX)

FORMULA:
  WEIGHTED_SIMILARITY(new, engram):
    sim = JACCARD(new, engram.raw)
    rec = exp(-λ × days_since_last_seen)
    return sim × engram.confidence × rec

  SURPRISE(new_text, memory_bank):
    if len(memory_bank) == 0: return 1.0
    scores = {id: WEIGHTED_SIMILARITY(new_text, e) for id, e in bank}
    best = max(scores)
    return 1.0 - best
"""

from typing import Optional, List, Dict
from dataclasses import dataclass

from neuronx.config import (
    SURPRISE_ECHO_THRESHOLD, SURPRISE_CLASH_THRESHOLD,
    CLASH_JACCARD_GATE,
)
from neuronx.core.node import EngramNode
from neuronx.utils.tokenizer import tokenize, jaccard


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EMOTION DETECTION KEYWORDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

EMOTION_KEYWORDS = {
    "happy": {
        "love", "enjoy", "happy", "great", "amazing", "wonderful",
        "excited", "fantastic", "awesome", "brilliant", "perfect",
        "glad", "pleased", "delighted", "joyful", "best",
    },
    "sad": {
        "hate", "dislike", "miss", "sad", "terrible", "awful",
        "depressed", "worst", "horrible", "miserable", "sucks",
        "disappointed", "unhappy", "unfortunately", "lost",
    },
    "curious": {
        "wonder", "interested", "curious", "thinking", "question",
        "investigate", "explore", "research", "fascinating",
    },
    "excited": {
        "excited", "cant wait", "thrilled", "pumped", "stoked",
        "anticipating", "eager", "looking forward",
    },
    "angry": {
        "angry", "frustrated", "annoyed", "furious", "rage",
        "irritated", "infuriated", "livid", "fed up",
    },
    "fear": {
        "afraid", "scared", "worried", "anxious", "terrified",
        "nervous", "panic", "dread", "fearful",
    },
    "love": {
        "adore", "cherish", "treasure", "devoted", "passion",
        "beloved", "soulmate", "darling",
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECAY CLASS KEYWORDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

DECAY_CLASS_KEYWORDS = {
    "identity": {
        "i am", "i'm", "my name", "i work", "i live", "my job",
        "i have", "i own", "my age", "i study", "my family",
        "my wife", "my husband", "my partner", "born in",
    },
    "event": {
        "yesterday", "last week", "last month", "last year",
        "happened", "went", "visited", "did", "today",
        "this morning", "tonight", "just now", "recently",
        "attended", "celebrated", "traveled", "bought",
    },
    "emotion": {
        "felt", "feeling", "makes me", "i was so", "so happy",
        "so sad", "so angry", "emotional", "cried", "laughed",
    },
    "opinion": {
        "think", "feel", "believe", "prefer", "like", "hate",
        "love", "wish", "hope", "opinion", "best", "worst",
        "favorite", "favourite", "rather",
    },
}


@dataclass
class SurpriseResult:
    """Result of surprise computation."""
    surprise_score: float
    best_match_id: Optional[str]
    best_jaccard: float
    action: str  # ECHO / FORGE / CLASH
    emotion: str
    decay_class: str


class Amygdala:
    """
    NRNLANG-Ω: AMYGDALA — The surprise and emotion detection layer.

    Processes every incoming idea:
    1. Tokenizes the input
    2. Finds best matching engram via WEIGHTED_SIMILARITY
    3. Computes surprise score
    4. Routes to ECHO / FORGE / CLASH (with CLASH gate — BUG-003 FIX)
    """

    @staticmethod
    def detect_emotion(text: str) -> str:
        """NRNLANG-Ω: DETECT emotion using keyword analysis."""
        text_lower = text.lower()
        best_emotion = "neutral"
        best_score = 0
        for emotion, keywords in EMOTION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_emotion = emotion
        return best_emotion

    @staticmethod
    def detect_decay_class(text: str) -> str:
        """NRNLANG-Ω: CLASSIFY — determine decay class."""
        text_lower = text.lower()
        for cls in ["identity", "event", "emotion", "opinion"]:
            keywords = DECAY_CLASS_KEYWORDS[cls]
            if any(kw in text_lower for kw in keywords):
                return cls
        return "fact"

    def compute(
        self,
        input_text: str,
        memory_bank: Dict[str, EngramNode],
    ) -> SurpriseResult:
        """
        NRNLANG-Ω: SURPRISE computation with CLASH gate (BUG-003 FIX).

        SURPRISE(new_text, memory_bank):
          if len(memory_bank) == 0: return 1.0, None, 0.0
          For each active engram:
            sim = JACCARD(new, engram.raw)
            rec = exp(-λ × days) × confidence
            weighted = sim × rec
          best = max(weighted)
          surprise = 1.0 - best

        ACTION:
          < 0.25                         → ECHO
          0.25..0.85                     → FORGE
          > 0.85 AND best_jaccard >= 0.15 → CLASH
          > 0.85 AND best_jaccard < 0.15  → FORGE (BUG-003 FIX)
        """
        emotion = self.detect_emotion(input_text)
        decay_class = self.detect_decay_class(input_text)
        input_tokens = tokenize(input_text)

        if not memory_bank:
            return SurpriseResult(
                surprise_score=1.0,
                best_match_id=None,
                best_jaccard=0.0,
                action="FORGE",
                emotion=emotion,
                decay_class=decay_class,
            )

        best_weighted = 0.0
        best_raw_jaccard = 0.0
        best_match_id: Optional[str] = None

        for eid, engram in memory_bank.items():
            if not engram.is_active_engram():
                continue

            engram_tokens = tokenize(engram.raw)
            sim = jaccard(input_tokens, engram_tokens)
            rec = engram.recency_score
            weighted = sim * engram.confidence * rec

            if weighted > best_weighted:
                best_weighted = weighted
                best_raw_jaccard = sim
                best_match_id = eid

        surprise = 1.0 - best_weighted
        surprise = max(0.0, min(1.0, surprise))

        # ── BUG-003 FIX: CLASH gate enforcement ──
        if surprise < SURPRISE_ECHO_THRESHOLD:
            action = "ECHO"
        elif surprise <= SURPRISE_CLASH_THRESHOLD:
            action = "FORGE"
        else:
            # surprise > 0.85
            if best_raw_jaccard >= CLASH_JACCARD_GATE:
                action = "CLASH"
            else:
                action = "FORGE"  # No topic overlap → not a clash

        return SurpriseResult(
            surprise_score=surprise,
            best_match_id=best_match_id,
            best_jaccard=best_raw_jaccard,
            action=action,
            emotion=emotion,
            decay_class=decay_class,
        )

    @staticmethod
    def split_compound(text: str) -> List[str]:
        """
        NRNLANG-Ω: SPLIT compound sentences into individual ideas.
        """
        connectors = [" and ", " but ", " however ", " although ", " also ", ". ", "! ", "? "]
        ideas = [text]
        for conn in connectors:
            new_ideas = []
            for idea in ideas:
                parts = idea.split(conn)
                for part in parts:
                    part = part.strip()
                    if len(part) > 10:
                        new_ideas.append(part)
                    elif new_ideas:
                        new_ideas[-1] += " " + part
            ideas = new_ideas if new_ideas else ideas

        seen = set()
        unique = []
        for idea in ideas:
            normalized = idea.lower().strip()
            if normalized not in seen and len(normalized) > 5:
                seen.add(normalized)
                unique.append(idea)
        return unique if unique else [text]
