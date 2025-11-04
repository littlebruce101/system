"""Bias detection module for analyzing text neutrality and objectivity."""

from .detector import BiasDetector, BiasDetectionResult
from .lexicons import (
    get_all_bias_lexicons,
    get_bias_weights,
    get_neutrality_bonus
)

__all__ = [
    "BiasDetector",
    "BiasDetectionResult",
    "get_all_bias_lexicons",
    "get_bias_weights",
    "get_neutrality_bonus"
]
