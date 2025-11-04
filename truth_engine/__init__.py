"""
Truth-First Search Engine - A comprehensive system for evaluating factual accuracy.

Components:
- Claims Extraction: Identifies factual statements in text
- Knowledge Verification: Checks claims against trusted sources
- Bias Detection: Analyzes language neutrality and objectivity
- Truth Scoring: Combines components into final truth score
- Monitoring: Real-time metrics and alerting
- A/B Testing: Optimization framework for scoring parameters
"""

__version__ = "1.0.0"

from .claims import ClaimsExtractor, Claim
from .verification import KnowledgeBaseVerifier, VerificationResult, VerificationStatus
from .bias import BiasDetector, BiasDetectionResult
from .scoring import TruthScorer, TruthScoreResult
from .monitoring import MetricsCollector, AlertManager, Alert, AlertSeverity
from .experiments import ExperimentManager, Experiment, Variant

__all__ = [
    # Claims
    "ClaimsExtractor",
    "Claim",

    # Verification
    "KnowledgeBaseVerifier",
    "VerificationResult",
    "VerificationStatus",

    # Bias
    "BiasDetector",
    "BiasDetectionResult",

    # Scoring
    "TruthScorer",
    "TruthScoreResult",

    # Monitoring
    "MetricsCollector",
    "AlertManager",
    "Alert",
    "AlertSeverity",

    # Experiments
    "ExperimentManager",
    "Experiment",
    "Variant",
]
