"""
Claims Extraction Engine - Identifies and extracts factual claims from text.
Uses spaCy NLP with custom patterns for claim identification.
"""

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

import spacy
from spacy.matcher import Matcher
from spacy.tokens import Doc, Span

from .patterns import (
    get_all_patterns,
    get_high_confidence_keywords,
    get_hedge_words,
    ENTITY_PATTERNS
)

logger = logging.getLogger(__name__)


@dataclass
class Claim:
    """Represents an extracted factual claim."""
    text: str
    claim_type: str
    confidence: float
    span_start: int
    span_end: int
    entities: List[Dict[str, str]]
    context: str
    hedge_words: List[str]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert claim to dictionary for serialization."""
        return {
            "text": self.text,
            "claim_type": self.claim_type,
            "confidence": self.confidence,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "entities": self.entities,
            "context": self.context,
            "hedge_words": self.hedge_words,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class ClaimsExtractor:
    """
    Extracts factual claims from text using NLP patterns.

    Features:
    - Multiple claim type detection (statistical, causal, temporal, etc.)
    - Confidence scoring based on linguistic features
    - Entity extraction for fact verification
    - Hedge word detection for uncertainty assessment
    """

    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize the claims extractor.

        Args:
            model_name: spaCy model to use (default: en_core_web_sm)
        """
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            logger.warning(f"Model {model_name} not found. Attempting to download...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name])
            self.nlp = spacy.load(model_name)

        self.matcher = Matcher(self.nlp.vocab)
        self.patterns = get_all_patterns()
        self.high_confidence_keywords = get_high_confidence_keywords()
        self.hedge_words = get_hedge_words()

        # Register all patterns
        self._register_patterns()

    def _register_patterns(self):
        """Register all claim patterns with the matcher."""
        for claim_type, patterns in self.patterns.items():
            for i, pattern in enumerate(patterns):
                pattern_id = f"{claim_type}_{i}"
                self.matcher.add(pattern_id, [pattern])

    def extract_claims(
        self,
        text: str,
        min_confidence: float = 0.3,
        context_window: int = 50
    ) -> List[Claim]:
        """
        Extract all factual claims from the given text.

        Args:
            text: Input text to analyze
            min_confidence: Minimum confidence threshold (0-1)
            context_window: Number of characters around claim for context

        Returns:
            List of extracted Claim objects
        """
        doc = self.nlp(text)
        matches = self.matcher(doc)

        claims = []
        seen_spans = set()  # Avoid duplicate overlapping claims

        for match_id, start, end in matches:
            span = doc[start:end]
            span_key = (start, end)

            # Skip if we've already processed this span
            if span_key in seen_spans:
                continue
            seen_spans.add(span_key)

            # Get claim type from match ID
            claim_type = self.nlp.vocab.strings[match_id].rsplit("_", 1)[0]

            # Extract entities involved in the claim
            entities = self._extract_entities(span, doc)

            # Detect hedge words
            hedge_words = self._detect_hedge_words(span)

            # Calculate confidence score
            confidence = self._calculate_confidence(
                span, claim_type, entities, hedge_words
            )

            # Skip low-confidence claims
            if confidence < min_confidence:
                continue

            # Get surrounding context
            context = self._get_context(span, text, context_window)

            claim = Claim(
                text=span.text,
                claim_type=claim_type,
                confidence=confidence,
                span_start=span.start_char,
                span_end=span.end_char,
                entities=entities,
                context=context,
                hedge_words=hedge_words
            )

            claims.append(claim)

        # Sort by confidence (highest first)
        claims.sort(key=lambda c: c.confidence, reverse=True)

        logger.info(f"Extracted {len(claims)} claims from text (length: {len(text)})")
        return claims

    def _extract_entities(self, span: Span, doc: Doc) -> List[Dict[str, str]]:
        """
        Extract named entities from the claim span.

        Args:
            span: spaCy Span object representing the claim
            doc: Full document for context

        Returns:
            List of entity dictionaries with text, type, and label
        """
        entities = []

        # Get entities within the span
        for ent in span.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })

        # Also check for entities in the sentence containing this span
        sent = span.sent
        for ent in sent.ents:
            if ent not in span.ents:
                # Include nearby entities for context
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "nearby": True
                })

        return entities

    def _detect_hedge_words(self, span: Span) -> List[str]:
        """
        Detect hedge words in the claim that indicate uncertainty.

        Args:
            span: spaCy Span object

        Returns:
            List of hedge words found
        """
        found_hedges = []
        span_text_lower = span.text.lower()

        for hedge in self.hedge_words:
            if hedge in span_text_lower:
                found_hedges.append(hedge)

        return found_hedges

    def _calculate_confidence(
        self,
        span: Span,
        claim_type: str,
        entities: List[Dict],
        hedge_words: List[str]
    ) -> float:
        """
        Calculate confidence score for the claim (0-1).

        Factors:
        - Claim type (some types are more reliable)
        - Presence of entities (more entities = higher confidence)
        - High-confidence keywords
        - Hedge words (reduce confidence)
        - Sentence structure quality

        Args:
            span: spaCy Span object
            claim_type: Type of claim
            entities: Extracted entities
            hedge_words: Detected hedge words

        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence by claim type
        type_confidence = {
            "statistical": 0.8,
            "temporal": 0.7,
            "definitional": 0.75,
            "causal": 0.6,
            "comparative": 0.65,
            "attribution": 0.7
        }
        base_score = type_confidence.get(claim_type, 0.5)

        # Entity bonus (more specific entities = higher confidence)
        entity_bonus = min(0.15, len(entities) * 0.05)

        # High-confidence keyword bonus
        keyword_bonus = 0.0
        span_text_lower = span.text.lower()
        for category, keywords in self.high_confidence_keywords.items():
            for keyword in keywords:
                if keyword in span_text_lower:
                    keyword_bonus += 0.02
        keyword_bonus = min(keyword_bonus, 0.15)

        # Hedge word penalty
        hedge_penalty = min(0.3, len(hedge_words) * 0.1)

        # Sentence quality (penalize very short or very long claims)
        length = len(span.text.split())
        if length < 3:
            length_penalty = 0.2
        elif length > 30:
            length_penalty = 0.15
        else:
            length_penalty = 0.0

        # Calculate final confidence
        confidence = base_score + entity_bonus + keyword_bonus - hedge_penalty - length_penalty

        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))

    def _get_context(self, span: Span, full_text: str, window: int) -> str:
        """
        Get surrounding context for the claim.

        Args:
            span: spaCy Span object
            full_text: Original text
            window: Number of characters before/after

        Returns:
            Context string
        """
        start = max(0, span.start_char - window)
        end = min(len(full_text), span.end_char + window)

        context = full_text[start:end]

        # Add ellipsis if truncated
        if start > 0:
            context = "..." + context
        if end < len(full_text):
            context = context + "..."

        return context

    def extract_claims_with_sentences(self, text: str, min_confidence: float = 0.3) -> Dict:
        """
        Extract claims and organize them by sentence for better structure.

        Args:
            text: Input text
            min_confidence: Minimum confidence threshold

        Returns:
            Dictionary with claims organized by sentence
        """
        doc = self.nlp(text)
        claims = self.extract_claims(text, min_confidence)

        # Organize by sentence
        result = {
            "total_claims": len(claims),
            "sentences": []
        }

        for sent in doc.sents:
            sent_claims = [
                c for c in claims
                if sent.start_char <= c.span_start < sent.end_char
            ]

            if sent_claims:
                result["sentences"].append({
                    "text": sent.text,
                    "start": sent.start_char,
                    "end": sent.end_char,
                    "claims": [c.to_dict() for c in sent_claims],
                    "claim_count": len(sent_claims)
                })

        return result


def main():
    """Example usage of the Claims Extractor."""
    # Example text with various types of claims
    text = """
    According to recent studies, 75% of users prefer faster search results.
    The new algorithm increased accuracy by 30% since January 2024.
    Climate change causes rising sea levels, which threatens coastal cities.
    Machine learning is a subset of artificial intelligence.
    Python is more popular than Java for data science applications.
    The company will launch the product in Q4 2024.
    """

    extractor = ClaimsExtractor()
    claims = extractor.extract_claims(text)

    print(f"\nExtracted {len(claims)} claims:\n")
    for i, claim in enumerate(claims, 1):
        print(f"{i}. [{claim.claim_type.upper()}] (confidence: {claim.confidence:.2f})")
        print(f"   Text: {claim.text}")
        print(f"   Entities: {[e['text'] for e in claim.entities]}")
        if claim.hedge_words:
            print(f"   Hedge words: {claim.hedge_words}")
        print()


if __name__ == "__main__":
    main()
