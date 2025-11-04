"""
Real-time Monitoring System - Tracks truth scores and system health.
Provides metrics aggregation, alerting, and performance monitoring.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import deque
import statistics

from prometheus_client import Counter, Histogram, Gauge, Summary
import numpy as np

logger = logging.getLogger(__name__)


# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# Truth score metrics
truth_score_histogram = Histogram(
    'truth_score_value',
    'Distribution of truth scores',
    buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 1.0]
)

truth_score_gauge = Gauge(
    'truth_score_current_avg',
    'Current average truth score (last hour)'
)

# Component score metrics
verification_score_histogram = Histogram(
    'verification_score',
    'Distribution of verification scores',
    buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
)

bias_score_histogram = Histogram(
    'bias_score',
    'Distribution of bias scores',
    buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
)

# Volume metrics
documents_scored_counter = Counter(
    'documents_scored_total',
    'Total number of documents scored'
)

claims_extracted_counter = Counter(
    'claims_extracted_total',
    'Total number of claims extracted'
)

claims_verified_counter = Counter(
    'claims_verified_total',
    'Total number of claims verified',
    ['status']  # verified, contradicted, unsupported, uncertain
)

# Performance metrics
scoring_duration = Histogram(
    'scoring_duration_seconds',
    'Time taken to score a document',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

verification_duration = Histogram(
    'verification_duration_seconds',
    'Time taken to verify a claim'
)

# Error metrics
scoring_errors_counter = Counter(
    'scoring_errors_total',
    'Total number of scoring errors',
    ['error_type']
)


# ============================================================================
# METRICS COLLECTOR
# ============================================================================

@dataclass
class MetricsSnapshot:
    """Snapshot of metrics at a point in time."""
    timestamp: datetime
    avg_truth_score: float
    median_truth_score: float
    min_truth_score: float
    max_truth_score: float
    stddev_truth_score: float
    total_documents: int
    total_claims: int
    total_verifications: int
    verification_rate: float
    contradiction_rate: float
    avg_processing_time_ms: float


class MetricsCollector:
    """
    Collects and aggregates metrics for monitoring.

    Features:
    - Real-time metric aggregation
    - Sliding window analytics
    - Anomaly detection
    - Alert triggering
    """

    def __init__(
        self,
        window_size: int = 1000,
        aggregation_interval_seconds: int = 60
    ):
        """
        Initialize metrics collector.

        Args:
            window_size: Number of recent scores to keep in memory
            aggregation_interval_seconds: How often to aggregate metrics
        """
        self.window_size = window_size
        self.aggregation_interval = aggregation_interval_seconds

        # Sliding windows for real-time metrics
        self.truth_scores = deque(maxlen=window_size)
        self.verification_scores = deque(maxlen=window_size)
        self.bias_scores = deque(maxlen=window_size)
        self.processing_times = deque(maxlen=window_size)

        # Counters
        self.total_documents = 0
        self.total_claims = 0
        self.total_verifications = 0
        self.total_verified = 0
        self.total_contradicted = 0

        # Last aggregation time
        self.last_aggregation = datetime.utcnow()

        logger.info(f"MetricsCollector initialized (window_size={window_size})")

    def record_truth_score(
        self,
        truth_score: float,
        verification_score: float,
        bias_score: float,
        claims_count: int,
        verifications_count: int,
        verified_count: int,
        contradicted_count: int,
        processing_time_ms: float
    ):
        """
        Record a complete truth scoring event.

        Args:
            truth_score: Final truth score
            verification_score: Verification component score
            bias_score: Bias component score
            claims_count: Number of claims extracted
            verifications_count: Number of verifications performed
            verified_count: Number of claims verified
            contradicted_count: Number of claims contradicted
            processing_time_ms: Processing time in milliseconds
        """
        # Update sliding windows
        self.truth_scores.append(truth_score)
        self.verification_scores.append(verification_score)
        self.bias_scores.append(bias_score)
        self.processing_times.append(processing_time_ms)

        # Update counters
        self.total_documents += 1
        self.total_claims += claims_count
        self.total_verifications += verifications_count
        self.total_verified += verified_count
        self.total_contradicted += contradicted_count

        # Update Prometheus metrics
        truth_score_histogram.observe(truth_score)
        verification_score_histogram.observe(verification_score)
        bias_score_histogram.observe(bias_score)
        documents_scored_counter.inc()
        claims_extracted_counter.inc(claims_count)

        if verified_count > 0:
            claims_verified_counter.labels(status='verified').inc(verified_count)
        if contradicted_count > 0:
            claims_verified_counter.labels(status='contradicted').inc(contradicted_count)

        scoring_duration.observe(processing_time_ms / 1000.0)

        # Update current average gauge
        if self.truth_scores:
            truth_score_gauge.set(statistics.mean(self.truth_scores))

        logger.debug(f"Recorded truth score: {truth_score:.2f}")

    def get_current_metrics(self) -> MetricsSnapshot:
        """
        Get current metrics snapshot.

        Returns:
            MetricsSnapshot object
        """
        if not self.truth_scores:
            return MetricsSnapshot(
                timestamp=datetime.utcnow(),
                avg_truth_score=0.0,
                median_truth_score=0.0,
                min_truth_score=0.0,
                max_truth_score=0.0,
                stddev_truth_score=0.0,
                total_documents=0,
                total_claims=0,
                total_verifications=0,
                verification_rate=0.0,
                contradiction_rate=0.0,
                avg_processing_time_ms=0.0
            )

        scores = list(self.truth_scores)

        # Calculate statistics
        avg_score = statistics.mean(scores)
        median_score = statistics.median(scores)
        min_score = min(scores)
        max_score = max(scores)
        stddev_score = statistics.stdev(scores) if len(scores) > 1 else 0.0

        # Rates
        verification_rate = (
            self.total_verified / self.total_verifications
            if self.total_verifications > 0 else 0.0
        )
        contradiction_rate = (
            self.total_contradicted / self.total_verifications
            if self.total_verifications > 0 else 0.0
        )

        # Processing time
        avg_processing = (
            statistics.mean(self.processing_times)
            if self.processing_times else 0.0
        )

        return MetricsSnapshot(
            timestamp=datetime.utcnow(),
            avg_truth_score=avg_score,
            median_truth_score=median_score,
            min_truth_score=min_score,
            max_truth_score=max_score,
            stddev_truth_score=stddev_score,
            total_documents=self.total_documents,
            total_claims=self.total_claims,
            total_verifications=self.total_verifications,
            verification_rate=verification_rate,
            contradiction_rate=contradiction_rate,
            avg_processing_time_ms=avg_processing
        )

    def detect_score_degradation(
        self,
        threshold: float = 0.1,
        lookback_window: int = 100
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Detect if truth scores are degrading.

        Compares recent scores to historical baseline.

        Args:
            threshold: Minimum degradation to trigger alert (e.g., 0.1 = 10% drop)
            lookback_window: Number of recent scores to compare

        Returns:
            Tuple of (is_degraded, details_dict)
        """
        if len(self.truth_scores) < lookback_window * 2:
            return False, None

        # Split into recent and baseline
        all_scores = list(self.truth_scores)
        recent_scores = all_scores[-lookback_window:]
        baseline_scores = all_scores[-lookback_window*2:-lookback_window]

        recent_avg = statistics.mean(recent_scores)
        baseline_avg = statistics.mean(baseline_scores)

        degradation = baseline_avg - recent_avg

        if degradation > threshold:
            details = {
                "baseline_avg": baseline_avg,
                "recent_avg": recent_avg,
                "degradation": degradation,
                "threshold": threshold,
                "samples": lookback_window
            }
            return True, details

        return False, None

    def detect_anomalies(
        self,
        z_score_threshold: float = 3.0
    ) -> List[Dict]:
        """
        Detect anomalous truth scores using z-score.

        Args:
            z_score_threshold: Number of standard deviations for anomaly

        Returns:
            List of anomaly details
        """
        if len(self.truth_scores) < 30:
            return []

        scores = np.array(list(self.truth_scores))
        mean = np.mean(scores)
        std = np.std(scores)

        if std == 0:
            return []

        # Calculate z-scores for recent scores (last 10)
        recent_scores = scores[-10:]
        z_scores = np.abs((recent_scores - mean) / std)

        anomalies = []
        for i, (score, z) in enumerate(zip(recent_scores, z_scores)):
            if z > z_score_threshold:
                anomalies.append({
                    "score": float(score),
                    "z_score": float(z),
                    "mean": float(mean),
                    "std": float(std),
                    "position": len(scores) - 10 + i
                })

        return anomalies

    def get_score_trend(self, window: int = 100) -> str:
        """
        Get trend direction for truth scores.

        Args:
            window: Number of recent scores to analyze

        Returns:
            'improving', 'declining', or 'stable'
        """
        if len(self.truth_scores) < window:
            return 'stable'

        scores = list(self.truth_scores)[-window:]

        # Calculate linear regression slope
        x = np.arange(len(scores))
        y = np.array(scores)

        if len(x) < 2:
            return 'stable'

        slope = np.polyfit(x, y, 1)[0]

        if slope > 0.001:
            return 'improving'
        elif slope < -0.001:
            return 'declining'
        else:
            return 'stable'

    def reset_counters(self):
        """Reset all counters (for testing or new period)."""
        self.total_documents = 0
        self.total_claims = 0
        self.total_verifications = 0
        self.total_verified = 0
        self.total_contradicted = 0
        logger.info("Metrics counters reset")


