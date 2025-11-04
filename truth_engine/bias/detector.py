"""
Bias Detection Engine - Identifies and scores various types of bias in text.
Analyzes language patterns, emotional loading, logical fallacies, and neutrality.
"""

import re
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

from .lexicons import (
    get_all_bias_lexicons,
    get_bias_weights,
    get_neutrality_bonus,
    EMOTIONAL_LOADING,
    HEDGE_WORDS,
    HYPERBOLE_WORDS,
    AD_HOMINEM_PATTERNS,
    WEASEL_WORDS,
    LOADED_QUESTION_PATTERNS,
    FALSE_BALANCE_INDICATORS,
    CHERRY_PICKING_INDICATORS,
    NEUTRAL_LANGUAGE
)

logger = logging.getLogger(__name__)


@dataclass
class BiasDetectionResult:
    """Result of bias detection analysis."""
    text: str
    overall_bias_score: float  # 0 = highly biased, 1 = neutral
    neutrality_score: float  # 0 = no neutral indicators, 1 = highly neutral
    bias_types: Dict[str, Dict]
    neutrality_indicators: Dict[str, int]
    recommendations: List[str]
    metadata: Dict
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "text_preview": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "overall_bias_score": self.overall_bias_score,
            "neutrality_score": self.neutrality_score,
            "bias_types": self.bias_types,
            "neutrality_indicators": self.neutrality_indicators,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class BiasDetector:
    """
    Detects various types of bias in text.

    Bias types detected:
    1. Emotional loading (positive/negative/fear)
    2. Hedging (uncertainty language)
    3. Hyperbole (exaggeration)
    4. Ad hominem (personal attacks)
    5. Weasel words (vague language)
    6. Loaded questions (presuppositional)
    7. False balance (artificial equivalence)
    8. Cherry-picking (selective presentation)
    """

    def __init__(self):
        """Initialize the bias detector."""
        self.lexicons = get_all_bias_lexicons()
        self.bias_weights = get_bias_weights()
        self.neutrality_bonus = get_neutrality_bonus()

    def analyze(self, text: str, context: str = None) -> BiasDetectionResult:
        """
        Analyze text for various types of bias.

        Args:
            text: Text to analyze
            context: Optional context (e.g., "news", "opinion", "academic")

        Returns:
            BiasDetectionResult object
        """
        logger.info(f"Analyzing bias for text of length {len(text)}")

        text_lower = text.lower()
        word_count = len(text.split())

        # Detect each type of bias
        bias_types = {}

        # 1. Emotional loading
        bias_types["emotional_loading"] = self._detect_emotional_loading(text_lower)

        # 2. Hedge words
        bias_types["hedge_words"] = self._detect_hedge_words(text_lower)

        # 3. Hyperbole
        bias_types["hyperbole"] = self._detect_hyperbole(text_lower)

        # 4. Ad hominem
        bias_types["ad_hominem"] = self._detect_ad_hominem(text_lower)

        # 5. Weasel words
        bias_types["weasel_words"] = self._detect_weasel_words(text_lower)

        # 6. Loaded questions
        bias_types["loaded_questions"] = self._detect_loaded_questions(text)

        # 7. False balance
        bias_types["false_balance"] = self._detect_false_balance(text_lower)

        # 8. Cherry-picking
        bias_types["cherry_picking"] = self._detect_cherry_picking(text_lower)

        # Detect neutrality indicators
        neutrality_indicators = self._detect_neutrality(text_lower)

        # Calculate overall scores
        overall_bias_score = self._calculate_overall_bias_score(
            bias_types, word_count
        )
        neutrality_score = self._calculate_neutrality_score(
            neutrality_indicators, word_count
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(bias_types, neutrality_indicators)

        # Create result
        result = BiasDetectionResult(
            text=text,
            overall_bias_score=overall_bias_score,
            neutrality_score=neutrality_score,
            bias_types=bias_types,
            neutrality_indicators=neutrality_indicators,
            recommendations=recommendations,
            metadata={
                "word_count": word_count,
                "context": context,
                "bias_types_found": sum(1 for b in bias_types.values() if b["count"] > 0)
            }
        )

        return result

    def _detect_emotional_loading(self, text: str) -> Dict:
        """Detect emotionally loaded language."""
        results = {
            "count": 0,
            "instances": [],
            "breakdown": {"positive": 0, "negative": 0, "fear": 0},
            "severity": 0.0
        }

        for category, words in EMOTIONAL_LOADING.items():
            for word in words:
                if word in text:
                    count = text.count(word)
                    results["count"] += count
                    results["breakdown"][category] += count
                    results["instances"].append({"word": word, "category": category})

        # Calculate severity (0-1)
        if results["count"] > 0:
            results["severity"] = min(1.0, results["count"] * 0.15)

        return results

    def _detect_hedge_words(self, text: str) -> Dict:
        """Detect hedge words indicating uncertainty."""
        results = {
            "count": 0,
            "instances": [],
            "severity": 0.0
        }

        for hedge in HEDGE_WORDS:
            if hedge in text:
                count = text.count(hedge)
                results["count"] += count
                results["instances"].append(hedge)

        # Hedging is less severe than other biases
        if results["count"] > 0:
            results["severity"] = min(0.7, results["count"] * 0.08)

        return results

    def _detect_hyperbole(self, text: str) -> Dict:
        """Detect hyperbolic/exaggerated language."""
        results = {
            "count": 0,
            "instances": [],
            "severity": 0.0
        }

        for word in HYPERBOLE_WORDS:
            if word in text:
                count = text.count(word)
                results["count"] += count
                results["instances"].append(word)

        if results["count"] > 0:
            results["severity"] = min(1.0, results["count"] * 0.12)

        return results

    def _detect_ad_hominem(self, text: str) -> Dict:
        """Detect personal attacks and ad hominem fallacies."""
        results = {
            "count": 0,
            "instances": [],
            "severity": 0.0
        }

        for pattern in AD_HOMINEM_PATTERNS:
            # Use regex for pattern matching
            matches = re.findall(r'\b' + pattern + r'\b', text, re.IGNORECASE)
            if matches:
                results["count"] += len(matches)
                results["instances"].extend(matches)

        # Ad hominem is severe bias
        if results["count"] > 0:
            results["severity"] = min(1.0, results["count"] * 0.25)

        return results

    def _detect_weasel_words(self, text: str) -> Dict:
        """Detect weasel words (vague, unsubstantiated claims)."""
        results = {
            "count": 0,
            "instances": [],
            "severity": 0.0
        }

        for weasel in WEASEL_WORDS:
            if weasel in text:
                count = text.count(weasel)
                results["count"] += count
                results["instances"].append(weasel)

        if results["count"] > 0:
            results["severity"] = min(1.0, results["count"] * 0.1)

        return results

    def _detect_loaded_questions(self, text: str) -> Dict:
        """Detect loaded questions with presuppositions."""
        results = {
            "count": 0,
            "instances": [],
            "severity": 0.0
        }

        for pattern in LOADED_QUESTION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                results["count"] += len(matches)
                results["instances"].extend([str(m) for m in matches])

        if results["count"] > 0:
            results["severity"] = min(1.0, results["count"] * 0.2)

        return results

    def _detect_false_balance(self, text: str) -> Dict:
        """Detect false balance (artificial equivalence)."""
        results = {
            "count": 0,
            "instances": [],
            "severity": 0.0
        }

        for indicator in FALSE_BALANCE_INDICATORS:
            if indicator in text:
                count = text.count(indicator)
                results["count"] += count
                results["instances"].append(indicator)

        if results["count"] > 0:
            results["severity"] = min(0.8, results["count"] * 0.1)

        return results

    def _detect_cherry_picking(self, text: str) -> Dict:
        """Detect cherry-picking indicators."""
        results = {
            "count": 0,
            "instances": [],
            "severity": 0.0
        }

        for indicator in CHERRY_PICKING_INDICATORS:
            if indicator in text:
                count = text.count(indicator)
                results["count"] += count
                results["instances"].append(indicator)

        if results["count"] > 0:
            results["severity"] = min(0.9, results["count"] * 0.12)

        return results

    def _detect_neutrality(self, text: str) -> Dict[str, int]:
        """Detect neutral/objective language indicators."""
        indicators = defaultdict(int)

        for category, words in NEUTRAL_LANGUAGE.items():
            for word in words:
                if word in text:
                    indicators[category] += text.count(word)

        return dict(indicators)

    def _calculate_overall_bias_score(
        self,
        bias_types: Dict[str, Dict],
        word_count: int
    ) -> float:
        """
        Calculate overall bias score (0 = highly biased, 1 = neutral).

        Args:
            bias_types: Dictionary of detected bias types
            word_count: Total word count

        Returns:
            Bias score between 0 and 1
        """
        if word_count == 0:
            return 0.0

        # Start with neutral score
        score = 1.0

        # Apply penalties for each bias type
        for bias_type, data in bias_types.items():
            if bias_type in self.bias_weights:
                weight = self.bias_weights[bias_type]
                severity = data.get("severity", 0.0)
                penalty = weight * severity
                score -= penalty

        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))

    def _calculate_neutrality_score(
        self,
        neutrality_indicators: Dict[str, int],
        word_count: int
    ) -> float:
        """
        Calculate neutrality score based on objective language.

        Args:
            neutrality_indicators: Dictionary of neutrality indicators
            word_count: Total word count

        Returns:
            Neutrality score between 0 and 1
        """
        if word_count == 0:
            return 0.0

        score = 0.0

        for category, count in neutrality_indicators.items():
            if category in self.neutrality_bonus:
                bonus = self.neutrality_bonus[category]
                score += count * bonus

        # Normalize by word count (more neutral words in longer text)
        normalized_score = score / max(1, word_count / 100)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, normalized_score))

    def _generate_recommendations(
        self,
        bias_types: Dict[str, Dict],
        neutrality_indicators: Dict[str, int]
    ) -> List[str]:
        """
        Generate recommendations for improving neutrality.

        Args:
            bias_types: Detected bias types
            neutrality_indicators: Neutrality indicators

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check each bias type
        for bias_type, data in bias_types.items():
            if data["count"] > 0:
                severity = data.get("severity", 0)
                if severity > 0.5:
                    rec = self._get_recommendation_for_bias(bias_type, data)
                    if rec:
                        recommendations.append(rec)

        # Check neutrality
        if sum(neutrality_indicators.values()) < 3:
            recommendations.append(
                "Consider adding more objective language, data, or cited sources"
            )

        return recommendations

    def _get_recommendation_for_bias(self, bias_type: str, data: Dict) -> str:
        """Get specific recommendation for a bias type."""
        recommendations = {
            "emotional_loading": f"Reduce emotionally loaded language ({data['count']} instances found)",
            "hyperbole": f"Avoid exaggeration and absolute statements ({data['count']} instances found)",
            "ad_hominem": f"Remove personal attacks and focus on arguments ({data['count']} instances found)",
            "weasel_words": f"Replace vague claims with specific, verifiable statements ({data['count']} instances found)",
            "loaded_questions": f"Rephrase questions to remove presuppositions ({data['count']} instances found)",
            "false_balance": f"Ensure balanced representation is warranted by evidence ({data['count']} instances found)",
            "cherry_picking": f"Include comprehensive evidence, not just selected examples ({data['count']} instances found)"
        }

        return recommendations.get(bias_type, "")


def main():
    """Example usage of Bias Detector."""
    detector = BiasDetector()

    # Example texts with different bias levels
    texts = [
        {
            "text": "The study found that 75% of participants showed improvement. "
                    "According to the published research, the methodology was peer-reviewed.",
            "label": "Neutral/Objective"
        },
        {
            "text": "This absolutely incredible, game-changing innovation will completely "
                    "revolutionize everything! Everyone agrees it's perfect!",
            "label": "Highly Biased (Hyperbole + Emotional Loading)"
        },
        {
            "text": "Some experts believe this might possibly indicate a potential trend, "
                    "though it's unclear and debatable.",
            "label": "Hedging + Weasel Words"
        },
        {
            "text": "The corrupt politicians are idiots who have no idea what they're doing. "
                    "Why don't they just admit they're wrong?",
            "label": "Ad Hominem + Loaded Questions"
        }
    ]

    for example in texts:
        result = detector.analyze(example["text"])

        print(f"\n{'='*70}")
        print(f"Text: {example['text'][:60]}...")
        print(f"Label: {example['label']}")
        print(f"\nOverall Bias Score: {result.overall_bias_score:.2f} (1.0 = neutral)")
        print(f"Neutrality Score: {result.neutrality_score:.2f}")
        print(f"\nBias Types Found:")
        for bias_type, data in result.bias_types.items():
            if data["count"] > 0:
                print(f"  - {bias_type}: {data['count']} instances (severity: {data['severity']:.2f})")

        if result.recommendations:
            print(f"\nRecommendations:")
            for rec in result.recommendations:
                print(f"  - {rec}")


if __name__ == "__main__":
    main()
