"""
Knowledge Base Verification - Checks claims against trusted knowledge sources.
Integrates with Wikidata, fact-checking APIs, and other authoritative sources.
"""

import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

import requests
from SPARQLWrapper import SPARQLWrapper, JSON

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Status of claim verification."""
    VERIFIED = "verified"
    CONTRADICTED = "contradicted"
    UNSUPPORTED = "unsupported"
    UNCERTAIN = "uncertain"
    ERROR = "error"


@dataclass
class VerificationResult:
    """Result of knowledge base verification."""
    claim_text: str
    status: VerificationStatus
    confidence: float
    sources: List[Dict[str, str]]
    evidence: List[str]
    contradictions: List[str]
    metadata: Dict
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "claim_text": self.claim_text,
            "status": self.status.value,
            "confidence": self.confidence,
            "sources": self.sources,
            "evidence": self.evidence,
            "contradictions": self.contradictions,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class KnowledgeBaseVerifier:
    """
    Verifies claims against authoritative knowledge bases.

    Features:
    - Wikidata SPARQL queries
    - Fact-checking API integration
    - Source reliability scoring
    - Evidence aggregation
    - Contradiction detection
    """

    def __init__(
        self,
        cache_ttl: int = 3600,
        wikidata_endpoint: str = "https://query.wikidata.org/sparql",
        enable_cache: bool = True
    ):
        """
        Initialize the knowledge base verifier.

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            wikidata_endpoint: Wikidata SPARQL endpoint URL
            enable_cache: Enable result caching
        """
        self.cache_ttl = cache_ttl
        self.wikidata_endpoint = wikidata_endpoint
        self.enable_cache = enable_cache
        self._cache = {}  # Simple in-memory cache
        self._cache_timestamps = {}

        # Initialize SPARQL wrapper
        self.sparql = SPARQLWrapper(wikidata_endpoint)
        self.sparql.setReturnFormat(JSON)

        # Fact-checking API endpoints
        self.factcheck_apis = {
            "google_factcheck": "https://factchecktools.googleapis.com/v1alpha1/claims:search",
            "fullfact": "https://fullfact.org/api/v1/search/"
        }

    def verify_claim(
        self,
        claim_text: str,
        entities: List[Dict[str, str]],
        claim_type: str
    ) -> VerificationResult:
        """
        Verify a claim against knowledge bases.

        Args:
            claim_text: The claim to verify
            entities: Named entities extracted from the claim
            claim_type: Type of claim (statistical, causal, etc.)

        Returns:
            VerificationResult object
        """
        # Check cache first
        cache_key = self._get_cache_key(claim_text)
        if self.enable_cache and cache_key in self._cache:
            if self._is_cache_valid(cache_key):
                logger.debug(f"Cache hit for claim: {claim_text[:50]}...")
                return self._cache[cache_key]

        logger.info(f"Verifying claim: {claim_text[:100]}...")

        # Collect evidence from multiple sources
        evidence = []
        contradictions = []
        sources = []

        # 1. Query Wikidata for relevant facts
        try:
            wikidata_results = self._query_wikidata(entities, claim_text, claim_type)
            if wikidata_results:
                evidence.extend(wikidata_results.get("evidence", []))
                contradictions.extend(wikidata_results.get("contradictions", []))
                sources.append({
                    "name": "Wikidata",
                    "url": "https://www.wikidata.org",
                    "reliability": 0.85
                })
        except Exception as e:
            logger.error(f"Wikidata query failed: {e}")

        # 2. Check fact-checking databases
        try:
            factcheck_results = self._query_factcheck_apis(claim_text)
            if factcheck_results:
                evidence.extend(factcheck_results.get("evidence", []))
                contradictions.extend(factcheck_results.get("contradictions", []))
                sources.extend(factcheck_results.get("sources", []))
        except Exception as e:
            logger.error(f"Fact-check API query failed: {e}")

        # 3. Determine verification status and confidence
        status, confidence = self._determine_status(evidence, contradictions)

        # Create result
        result = VerificationResult(
            claim_text=claim_text,
            status=status,
            confidence=confidence,
            sources=sources,
            evidence=evidence,
            contradictions=contradictions,
            metadata={
                "claim_type": claim_type,
                "entities_checked": len(entities),
                "sources_consulted": len(sources)
            }
        )

        # Cache the result
        if self.enable_cache:
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.utcnow()

        return result

    def _query_wikidata(
        self,
        entities: List[Dict[str, str]],
        claim_text: str,
        claim_type: str
    ) -> Optional[Dict]:
        """
        Query Wikidata for information about entities in the claim.

        Args:
            entities: Named entities from the claim
            claim_text: Full claim text
            claim_type: Type of claim

        Returns:
            Dictionary with evidence and contradictions
        """
        if not entities:
            return None

        results = {
            "evidence": [],
            "contradictions": []
        }

        # Extract entity labels for querying
        entity_labels = [e["text"] for e in entities if e.get("label") in ["PERSON", "ORG", "GPE", "PRODUCT"]]

        if not entity_labels:
            return None

        # Build SPARQL query for each entity
        for entity_label in entity_labels[:3]:  # Limit to first 3 entities
            try:
                query = f"""
                SELECT DISTINCT ?item ?itemLabel ?property ?propertyLabel ?value ?valueLabel WHERE {{
                  ?item ?label "{entity_label}"@en.
                  ?item ?property ?value.
                  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
                }}
                LIMIT 10
                """

                self.sparql.setQuery(query)
                wikidata_response = self.sparql.query().convert()

                # Process results
                for binding in wikidata_response.get("results", {}).get("bindings", []):
                    property_label = binding.get("propertyLabel", {}).get("value", "")
                    value_label = binding.get("valueLabel", {}).get("value", "")

                    if property_label and value_label:
                        evidence_text = f"{entity_label} {property_label}: {value_label}"
                        results["evidence"].append(evidence_text)

            except Exception as e:
                logger.warning(f"SPARQL query failed for entity '{entity_label}': {e}")
                continue

        return results if results["evidence"] or results["contradictions"] else None

    def _query_factcheck_apis(self, claim_text: str) -> Optional[Dict]:
        """
        Query fact-checking APIs for existing fact-checks.

        Args:
            claim_text: Claim to search for

        Returns:
            Dictionary with evidence, contradictions, and sources
        """
        results = {
            "evidence": [],
            "contradictions": [],
            "sources": []
        }

        # Note: These require API keys in production
        # For now, this is a structure showing how it would work

        # Example: Google Fact Check Tools API
        # Requires API key: api_key = os.getenv("GOOGLE_FACTCHECK_API_KEY")
        # params = {
        #     "query": claim_text,
        #     "key": api_key
        # }
        # response = requests.get(self.factcheck_apis["google_factcheck"], params=params)

        # For demonstration, return placeholder structure
        logger.info("Fact-check API integration ready (requires API keys in production)")

        return results if results["evidence"] or results["contradictions"] else None

    def _determine_status(
        self,
        evidence: List[str],
        contradictions: List[str]
    ) -> Tuple[VerificationStatus, float]:
        """
        Determine verification status based on evidence and contradictions.

        Args:
            evidence: Supporting evidence found
            contradictions: Contradicting evidence found

        Returns:
            Tuple of (VerificationStatus, confidence_score)
        """
        evidence_count = len(evidence)
        contradiction_count = len(contradictions)

        # No evidence found
        if evidence_count == 0 and contradiction_count == 0:
            return VerificationStatus.UNSUPPORTED, 0.0

        # Strong contradictions
        if contradiction_count > evidence_count:
            confidence = min(0.9, contradiction_count * 0.15)
            return VerificationStatus.CONTRADICTED, confidence

        # Mixed evidence
        if contradiction_count > 0 and evidence_count > 0:
            # Calculate ratio
            ratio = evidence_count / (evidence_count + contradiction_count)
            if ratio > 0.7:
                return VerificationStatus.VERIFIED, ratio * 0.8
            else:
                return VerificationStatus.UNCERTAIN, 0.4

        # Strong supporting evidence
        if evidence_count >= 3:
            confidence = min(0.95, 0.6 + evidence_count * 0.1)
            return VerificationStatus.VERIFIED, confidence

        # Some supporting evidence
        if evidence_count > 0:
            confidence = 0.4 + evidence_count * 0.15
            return VerificationStatus.VERIFIED, min(confidence, 0.85)

        return VerificationStatus.UNCERTAIN, 0.3

    def _get_cache_key(self, claim_text: str) -> str:
        """Generate cache key from claim text."""
        return hashlib.sha256(claim_text.encode()).hexdigest()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid."""
        if cache_key not in self._cache_timestamps:
            return False

        timestamp = self._cache_timestamps[cache_key]
        age = (datetime.utcnow() - timestamp).total_seconds()
        return age < self.cache_ttl

    def clear_cache(self):
        """Clear the verification cache."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Verification cache cleared")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "ttl_seconds": self.cache_ttl,
            "oldest_entry": min(self._cache_timestamps.values()) if self._cache_timestamps else None
        }


def main():
    """Example usage of Knowledge Base Verifier."""
    verifier = KnowledgeBaseVerifier()

    # Example claims
    claims = [
        {
            "text": "Python was created by Guido van Rossum",
            "entities": [
                {"text": "Python", "label": "PRODUCT"},
                {"text": "Guido van Rossum", "label": "PERSON"}
            ],
            "type": "definitional"
        },
        {
            "text": "The Earth is flat",
            "entities": [{"text": "Earth", "label": "GPE"}],
            "type": "definitional"
        }
    ]

    for claim in claims:
        result = verifier.verify_claim(
            claim["text"],
            claim["entities"],
            claim["type"]
        )

        print(f"\nClaim: {claim['text']}")
        print(f"Status: {result.status.value}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Evidence: {len(result.evidence)} items")
        print(f"Contradictions: {len(result.contradictions)} items")
        print(f"Sources: {[s['name'] for s in result.sources]}")


if __name__ == "__main__":
    main()