def main():
    """Example usage of MetricsCollector."""
    collector = MetricsCollector(window_size=100)

    # Simulate scoring events
    print("Simulating scoring events...\n")

    # Good scores
    for i in range(50):
        collector.record_truth_score(
            truth_score=0.75 + np.random.normal(0, 0.05),
            verification_score=0.8 + np.random.normal(0, 0.05),
            bias_score=0.7 + np.random.normal(0, 0.05),
            claims_count=np.random.randint(3, 10),
            verifications_count=np.random.randint(3, 10),
            verified_count=np.random.randint(2, 8),
            contradicted_count=np.random.randint(0, 2),
            processing_time_ms=np.random.uniform(500, 2000)
        )

    # Degrading scores
    for i in range(30):
        collector.record_truth_score(
            truth_score=0.55 + np.random.normal(0, 0.05),
            verification_score=0.6 + np.random.normal(0, 0.05),
            bias_score=0.5 + np.random.normal(0, 0.05),
            claims_count=np.random.randint(2, 8),
            verifications_count=np.random.randint(2, 8),
            verified_count=np.random.randint(1, 5),
            contradicted_count=np.random.randint(1, 4),
            processing_time_ms=np.random.uniform(700, 2500)
        )

    # Get metrics
    snapshot = collector.get_current_metrics()
    print("Current Metrics Snapshot:")
    print(f"  Average Truth Score: {snapshot.avg_truth_score:.3f}")
    print(f"  Median Truth Score: {snapshot.median_truth_score:.3f}")
    print(f"  Std Dev: {snapshot.stddev_truth_score:.3f}")
    print(f"  Documents Scored: {snapshot.total_documents}")
    print(f"  Verification Rate: {snapshot.verification_rate:.1%}")
    print(f"  Avg Processing Time: {snapshot.avg_processing_time_ms:.0f}ms\n")

    # Check for degradation
    is_degraded, details = collector.detect_score_degradation(threshold=0.1)
    if is_degraded:
        print("⚠️  SCORE DEGRADATION DETECTED!")
        print(f"  Baseline Average: {details['baseline_avg']:.3f}")
        print(f"  Recent Average: {details['recent_avg']:.3f}")
        print(f"  Degradation: {details['degradation']:.3f}\n")

    # Check for anomalies
    anomalies = collector.detect_anomalies()
    if anomalies:
        print(f"⚠️  {len(anomalies)} ANOMALIES DETECTED!")
        for anom in anomalies[:3]:
            print(f"  Score: {anom['score']:.3f} (z-score: {anom['z_score']:.2f})")
        print()

    # Check trend
    trend = collector.get_score_trend()
    print(f"Score Trend: {trend.upper()}")


if __name__ == "__main__":
    main()
