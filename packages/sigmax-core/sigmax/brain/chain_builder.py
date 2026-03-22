"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Chain Builder                            ║
║  CAULANG-Ω: CHAIN — extract WHY from raw text            ║
╚══════════════════════════════════════════════════════════╝

Extracts causal relationships from text using:
1. Rule-based pattern detection (fast, local)
2. AI refinement via LLM (optional, for complex text)

Detects: direct, indirect, conditional, temporal, inhibitory,
correlative, and counterfactual relationships.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from sigmax.config import (
    CAUSAL_SIGNAL_WORDS,
    PROMPT_EXTRACT_CHAINS,
    MAX_INPUT_CHARS,
)
from sigmax.core.causenode import CauseNode
from sigmax.core.tokenizer import (
    detect_causal_signals,
    has_causal_language,
    split_causal_text,
    extract_subjects,
    normalize_text,
    word_overlap,
)
from sigmax.exceptions import ChainExtractionError


# Pre-compiled causal patterns
_PATTERNS = [
    # "X causes Y"
    (re.compile(
        r'(.{5,80}?)\s+(?:causes?|caused)\s+(.{5,80})',
        re.IGNORECASE
    ), "direct"),
    # "X leads to Y"
    (re.compile(
        r'(.{5,80}?)\s+(?:leads?\s+to|led\s+to)\s+(.{5,80})',
        re.IGNORECASE
    ), "direct"),
    # "X results in Y"
    (re.compile(
        r'(.{5,80}?)\s+(?:results?\s+in|resulted\s+in)\s+(.{5,80})',
        re.IGNORECASE
    ), "direct"),
    # "because of X, Y" / "Y because X"
    (re.compile(
        r'(.{5,80}?)\s+because\s+(.{5,80})',
        re.IGNORECASE
    ), "direct"),
    # "X therefore Y"
    (re.compile(
        r'(.{5,80}?)\s+(?:therefore|thus|hence|consequently)\s+(.{5,80})',
        re.IGNORECASE
    ), "direct"),
    # "X prevents Y"
    (re.compile(
        r'(.{5,80}?)\s+(?:prevents?|prevented|blocks?|blocked|inhibits?)\s+(.{5,80})',
        re.IGNORECASE
    ), "inhibitory"),
    # "if X then Y"
    (re.compile(
        r'if\s+(.{5,80}?)\s*,?\s*then\s+(.{5,80})',
        re.IGNORECASE
    ), "conditional"),
    # "X triggers Y"
    (re.compile(
        r'(.{5,80}?)\s+(?:triggers?|triggered|sparks?|sparked)\s+(.{5,80})',
        re.IGNORECASE
    ), "direct"),
    # "X enables Y"
    (re.compile(
        r'(.{5,80}?)\s+(?:enables?|enabled|allows?|allowed)\s+(.{5,80})',
        re.IGNORECASE
    ), "direct"),
    # "due to X, Y" / "Y due to X"
    (re.compile(
        r'(.{5,80}?)\s+due\s+to\s+(.{5,80})',
        re.IGNORECASE
    ), "direct"),
    # "X affects Y"
    (re.compile(
        r'(.{5,80}?)\s+(?:affects?|affected|influences?|influenced)\s+(.{5,80})',
        re.IGNORECASE
    ), "indirect"),
    # "X correlates with Y"
    (re.compile(
        r'(.{5,80}?)\s+(?:correlates?\s+with|associated\s+with)\s+(.{5,80})',
        re.IGNORECASE
    ), "correlative"),
    # "after X, Y" (temporal)
    (re.compile(
        r'after\s+(.{5,80}?)\s*,\s*(.{5,80})',
        re.IGNORECASE
    ), "temporal"),
    # "when X, Y" (temporal)
    (re.compile(
        r'when\s+(.{5,80}?)\s*,\s*(.{5,80})',
        re.IGNORECASE
    ), "temporal"),
    # "without X, Y would not" (counterfactual)
    (re.compile(
        r'without\s+(.{5,80}?)\s*,\s*(.{5,80})',
        re.IGNORECASE
    ), "counterfactual"),
]


def _clean_fragment(text: str) -> str:
    """Clean a cause/effect text fragment."""
    text = text.strip()
    # Remove leading conjunctions
    text = re.sub(r'^(?:and|but|so|or|yet)\s+', '', text, flags=re.IGNORECASE)
    # Remove trailing punctuation
    text = text.rstrip('.,;:!?')
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


