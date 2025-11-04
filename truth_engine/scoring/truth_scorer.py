"""
Truth Scoring Engine - Combines all components into a final truth score.
Integrates claims extraction, verification, and bias detection.
"""

import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid

from ..claims import ClaimsExtractor, Claim
from ..verification import KnowledgeBaseVerifier, VerificationResult
from ..bias import BiasDetector, BiasDetectionResult

logger = logging.getLogger(__name__)


@dataclass
class TruthScoreResult:
    """Complete truth scoring result for a document."""
    document_id: str
    document_url: Optional[str]
    document_title: Optional[str]
    document_text: str

    # Final truth score
    truth_score: float

    # Component scores
    claim_extraction_score: float
    verification_score: float
    bias_score: float

    # Detailed results
    claims: List[Claim]
    verification_results: List[VerificationResult]
    bias_result: BiasDetectionResult

    # Metadata
    claims_analyzed: int
    claims_verified: int
    claims_contradicted: int
    weights: Dict[str, float]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "document_id": self.document_id,
            "document_url": self.document_url,
            "document_title": self.document_title,
            "document_text_preview": self.document_text[:200] + "..." if len(self.document_text) > 200 else self.document_text,

            # Scores
            "truth_score": float(self.truth_score),
            "claim_extraction_score": float(self.claim_extraction_score),
            "verification_score": float(self.verification_score),
            "bias_score": float(self.bias_score),

            # Details
            "claims_analyzed": self.claims_analyzed,
            "claims_verified": self.claims_verified,
            "claims_contradicted": self.claims_contradicted,

            # Component results
            "claims": [c.to_dict() for c in self.claims],
            "verification_results": [v.to_dict() for v in self.verification_results],
            "bias_result": self.bias_result.to_dict(),

            # Metadata
            "weights": self.weights,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    def get_summary(self) -> str:
        """Get a human-readable summary."""
        rating = self._get_rating()
        return f"""
Truth Score Summary
===================
Document: {self.document_title or 'Untitled'}
Overall Truth Score: {self.truth_score:.2f}/1.00 ({rating})

Component Scores:
  - Claim Quality: {self.claim_extraction_score:.2f}
  - Verification: {self.verification_score:.2f}
  - Bias/Neutrality: {self.bias_score:.2f}

Analysis:
  - {self.claims_analyzed} claims analyzed
  - {self.claims_verified} claims verified
  - {self.claims_contradicted} claims contradicted

Bias Assessment: {self.bias_result.overall_bias_score:.2f}/1.00 (higher is better)
Neutrality Score: {self.bias_result.neutrality_score:.2f}/1.00

{self._get_interpretation()}
        """.strip()

    def _get_rating(self) -> str:
        """Get text rating based on truth score."""
        if self.truth_score >= 0.85:
            return "Excellent"
        elif self.truth_score >= 0.70:
            return "Good"
        elif self.truth_score >= 0.55:
            return "Fair"
        elif self.truth_score >= 0.40:
            return "Poor"
        else:
            return "Very Poor"

    def _get_interpretation(self) -> str:
        """Get interpretation of the scores."""
        interpretations = []

        if self.verification_score < 0.5:
            interpretations.append("⚠️  Many claims could not be verified or were contradicted")

        if self.bias_score < 0.6:
            interpretations.append("⚠️  Significant bias detected in language")

        if self.claim_extraction_score < 0.5:
            interpretations.append("⚠️  Claims are vague or lack confidence")

        if len(interpretations) == 0:
            interpretations.append("✓ Document appears factual and neutral")

        return "\n".join(interpretations)


