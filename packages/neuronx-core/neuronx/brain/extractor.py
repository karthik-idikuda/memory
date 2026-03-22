"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Memory Extractor                       ║
║  NRNLANG-Ω: EXTRACT — pull storable facts from text     ║
╚══════════════════════════════════════════════════════════╝

BUG-013 FIX: Long inputs (>500 chars) are chunked into sentences,
each processed separately through surprise engine, then deduped.
"""

import re
from typing import List, Dict

from neuronx.config import MAX_INPUT_CHARS_BEFORE_CHUNK
from neuronx.core.surprise import Amygdala


class MemoryExtractor:
    """
    NRNLANG-Ω: EXTRACTOR — splits user input into storable memory units.

    BUG-013 FIX: If input > 500 chars, split into sentences first,
    process each chunk separately, merge and deduplicate by similarity > 0.9.
    """

    def __init__(self):
        self.amygdala = Amygdala()

    @staticmethod
    def split_sentences(text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]

    def extract(self, text: str) -> List[Dict]:
        """
        Extract storable memory items from user text.

        BUG-013 FIX: If input > 500 chars, chunk into sentences.

        Returns list of dicts with keys: text, emotion, decay_class.
        """
        text = text.strip()
        if not text or len(text) < 5:
            return []

        # BUG-013 FIX: Chunk long inputs
        if len(text) > MAX_INPUT_CHARS_BEFORE_CHUNK:
            sentences = self.split_sentences(text)
            if len(sentences) <= 1:
                sentences = self.amygdala.split_compound(text)
        else:
            sentences = self.amygdala.split_compound(text)

        results = []
        seen_normalized = set()

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue

            normalized = sentence.lower().strip()
            if normalized in seen_normalized:
                continue
            seen_normalized.add(normalized)

            # Check similarity with already extracted items
            from neuronx.utils.tokenizer import tokenize, jaccard
            new_tokens = tokenize(sentence)
            is_duplicate = False
            for existing in results:
                existing_tokens = tokenize(existing["text"])
                if jaccard(new_tokens, existing_tokens) > 0.95:
                    is_duplicate = True
                    break

            if is_duplicate:
                continue

            emotion = self.amygdala.detect_emotion(sentence)
            decay_class = self.amygdala.detect_decay_class(sentence)

            results.append({
                "text": sentence,
                "emotion": emotion,
                "decay_class": decay_class,
            })

        return results if results else [{"text": text, "emotion": self.amygdala.detect_emotion(text), "decay_class": self.amygdala.detect_decay_class(text)}]
