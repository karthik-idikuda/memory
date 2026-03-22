"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Memory Extractor                       ║
║  NRNLANG-Ω: <@ PULL_FROM_AI — extract storable memories  ║
╚══════════════════════════════════════════════════════════╝

Uses Claude API (PROMPT_EXTRACT) to extract structured memories
from user messages. Falls back to rule-based extraction if API
is unavailable (offline mode).
"""

import json
import re
import logging

from core.surprise import Amygdala

logger = logging.getLogger("NEURONX.EXTRACTOR")


class MemoryExtractor:
    """
    NRNLANG-Ω: EXTRACTOR — pulls structured memories from raw text.

    AI mode:   Uses PROMPT_EXTRACT → Claude → JSON array of memories
    Rule mode: Uses heuristics → split sentences → classify each
    """

    def __init__(self, ai_client=None, model: str = "claude-sonnet-4-20250514"):
        self.ai_client = ai_client
        self.model = model
        self.amygdala = Amygdala()

    def extract(self, message: str) -> list[dict]:
        """
        Extract storable memories from a user message.

        Returns list of:
        {
            "text": str,
            "decay_class": str,
            "emotion": str,
            "confidence": float,
            "tags": list[str],
            "subject": str,
        }
        """
        if self.ai_client:
            try:
                return self._extract_ai(message)
            except Exception as e:
                logger.warning(f"AI extraction failed: {e}, falling back to rules")

        return self._extract_rules(message)

    def _extract_ai(self, message: str) -> list[dict]:
        """Use Claude API + PROMPT_EXTRACT to extract memories."""
        from interface.prompts import MEMORY_EXTRACTION_PROMPT

        prompt = MEMORY_EXTRACTION_PROMPT.format(user_message=message)

        response = self.ai_client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()

        # Parse JSON from response
        # Handle possible markdown code blocks
        if text.startswith("```"):
            text = re.sub(r"```(?:json)?\s*", "", text)
            text = text.rstrip("`").strip()

        memories = json.loads(text)

        if not isinstance(memories, list):
            return []

        # Validate each memory
        valid = []
        for m in memories:
            if isinstance(m, dict) and "text" in m:
                valid.append({
                    "text": m.get("text", ""),
                    "decay_class": m.get("decay_class", "fact"),
                    "emotion": m.get("emotion", "neutral"),
                    "confidence": float(m.get("confidence", 0.8)),
                    "tags": m.get("tags", []),
                    "subject": m.get("subject", ""),
                })
        return valid

    def _extract_rules(self, message: str) -> list[dict]:
        """
        Rule-based extraction fallback (no API needed).

        Splits compound sentences, classifies each piece,
        converts to third person, returns structured memories.
        """
        # Split into individual ideas
        ideas = self.amygdala.split_compound(message)

        memories = []
        for idea in ideas:
            idea = idea.strip()
            if len(idea) < 10:
                continue

            # Skip pure questions and greetings
            if self._is_noise(idea):
                continue

            emotion = self.amygdala.detect_emotion(idea)
            decay_class = self.amygdala.detect_decay_class(idea)

            # Convert to third person
            text = self._to_third_person(idea)

            memories.append({
                "text": text,
                "decay_class": decay_class,
                "emotion": emotion,
                "confidence": 0.80,
                "tags": self._auto_tag(idea),
                "subject": self._extract_subject(idea),
            })

        return memories

    @staticmethod
    def _is_noise(text: str) -> bool:
        """Check if text is noise (greetings, questions, filler)."""
        noise_patterns = [
            r"^(hi|hello|hey|yo|sup|greetings)\b",
            r"^(thanks|thank you|ok|okay|sure|got it|alright)\b",
            r"^(what|how|when|where|why|who|can you|could you|would you)\b.*\?$",
        ]
        text_lower = text.lower().strip()
        for pattern in noise_patterns:
            if re.match(pattern, text_lower):
                return True
        return False

    @staticmethod
    def _to_third_person(text: str) -> str:
        """Convert first person ('I love') to third person ('User loves')."""
        replacements = [
            (r"\bi am\b", "User is"),
            (r"\bi'm\b", "User is"),
            (r"\bi have\b", "User has"),
            (r"\bi've\b", "User has"),
            (r"\bi was\b", "User was"),
            (r"\bi will\b", "User will"),
            (r"\bi'll\b", "User will"),
            (r"\bi would\b", "User would"),
            (r"\bi'd\b", "User would"),
            (r"\bi can\b", "User can"),
            (r"\bi do\b", "User does"),
            (r"\bi don't\b", "User doesn't"),
            (r"\bi didn't\b", "User didn't"),
            (r"\bi like\b", "User likes"),
            (r"\bi love\b", "User loves"),
            (r"\bi hate\b", "User hates"),
            (r"\bi want\b", "User wants"),
            (r"\bi need\b", "User needs"),
            (r"\bi think\b", "User thinks"),
            (r"\bi feel\b", "User feels"),
            (r"\bi believe\b", "User believes"),
            (r"\bi prefer\b", "User prefers"),
            (r"\bi know\b", "User knows"),
            (r"\bi live\b", "User lives"),
            (r"\bi work\b", "User works"),
            (r"\bi study\b", "User studies"),
            (r"\bmy\b", "User's"),
            (r"\bme\b", "User"),
            (r"\bmine\b", "User's"),
            (r"\bi\b", "User"),
        ]
        result = text
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result

    @staticmethod
    def _auto_tag(text: str) -> list[str]:
        """Auto-generate tags from text content."""
        tags = []
        text_lower = text.lower()

        tag_keywords = {
            "person": ["friend", "family", "mom", "dad", "brother", "sister",
                       "wife", "husband", "partner", "colleague"],
            "place": ["city", "country", "home", "office", "school", "live",
                      "moved", "travel", "visit"],
            "preference": ["love", "hate", "like", "prefer", "enjoy",
                           "favorite", "favourite", "best", "worst"],
            "work": ["work", "job", "career", "company", "project",
                     "office", "boss", "colleague"],
            "health": ["health", "exercise", "gym", "diet", "sleep",
                       "doctor", "sick", "medication"],
            "hobby": ["hobby", "play", "game", "sport", "music",
                      "read", "cook", "draw", "paint"],
            "event": ["yesterday", "today", "last week", "went", "visited",
                      "attended", "happened", "celebrated"],
            "fact": ["is", "are", "was", "capital", "population", "year"],
        }

        for tag, keywords in tag_keywords.items():
            if any(kw in text_lower for kw in keywords):
                tags.append(tag)
                if len(tags) >= 4:
                    break

        return tags if tags else ["general"]

    @staticmethod
    def _extract_subject(text: str) -> str:
        """Extract a 2-3 word subject from text."""
        # Remove common prefixes
        text = re.sub(
            r"^(i|user|we|they|he|she)\s+(am|is|are|was|were|have|has|had|"
            r"love|like|hate|prefer|think|feel|believe|want|need|work|live|study)\s+",
            "", text, flags=re.IGNORECASE
        ).strip()

        words = text.split()[:3]
        return " ".join(words) if words else "unknown"
