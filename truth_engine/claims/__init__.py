"""Claims extraction module for identifying factual statements in text."""

from .extractor import ClaimsExtractor, Claim
from .patterns import get_all_patterns, get_high_confidence_keywords, get_hedge_words

__all__ = [
    "ClaimsExtractor",
    "Claim",
    "get_all_patterns",
    "get_high_confidence_keywords",
    "get_hedge_words"
]
