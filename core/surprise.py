"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — AMYGDALA (Surprise + Emotion Engine)   ║
║  NRNLANG-Ω: ⚡ SPARK — high surprise moment              ║
╚══════════════════════════════════════════════════════════╝

The AMYGDALA is the gatekeeper. Every incoming idea passes through
it for surprise scoring. It decides:
  SURPRISE < 0.25  → ECHO      (already known, strengthen it)
  SURPRISE 0.25–0.85 → FORGE   (genuinely new, store it)
  SURPRISE > 0.85  → CLASH     (contradicts existing truth)
"""

import math
import re
from typing import Optional

from core.node import Engram, DECAY_RATES


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NRNLANG-Ω ACTION THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

THRESHOLD_ECHO = 0.25     # Below this → already known → strengthen
THRESHOLD_FORGE = 0.85    # Below this → genuinely new → store
# Above THRESHOLD_FORGE → contradiction detected → CLASH

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STOP WORDS — filtered from tokens
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

STOP_WORDS = {
    "the", "and", "or", "but", "is", "are", "was", "were", "been",
    "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "i", "you", "my", "your", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them", "our", "their", "its",
    "a", "an", "this", "that", "these", "those",
    "do", "does", "did", "have", "has", "had", "will", "would",
    "can", "could", "should", "may", "might", "shall",
    "not", "no", "so", "if", "then", "than", "too", "very",
    "just", "also", "now", "here", "there", "when", "where",
    "what", "which", "who", "whom", "how", "why",
    "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "only", "own", "same",
    "about", "up", "out", "off", "over", "under",
    "again", "further", "once", "into", "through", "during",
    "before", "after", "above", "below", "between", "because",
    "until", "while", "being", "having", "doing",
    "really", "actually", "basically", "literally", "always",
    "never", "sometimes", "often", "usually", "still", "already",
    "even", "much", "many", "well", "back", "going", "like",
    "know", "think", "want", "get", "got", "make", "made",
    "say", "said", "tell", "told", "give", "take", "come",
    "go", "went", "see", "saw", "look", "find", "let",
}

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


class Amygdala:
    """
    NRNLANG-Ω: AMYGDALA — The surprise and emotion detection layer.

    Processes every incoming idea:
    1. Tokenizes the input
    2. Finds best matching engram in existing memories
    3. Computes surprise score
    4. Routes to ECHO / FORGE / CLASH
    """

    def __init__(self):
        pass

    @staticmethod
    def tokenize(text: str) -> set[str]:
        """
        NRNLANG-Ω: TOKENIZE — extract meaningful signal tokens.

        Rules:
        1. Lowercase everything
        2. Remove punctuation
        3. Split on spaces
        4. Remove tokens shorter than 3 chars
        5. Remove stop words
        """
        # Lowercase and remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)

        # Split and filter
        tokens = set()
        for word in text.split():
            if len(word) >= 3 and word not in STOP_WORDS:
                tokens.add(word)

        return tokens

    @staticmethod
    def jaccard_similarity(set_a: set, set_b: set) -> float:
        """
        NRNLANG-Ω: SIMILARITY(A, B) =
          |tokens_A ∩ tokens_B| / |tokens_A ∪ tokens_B|

        Jaccard similarity — counts meaningful word overlap.
        """
        if not set_a or not set_b:
            return 0.0

        intersection = set_a & set_b
        union = set_a | set_b

        if not union:
            return 0.0

        return len(intersection) / len(union)

    @staticmethod
    def detect_emotion(text: str) -> str:
        """
        NRNLANG-Ω: DETECT emotion using keyword analysis.

        Returns: happy/sad/curious/excited/angry/fear/love/neutral
        """
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
        """
        NRNLANG-Ω: CLASSIFY — determine decay class.

        Priority: identity > event > emotion > opinion > fact
        """
        text_lower = text.lower()

        for cls in ["identity", "event", "emotion", "opinion"]:
            keywords = DECAY_CLASS_KEYWORDS[cls]
            if any(kw in text_lower for kw in keywords):
                return cls

        return "fact"  # default

    def compute_surprise(
        self,
        input_text: str,
        existing_engrams: list[Engram],
    ) -> tuple[float, Optional[Engram], str]:
        """
        NRNLANG-Ω: FORMULA D — SURPRISE SCORE

        SURPRISE = 1 - max(SIMILARITY × confidence × RECENCY)

        Returns:
            (surprise_score, best_matching_engram, action)
            action is one of: "ECHO", "FORGE", "CLASH"
        """
        input_tokens = self.tokenize(input_text)

        if not existing_engrams:
            # No memories exist yet — everything is new
            return (1.0, None, "FORGE")

        best_weighted_similarity = 0.0
        best_raw_similarity = 0.0
        best_match: Optional[Engram] = None

        for engram in existing_engrams:
            if not engram.is_active:
                continue

            engram_tokens = self.tokenize(engram.raw)
            similarity = self.jaccard_similarity(input_tokens, engram_tokens)
            recency = engram.recency_score

            weighted = similarity * engram.confidence * recency

            if weighted > best_weighted_similarity:
                best_weighted_similarity = weighted
                best_raw_similarity = similarity
                best_match = engram

        surprise = 1.0 - best_weighted_similarity

        # ── Special Cases ──

        # Low confidence existing engram → boost surprise
        if best_match and best_match.confidence < 0.3:
            surprise = min(1.0, surprise + 0.2)

        # Time reference signals potential update
        input_lower = input_text.lower()
        time_refs = ["used to", "anymore", "no longer", "stopped", "changed"]
        if any(ref in input_lower for ref in time_refs):
            surprise = min(1.0, surprise + 0.3)

        # New proper noun detection
        words = input_text.split()
        for word in words:
            if word[0:1].isupper() and len(word) > 2:
                # Check if this capitalized word exists in any engram
                found = False
                for engram in existing_engrams:
                    if word.lower() in engram.raw.lower():
                        found = True
                        break
                if not found:
                    surprise = max(surprise, 0.9)  # New entity
                    break

        surprise = max(0.0, min(1.0, surprise))

        # ── Determine Action ──
        # CLASH only triggers when there IS a related match with topic overlap.
        # Completely novel info (zero/low similarity) should FORGE, not CLASH.
        if surprise < THRESHOLD_ECHO:
            action = "ECHO"
        elif surprise <= THRESHOLD_FORGE:
            action = "FORGE"
        elif best_raw_similarity >= 0.15:
            action = "CLASH"  # Only clash when there's a related existing memory
        else:
            action = "FORGE"  # Completely new topic — just store it

        return (surprise, best_match, action)

    @staticmethod
    def split_compound(text: str) -> list[str]:
        """
        NRNLANG-Ω: SPLIT compound sentences into individual ideas.
        "I love pizza and hate cold weather" → TWO ideas.
        """
        # Split on common compound connectors
        connectors = [
            " and ", " but ", " however ", " although ",
            " also ", ". ", "! ", "? ",
        ]

        ideas = [text]
        for conn in connectors:
            new_ideas = []
            for idea in ideas:
                parts = idea.split(conn)
                for part in parts:
                    part = part.strip()
                    if len(part) > 10:  # Minimum idea length
                        new_ideas.append(part)
                    elif new_ideas:
                        # Append short parts to previous idea
                        new_ideas[-1] += " " + part
            ideas = new_ideas if new_ideas else ideas

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for idea in ideas:
            normalized = idea.lower().strip()
            if normalized not in seen and len(normalized) > 5:
                seen.add(normalized)
                unique.append(idea)

        return unique if unique else [text]

    def process_input(
        self,
        text: str,
        existing_engrams: list[Engram],
    ) -> list[dict]:
        """
        NRNLANG-Ω: Full input processing pipeline.

        INPUT ~> INPUT_PROCESSOR ~> AMYGDALA

        Returns list of processed ideas, each with:
        {
            "text": str,
            "emotion": str,
            "decay_class": str,
            "surprise": float,
            "best_match": Optional[Engram],
            "action": str,  # ECHO / FORGE / CLASH
        }
        """
        # Split compound statements
        ideas = self.split_compound(text)

        results = []
        for idea in ideas:
            emotion = self.detect_emotion(idea)
            decay_class = self.detect_decay_class(idea)
            surprise, best_match, action = self.compute_surprise(
                idea, existing_engrams
            )

            results.append({
                "text": idea,
                "emotion": emotion,
                "decay_class": decay_class,
                "surprise": surprise,
                "best_match": best_match,
                "action": action,
            })

        return results