class TruthScorer:
    """
    Main truth scoring engine that orchestrates all components.

    Pipeline:
    1. Extract claims from text (ClaimsExtractor)
    2. Verify each claim (KnowledgeBaseVerifier)
    3. Analyze bias (BiasDetector)
    4. Combine scores into final truth score
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        min_claim_confidence: float = 0.3,
        enable_verification: bool = True,
        enable_bias_detection: bool = True
    ):
        """
        Initialize the truth scorer.

        Args:
            weights: Score weights for combining components
            min_claim_confidence: Minimum confidence for claim extraction
            enable_verification: Enable knowledge base verification
            enable_bias_detection: Enable bias detection
        """
        # Default weights
        self.weights = weights or {
            "verification": 0.5,
            "bias": 0.3,
            "claim_quality": 0.2
        }

        # Validate weights sum to 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total_weight}, normalizing to 1.0")
            self.weights = {k: v/total_weight for k, v in self.weights.items()}

        self.min_claim_confidence = min_claim_confidence
        self.enable_verification = enable_verification
        self.enable_bias_detection = enable_bias_detection

        # Initialize components
        self.claims_extractor = ClaimsExtractor()
        if enable_verification:
            self.knowledge_verifier = KnowledgeBaseVerifier()
        if enable_bias_detection:
            self.bias_detector = BiasDetector()

        logger.info(f"TruthScorer initialized with weights: {self.weights}")

    def score_document(
        self,
        text: str,
        document_url: Optional[str] = None,
        document_title: Optional[str] = None,
        context: Optional[str] = None
    ) -> TruthScoreResult:
        """
        Score a document for truthfulness.

        Args:
            text: Document text to analyze
            document_url: Optional URL of the document
            document_title: Optional title of the document
            context: Optional context (e.g., "news", "opinion")

        Returns:
            TruthScoreResult object
        """
        start_time = datetime.utcnow()
        document_id = str(uuid.uuid4())

        logger.info(f"Scoring document {document_id} (length: {len(text)} chars)")

        # Step 1: Extract claims
        logger.info("Step 1: Extracting claims...")
        claims = self.claims_extractor.extract_claims(
            text,
            min_confidence=self.min_claim_confidence
        )
        logger.info(f"Extracted {len(claims)} claims")

        # Step 2: Verify claims
        verification_results = []
        if self.enable_verification and claims:
            logger.info("Step 2: Verifying claims...")
            for claim in claims:
                try:
                    result = self.knowledge_verifier.verify_claim(
                        claim.text,
                        claim.entities,
                        claim.claim_type
                    )
                    verification_results.append(result)
                except Exception as e:
                    logger.error(f"Verification failed for claim '{claim.text[:50]}...': {e}")

            logger.info(f"Verified {len(verification_results)} claims")

        # Step 3: Detect bias
        bias_result = None
        if self.enable_bias_detection:
            logger.info("Step 3: Analyzing bias...")
            bias_result = self.bias_detector.analyze(text, context)
            logger.info(f"Bias analysis complete: score={bias_result.overall_bias_score:.2f}")

        # Step 4: Calculate component scores
        claim_extraction_score = self._calculate_claim_extraction_score(claims)
        verification_score = self._calculate_verification_score(verification_results)
        bias_score = bias_result.overall_bias_score if bias_result else 0.5

        # Step 5: Calculate final truth score
        truth_score = self._calculate_truth_score(
            claim_extraction_score,
            verification_score,
            bias_score
        )

        # Count verified/contradicted claims
        claims_verified = sum(
            1 for r in verification_results
            if hasattr(r, 'status') and str(r.status.value) == 'verified'
        )
        claims_contradicted = sum(
            1 for r in verification_results
            if hasattr(r, 'status') and str(r.status.value) == 'contradicted'
        )

        # Create result
        result = TruthScoreResult(
            document_id=document_id,
            document_url=document_url,
            document_title=document_title,
            document_text=text,
            truth_score=truth_score,
            claim_extraction_score=claim_extraction_score,
            verification_score=verification_score,
            bias_score=bias_score,
            claims=claims,
            verification_results=verification_results,
            bias_result=bias_result,
            claims_analyzed=len(claims),
            claims_verified=claims_verified,
            claims_contradicted=claims_contradicted,
            weights=self.weights
        )

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Scoring complete: truth_score={truth_score:.2f} (took {elapsed:.2f}s)")

        return result

    def _calculate_claim_extraction_score(self, claims: List[Claim]) -> float:
        """
        Calculate claim extraction quality score.

        Factors:
        - Number of claims (more is better, to a point)
        - Average claim confidence
        - Presence of high-confidence claims

        Args:
            claims: Extracted claims

        Returns:
            Score between 0 and 1
        """
        if not claims:
            return 0.3  # Neutral score for no claims

        # Average confidence
        avg_confidence = sum(c.confidence for c in claims) / len(claims)

        # Count high-confidence claims
        high_conf_claims = sum(1 for c in claims if c.confidence >= 0.7)
        high_conf_ratio = high_conf_claims / len(claims)

        # Claim density (penalize too few or too many claims)
        optimal_claim_count = 5
        if len(claims) < optimal_claim_count:
            density_score = len(claims) / optimal_claim_count
        else:
            density_score = min(1.0, optimal_claim_count / len(claims) * 0.8 + 0.2)

        # Combine factors
        score = (
            avg_confidence * 0.5 +
            high_conf_ratio * 0.3 +
            density_score * 0.2
        )

        return max(0.0, min(1.0, score))

    def _calculate_verification_score(self, verification_results: List[VerificationResult]) -> float:
        """
        Calculate verification quality score.

        Factors:
        - Verification rate (% of claims verified)
        - Verification confidence
        - Contradiction rate (penalty)

        Args:
            verification_results: Verification results

        Returns:
            Score between 0 and 1
        """
        if not verification_results:
            return 0.5  # Neutral score for no verifications

        # Count statuses
        verified = sum(1 for r in verification_results if str(r.status.value) == 'verified')
        contradicted = sum(1 for r in verification_results if str(r.status.value) == 'contradicted')
        total = len(verification_results)

        # Verification rate
        verification_rate = verified / total if total > 0 else 0

        # Average confidence of verified claims
        verified_claims = [r for r in verification_results if str(r.status.value) == 'verified']
        avg_verified_confidence = (
            sum(r.confidence for r in verified_claims) / len(verified_claims)
            if verified_claims else 0
        )

        # Contradiction penalty
        contradiction_rate = contradicted / total if total > 0 else 0
        contradiction_penalty = contradiction_rate * 0.5

        # Combine factors
        score = (
            verification_rate * 0.6 +
            avg_verified_confidence * 0.4 -
            contradiction_penalty
        )

        return max(0.0, min(1.0, score))

    def _calculate_truth_score(
        self,
        claim_extraction_score: float,
        verification_score: float,
        bias_score: float
    ) -> float:
        """
        Calculate final truth score as weighted combination of components.

        Args:
            claim_extraction_score: Claim quality score
            verification_score: Verification score
            bias_score: Bias/neutrality score

        Returns:
            Final truth score between 0 and 1
        """
        score = (
            verification_score * self.weights["verification"] +
            bias_score * self.weights["bias"] +
            claim_extraction_score * self.weights["claim_quality"]
        )

        return max(0.0, min(1.0, score))

    def update_weights(self, new_weights: Dict[str, float]):
        """
        Update scoring weights (for A/B testing).

        Args:
            new_weights: New weight configuration
        """
        # Validate weights sum to 1.0
        total_weight = sum(new_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            normalized = {k: v/total_weight for k, v in new_weights.items()}
            logger.info(f"Normalized weights from {new_weights} to {normalized}")
            self.weights = normalized
        else:
            self.weights = new_weights

        logger.info(f"Updated scoring weights to: {self.weights}")


def main():
    """Example usage of Truth Scorer."""
    scorer = TruthScorer()

    # Example documents
    documents = [
        {
            "text": """
            According to recent studies, 75% of users prefer faster search results.
            The new algorithm increased accuracy by 30% since January 2024.
            Python is a programming language created by Guido van Rossum.
            Research published in peer-reviewed journals shows clear evidence.
            """,
            "title": "Tech News Article (High Quality)",
            "context": "news"
        },
        {
            "text": """
            This absolutely revolutionary product will completely transform everything!
            Everyone agrees it's the best thing ever invented. The corrupt competitors
            are just jealous idiots who don't understand innovation. Why don't they
            just admit they're wrong? Some experts might possibly think it could work.
            """,
            "title": "Marketing Content (Low Quality)",
            "context": "commercial"
        }
    ]

    for doc in documents:
        print(f"\n{'='*80}")
        result = scorer.score_document(
            text=doc["text"],
            document_title=doc["title"],
            context=doc.get("context")
        )

        print(result.get_summary())


if __name__ == "__main__":
    main()
