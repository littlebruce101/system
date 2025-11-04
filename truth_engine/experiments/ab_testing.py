"""
A/B Testing Framework - Optimizes truth scoring through controlled experiments.
Enables testing different scoring weights, algorithms, and parameters.
"""

import logging
import hashlib
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import random

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Experiment lifecycle status."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Variant:
    """Represents an experiment variant."""
    name: str
    description: str
    config: Dict
    traffic_allocation: float  # 0.0 to 1.0

    def __post_init__(self):
        if not 0.0 <= self.traffic_allocation <= 1.0:
            raise ValueError("traffic_allocation must be between 0.0 and 1.0")


@dataclass
class ExperimentResult:
    """Results for a single variant."""
    variant_name: str
    sample_size: int
    metric_values: List[float] = field(default_factory=list)
    mean: float = 0.0
    median: float = 0.0
    stddev: float = 0.0
    confidence_interval: Tuple[float, float] = (0.0, 0.0)

    def calculate_statistics(self):
        """Calculate statistical measures."""
        if not self.metric_values:
            return

        self.sample_size = len(self.metric_values)
        self.mean = float(np.mean(self.metric_values))
        self.median = float(np.median(self.metric_values))
        self.stddev = float(np.std(self.metric_values))

        # 95% confidence interval
        if self.sample_size > 1:
            stderr = stats.sem(self.metric_values)
            ci = stats.t.interval(
                0.95,
                self.sample_size - 1,
                loc=self.mean,
                scale=stderr
            )
            self.confidence_interval = (float(ci[0]), float(ci[1]))

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "variant_name": self.variant_name,
            "sample_size": self.sample_size,
            "mean": self.mean,
            "median": self.median,
            "stddev": self.stddev,
            "confidence_interval": {
                "lower": self.confidence_interval[0],
                "upper": self.confidence_interval[1]
            }
        }