class ChainBuilder:
    """
    Extracts causal chains from text.

    Two modes:
    1. Rule-based: fast, local, pattern-matching
    2. AI-assisted: uses LLM for complex chain extraction

    Usage:
        builder = ChainBuilder()
        nodes = builder.extract(text)
        nodes = builder.extract_with_ai(text, llm_fn)
    """

    def __init__(self):
        self._extraction_count = 0
        self._ai_extraction_count = 0

    def extract(self, text: str) -> List[CauseNode]:
        """
        Extract causal chains from text using rule-based patterns.
        Returns a list of CauseNodes (not yet persisted).
        """
        if not text or not isinstance(text, str):
            return []

        text = text[:MAX_INPUT_CHARS]  # truncate overlong input

        # Check for causal language first (fast gate)
        if not has_causal_language(text):
            # Try split-based extraction as fallback
            pairs = split_causal_text(text)
            if not pairs:
                return []
            return self._pairs_to_nodes(pairs, "direct")

        # Pattern-based extraction
        nodes = []
        seen = set()  # de-duplicate

        for pattern, cause_type in _PATTERNS:
            for match in pattern.finditer(text):
                cause = _clean_fragment(match.group(1))
                effect = _clean_fragment(match.group(2))

                if not cause or not effect:
                    continue
                if len(cause) < 3 or len(effect) < 3:
                    continue

                # De-duplicate by normalized text
                key = (normalize_text(cause), normalize_text(effect))
                if key in seen:
                    continue
                seen.add(key)

                # Extract metadata
                subjects = extract_subjects(cause + " " + effect)
                subject = subjects[0] if subjects else ""

                node = CauseNode(
                    cause=cause,
                    effect=effect,
                    cause_type=cause_type,
                    confidence=0.50,
                    tags=subjects[:5],
                    subject=subject,
                    source="rule_extraction",
                    decay_class="medium",
                )
                nodes.append(node)

        # Also try split-based extraction for anything missed
        pairs = split_causal_text(text)
        for cause, effect in pairs:
            cause = _clean_fragment(cause)
            effect = _clean_fragment(effect)
            key = (normalize_text(cause), normalize_text(effect))
            if key not in seen and len(cause) > 3 and len(effect) > 3:
                seen.add(key)
                subjects = extract_subjects(cause + " " + effect)
                node = CauseNode(
                    cause=cause,
                    effect=effect,
                    cause_type="direct",
                    confidence=0.40,
                    tags=subjects[:5],
                    subject=subjects[0] if subjects else "",
                    source="rule_extraction",
                    decay_class="medium",
                )
                nodes.append(node)

        self._extraction_count += len(nodes)
        return nodes

    def extract_with_ai(
        self,
        text: str,
        llm_fn: Callable[[str], str],
    ) -> List[CauseNode]:
        """
        Extract causal chains using an AI/LLM function.

        Args:
            text: Input text to analyze
            llm_fn: Function that takes a prompt string and returns LLM response

        Returns:
            List of CauseNodes extracted by the LLM.
        """
        if not text:
            return []

        text = text[:MAX_INPUT_CHARS]

        prompt = PROMPT_EXTRACT_CHAINS.format(message=text)

        try:
            response = llm_fn(prompt)
            chains = self._parse_ai_response(response)
        except Exception as e:
            raise ChainExtractionError(f"AI extraction failed: {e}")

        nodes = []
        for chain in chains:
            try:
                cause = chain.get('cause', '').strip()
                effect = chain.get('effect', '').strip()
                if not cause or not effect:
                    continue

                node = CauseNode(
                    cause=cause,
                    effect=effect,
                    cause_type=chain.get('type', 'direct'),
                    confidence=float(chain.get('confidence', 0.60)),
                    tags=chain.get('tags', []),
                    subject=chain.get('subject', ''),
                    source="ai_extraction",
                    decay_class=chain.get('decay_class', 'medium'),
                )
                nodes.append(node)
            except Exception:
                continue

        self._ai_extraction_count += len(nodes)
        return nodes

    def _pairs_to_nodes(
        self, pairs: List[Tuple[str, str]], default_type: str
    ) -> List[CauseNode]:
        """Convert (cause, effect) pairs to CauseNodes."""
        nodes = []
        for cause, effect in pairs:
            cause = _clean_fragment(cause)
            effect = _clean_fragment(effect)
            if cause and effect and len(cause) > 3 and len(effect) > 3:
                subjects = extract_subjects(cause + " " + effect)
                node = CauseNode(
                    cause=cause,
                    effect=effect,
                    cause_type=default_type,
                    confidence=0.40,
                    tags=subjects[:5],
                    subject=subjects[0] if subjects else "",
                    source="rule_extraction",
                    decay_class="medium",
                )
                nodes.append(node)
        return nodes

    def _parse_ai_response(self, response: str) -> List[dict]:
        """Parse LLM response into list of chain dicts."""
        response = response.strip()

        # Try to find JSON array in response
        # Handle markdown code blocks
        if '```' in response:
            match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response, re.DOTALL)
            if match:
                response = match.group(1).strip()

        # Try direct JSON parse
        try:
            result = json.loads(response)
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                return [result]
        except json.JSONDecodeError:
            pass

        # Try to find JSON array in text
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return []

    def find_duplicates(
        self,
        new_nodes: List[CauseNode],
        existing_nodes: List[CauseNode],
        threshold: float = 0.70,
    ) -> List[Tuple[CauseNode, CauseNode, float]]:
        """
        Find potential duplicates between new and existing nodes.
        Returns list of (new_node, existing_node, similarity) tuples.
        """
        duplicates = []
        for new in new_nodes:
            for existing in existing_nodes:
                cause_sim = word_overlap(new.cause, existing.cause)
                effect_sim = word_overlap(new.effect, existing.effect)
                combined = (cause_sim + effect_sim) / 2.0
                if combined >= threshold:
                    duplicates.append((new, existing, combined))
        return duplicates

    @property
    def stats(self) -> dict:
        return {
            'rule_extractions': self._extraction_count,
            'ai_extractions': self._ai_extraction_count,
            'total': self._extraction_count + self._ai_extraction_count,
        }