@dataclass
class Experiment:
    """
    Represents an A/B test experiment.

    Features:
    - Multiple variant support
    - Configurable traffic allocation
    - Statistical significance testing
    - Early stopping detection
    """

    id: str
    name: str
    description: str
    hypothesis: str
    status: ExperimentStatus
    variants: List[Variant]
    primary_metric: str
    secondary_metrics: List[str]

    # Statistical parameters
    minimum_sample_size: int = 1000
    confidence_level: float = 0.95
    minimum_detectable_effect: float = 0.05  # 5%

    # Results
    results: Dict[str, ExperimentResult] = field(default_factory=dict)
    winner: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    def __post_init__(self):
        # Validate traffic allocation sums to 1.0
        total_traffic = sum(v.traffic_allocation for v in self.variants)
        if abs(total_traffic - 1.0) > 0.01:
            raise ValueError(f"Variant traffic allocations must sum to 1.0, got {total_traffic}")

        # Initialize results for each variant
        for variant in self.variants:
            self.results[variant.name] = ExperimentResult(
                variant_name=variant.name,
                sample_size=0
            )

    def assign_variant(self, user_id: str) -> Variant:
        """
        Assign a variant to a user using consistent hashing.

        Args:
            user_id: User identifier

        Returns:
            Assigned Variant
        """
        # Use hash for consistent assignment
        hash_value = int(hashlib.sha256(
            f"{self.id}:{user_id}".encode()
        ).hexdigest(), 16)

        # Map to [0, 1]
        normalized = (hash_value % 10000) / 10000.0

        # Assign based on traffic allocation
        cumulative = 0.0
        for variant in self.variants:
            cumulative += variant.traffic_allocation
            if normalized < cumulative:
                return variant

        # Fallback (shouldn't happen if allocations sum to 1.0)
        return self.variants[0]

    def record_metric(self, variant_name: str, metric_value: float):
        """
        Record a metric observation for a variant.

        Args:
            variant_name: Name of the variant
            metric_value: Metric value to record
        """
        if variant_name not in self.results:
            logger.warning(f"Unknown variant: {variant_name}")
            return

        self.results[variant_name].metric_values.append(metric_value)
        self.results[variant_name].calculate_statistics()

    def analyze_results(self) -> Dict:
        """
        Analyze experiment results and determine statistical significance.

        Returns:
            Dictionary with analysis results
        """
        # Ensure we have enough data
        min_samples_met = all(
            r.sample_size >= self.minimum_sample_size
            for r in self.results.values()
        )

        if not min_samples_met:
            return {
                "ready_for_analysis": False,
                "reason": "Minimum sample size not met for all variants",
                "sample_sizes": {
                    name: result.sample_size
                    for name, result in self.results.items()
                }
            }

        # Recalculate statistics
        for result in self.results.values():
            result.calculate_statistics()

        # Find control (first variant) and treatment variants
        control = self.results[self.variants[0].name]
        treatments = [
            self.results[v.name]
            for v in self.variants[1:]
        ]

        # Perform t-tests
        comparisons = []
        for treatment in treatments:
            # Two-sample t-test
            t_stat, p_value = stats.ttest_ind(
                control.metric_values,
                treatment.metric_values
            )

            # Effect size (Cohen's d)
            pooled_std = np.sqrt(
                (control.stddev ** 2 + treatment.stddev ** 2) / 2
            )
            effect_size = (treatment.mean - control.mean) / pooled_std if pooled_std > 0 else 0

            # Relative improvement
            relative_improvement = (
                (treatment.mean - control.mean) / control.mean
                if control.mean != 0 else 0
            )

            is_significant = p_value < (1 - self.confidence_level)
            meets_mde = abs(relative_improvement) >= self.minimum_detectable_effect

            comparisons.append({
                "variant": treatment.variant_name,
                "control_mean": control.mean,
                "treatment_mean": treatment.mean,
                "difference": treatment.mean - control.mean,
                "relative_improvement": relative_improvement,
                "p_value": float(p_value),
                "t_statistic": float(t_stat),
                "effect_size": float(effect_size),
                "is_significant": is_significant,
                "meets_minimum_detectable_effect": meets_mde,
                "winner": is_significant and meets_mde and treatment.mean > control.mean
            })

        # Determine overall winner
        significant_improvements = [
            c for c in comparisons
            if c["is_significant"] and c["meets_minimum_detectable_effect"] and c["winner"]
        ]

        if significant_improvements:
            # Pick variant with highest mean
            winner_comparison = max(significant_improvements, key=lambda x: x["treatment_mean"])
            self.winner = winner_comparison["variant"]
        else:
            self.winner = self.variants[0].name  # Control wins by default

        return {
            "ready_for_analysis": True,
            "winner": self.winner,
            "confidence_level": self.confidence_level,
            "minimum_detectable_effect": self.minimum_detectable_effect,
            "comparisons": comparisons,
            "variant_statistics": {
                name: result.to_dict()
                for name, result in self.results.items()
            }
        }

    def should_stop_early(self) -> Tuple[bool, str]:
        """
        Check if experiment should stop early.

        Returns:
            Tuple of (should_stop, reason)
        """
        # Check if minimum samples met
        min_samples = min(r.sample_size for r in self.results.values())
        if min_samples < self.minimum_sample_size:
            return False, ""

        # Run analysis
        analysis = self.analyze_results()

        if not analysis["ready_for_analysis"]:
            return False, ""

        # Check for clear winner
        significant_comparisons = [
            c for c in analysis["comparisons"]
            if c["is_significant"] and c["meets_minimum_detectable_effect"]
        ]

        if len(significant_comparisons) > 0:
            # Check if winner is clear (p-value very low)
            for comp in significant_comparisons:
                if comp["p_value"] < 0.01 and abs(comp["relative_improvement"]) > self.minimum_detectable_effect * 2:
                    return True, f"Clear winner detected: {comp['variant']}"

        return False, ""

    def get_status_summary(self) -> Dict:
        """Get experiment status summary."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "variants": [
                {
                    "name": v.name,
                    "traffic": v.traffic_allocation,
                    "sample_size": self.results[v.name].sample_size
                }
                for v in self.variants
            ],
            "total_samples": sum(r.sample_size for r in self.results.values()),
            "minimum_sample_size": self.minimum_sample_size,
            "progress": min(1.0, min(r.sample_size for r in self.results.values()) / self.minimum_sample_size),
            "winner": self.winner,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None
        }


class ExperimentManager:
    """
    Manages multiple A/B test experiments.

    Features:
    - Experiment lifecycle management
    - Variant assignment
    - Metric recording
    - Result analysis
    """

    def __init__(self):
        """Initialize experiment manager."""
        self.experiments: Dict[str, Experiment] = {}
        logger.info("ExperimentManager initialized")

    def create_experiment(
        self,
        name: str,
        description: str,
        hypothesis: str,
        variants: List[Variant],
        primary_metric: str,
        secondary_metrics: Optional[List[str]] = None,
        minimum_sample_size: int = 1000,
        confidence_level: float = 0.95,
        minimum_detectable_effect: float = 0.05
    ) -> Experiment:
        """
        Create a new experiment.

        Args:
            name: Experiment name
            description: Description
            hypothesis: Hypothesis being tested
            variants: List of variants
            primary_metric: Primary success metric
            secondary_metrics: Optional secondary metrics
            minimum_sample_size: Minimum samples per variant
            confidence_level: Statistical confidence level
            minimum_detectable_effect: Minimum effect size to detect

        Returns:
            Created Experiment
        """
        experiment = Experiment(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            hypothesis=hypothesis,
            status=ExperimentStatus.DRAFT,
            variants=variants,
            primary_metric=primary_metric,
            secondary_metrics=secondary_metrics or [],
            minimum_sample_size=minimum_sample_size,
            confidence_level=confidence_level,
            minimum_detectable_effect=minimum_detectable_effect
        )

        self.experiments[experiment.id] = experiment
        logger.info(f"Created experiment: {name} (id={experiment.id})")

        return experiment

    def start_experiment(self, experiment_id: str):
        """Start an experiment."""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.utcnow()

        logger.info(f"Started experiment: {experiment.name}")

    def stop_experiment(self, experiment_id: str, reason: str = "Manual stop"):
        """Stop an experiment."""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.COMPLETED
        experiment.ended_at = datetime.utcnow()

        # Run final analysis
        analysis = experiment.analyze_results()

        logger.info(f"Stopped experiment: {experiment.name}, Winner: {analysis.get('winner')}, Reason: {reason}")

        return analysis

    def get_variant_for_user(self, experiment_id: str, user_id: str) -> Optional[Variant]:
        """Get variant assignment for a user."""
        if experiment_id not in self.experiments:
            return None

        experiment = self.experiments[experiment_id]

        if experiment.status != ExperimentStatus.RUNNING:
            return None

        return experiment.assign_variant(user_id)

    def record_metric(
        self,
        experiment_id: str,
        variant_name: str,
        metric_value: float
    ):
        """Record a metric for an experiment variant."""
        if experiment_id not in self.experiments:
            logger.warning(f"Experiment {experiment_id} not found")
            return

        experiment = self.experiments[experiment_id]
        experiment.record_metric(variant_name, metric_value)

        # Check for early stopping
        should_stop, reason = experiment.should_stop_early()
        if should_stop:
            logger.info(f"Early stopping triggered for experiment {experiment.name}: {reason}")
            self.stop_experiment(experiment_id, reason)

    def get_experiment_status(self, experiment_id: str) -> Optional[Dict]:
        """Get experiment status."""
        if experiment_id not in self.experiments:
            return None

        return self.experiments[experiment_id].get_status_summary()

    def list_experiments(self, status: Optional[ExperimentStatus] = None) -> List[Dict]:
        """List all experiments, optionally filtered by status."""
        experiments = list(self.experiments.values())

        if status:
            experiments = [e for e in experiments if e.status == status]

        return [e.get_status_summary() for e in experiments]


def main():
    """Example usage of A/B Testing Framework."""
    manager = ExperimentManager()

    # Create experiment: Testing different truth score weights
    print("Creating A/B test for truth score weights...\n")

    variants = [
        Variant(
            name="control",
            description="Current weights (verification=0.5, bias=0.3, claim=0.2)",
            config={
                "weights": {
                    "verification": 0.5,
                    "bias": 0.3,
                    "claim_quality": 0.2
                }
            },
            traffic_allocation=0.5
        ),
        Variant(
            name="variant_high_verification",
            description="Higher verification weight (verification=0.6, bias=0.25, claim=0.15)",
            config={
                "weights": {
                    "verification": 0.6,
                    "bias": 0.25,
                    "claim_quality": 0.15
                }
            },
            traffic_allocation=0.5
        )
    ]

    experiment = manager.create_experiment(
        name="Truth Score Weights Optimization",
        description="Testing higher verification weight for better accuracy",
        hypothesis="Increasing verification weight will improve user satisfaction",
        variants=variants,
        primary_metric="user_satisfaction_score",
        secondary_metrics=["truth_score_accuracy", "processing_time"],
        minimum_sample_size=500
    )

    manager.start_experiment(experiment.id)

    # Simulate recording metrics
    print("Simulating experiment with user traffic...\n")

    for i in range(1200):
        user_id = f"user_{i}"
        variant = manager.get_variant_for_user(experiment.id, user_id)

        if variant:
            # Simulate metric (variant_high_verification performs slightly better)
            if variant.name == "control":
                metric = np.random.normal(0.72, 0.1)
            else:
                metric = np.random.normal(0.76, 0.1)

            metric = max(0.0, min(1.0, metric))  # Clamp to [0, 1]

            manager.record_metric(experiment.id, variant.name, metric)

    # Get results
    print(f"{'='*70}")
    print("Experiment Results")
    print(f"{'='*70}\n")

    analysis = experiment.analyze_results()

    print(f"Winner: {analysis['winner']}\n")

    print("Variant Statistics:")
    for name, stats in analysis['variant_statistics'].items():
        print(f"\n{name}:")
        print(f"  Sample Size: {stats['sample_size']}")
        print(f"  Mean: {stats['mean']:.4f}")
        print(f"  Std Dev: {stats['stddev']:.4f}")
        print(f"  95% CI: [{stats['confidence_interval']['lower']:.4f}, {stats['confidence_interval']['upper']:.4f}]")

    print(f"\n{'='*70}")
    print("Statistical Comparisons:")
    print(f"{'='*70}\n")

    for comp in analysis['comparisons']:
        print(f"Variant: {comp['variant']}")
        print(f"  Improvement: {comp['relative_improvement']*100:.2f}%")
        print(f"  P-value: {comp['p_value']:.6f}")
        print(f"  Statistically Significant: {'Yes' if comp['is_significant'] else 'No'}")
        print(f"  Winner: {'Yes' if comp['winner'] else 'No'}")
        print()


if __name__ == "__main__":
    main()
