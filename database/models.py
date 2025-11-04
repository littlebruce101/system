"""
SQLAlchemy models for the Truth-First Search System.
Corresponds to database/schema.sql.
"""

from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum as PyEnum
import uuid

from sqlalchemy import (
    Column, String, Integer, Numeric, Text, TIMESTAMP, Boolean,
    ForeignKey, CheckConstraint, Index, ARRAY, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ENUM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class VerificationStatus(PyEnum):
    """Status of claim verification."""
    VERIFIED = "verified"
    CONTRADICTED = "contradicted"
    UNSUPPORTED = "unsupported"
    UNCERTAIN = "uncertain"
    ERROR = "error"


class AlertSeverity(PyEnum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(PyEnum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class ExperimentStatus(PyEnum):
    """Experiment status."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============================================================================
# MODELS
# ============================================================================

class Claim(Base):
    """Claims extracted from text."""
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(50), nullable=False)
    confidence = Column(Numeric(3, 2), nullable=False)

    # Source information
    source_document_id = Column(UUID(as_uuid=True))
    span_start = Column(Integer)
    span_end = Column(Integer)
    context = Column(Text)

    # Extracted entities
    entities = Column(JSONB, default=[])

    # Linguistic features
    hedge_words = Column(ARRAY(Text))
    high_confidence_keywords = Column(ARRAY(Text))

    # Metadata
    extracted_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    verification_results = relationship("VerificationResult", back_populates="claim", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='claims_confidence_check'),
        Index('idx_claims_type', 'claim_type'),
        Index('idx_claims_confidence', 'confidence'),
        Index('idx_claims_extracted_at', 'extracted_at'),
    )


class VerificationResult(Base):
    """Verification results for claims."""
    __tablename__ = "verification_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey('claims.id', ondelete='CASCADE'), nullable=False)

    # Verification outcome
    status = Column(ENUM(VerificationStatus, name='verification_status'), nullable=False)
    confidence = Column(Numeric(3, 2), nullable=False)

    # Evidence
    evidence = Column(JSONB, default=[])
    contradictions = Column(JSONB, default=[])
    sources = Column(JSONB, default=[])

    # Metadata
    verification_method = Column(String(100))
    verified_at = Column(TIMESTAMP, default=datetime.utcnow)
    cache_key = Column(String(64))
    cache_expires_at = Column(TIMESTAMP)

    # Quality metrics
    sources_consulted = Column(Integer, default=0)
    evidence_count = Column(Integer, default=0)
    contradiction_count = Column(Integer, default=0)

    # Relationships
    claim = relationship("Claim", back_populates="verification_results")

    __table_args__ = (
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='verification_confidence_check'),
        Index('idx_verification_claim_id', 'claim_id'),
        Index('idx_verification_status', 'status'),
        Index('idx_verification_confidence', 'confidence'),
        Index('idx_verification_cache_key', 'cache_key'),
        Index('idx_verification_verified_at', 'verified_at'),
    )


class BiasDetectionResult(Base):
    """Bias detection analysis results."""
    __tablename__ = "bias_detection_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Text being analyzed
    text_hash = Column(String(64), nullable=False)
    text_preview = Column(Text)
    word_count = Column(Integer)

    # Overall scores
    overall_bias_score = Column(Numeric(3, 2), nullable=False)
    neutrality_score = Column(Numeric(3, 2), nullable=False)

    # Bias type breakdowns
    emotional_loading = Column(JSONB, default={})
    hedge_words = Column(JSONB, default={})
    hyperbole = Column(JSONB, default={})
    ad_hominem = Column(JSONB, default={})
    weasel_words = Column(JSONB, default={})
    loaded_questions = Column(JSONB, default={})
    false_balance = Column(JSONB, default={})
    cherry_picking = Column(JSONB, default={})

    # Neutrality indicators
    neutrality_indicators = Column(JSONB, default={})

    # Recommendations
    recommendations = Column(ARRAY(Text))

    # Metadata
    context = Column(String(100))
    analyzed_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('overall_bias_score >= 0 AND overall_bias_score <= 1', name='bias_score_check'),
        CheckConstraint('neutrality_score >= 0 AND neutrality_score <= 1', name='neutrality_score_check'),
        Index('idx_bias_text_hash', 'text_hash'),
        Index('idx_bias_overall_score', 'overall_bias_score'),
        Index('idx_bias_neutrality_score', 'neutrality_score'),
        Index('idx_bias_analyzed_at', 'analyzed_at'),
    )


class TruthScore(Base):
    """Combined truth scores for documents."""
    __tablename__ = "truth_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Document/content reference
    document_id = Column(UUID(as_uuid=True), nullable=False)
    document_url = Column(Text)
    document_title = Column(Text)

    # Component scores
    claim_extraction_score = Column(Numeric(3, 2))
    verification_score = Column(Numeric(3, 2))
    bias_score = Column(Numeric(3, 2))

    # Final combined score
    truth_score = Column(Numeric(3, 2), nullable=False)

    # Score weights used
    weights = Column(JSONB, default={
        "verification": 0.5,
        "bias": 0.3,
        "claim_quality": 0.2
    })

    # References
    claims_analyzed = Column(Integer, default=0)
    claims_verified = Column(Integer, default=0)
    claims_contradicted = Column(Integer, default=0)

    # Metadata
    scored_at = Column(TIMESTAMP, default=datetime.utcnow)
    score_version = Column(String(20), default='1.0')

    # A/B testing
    experiment_id = Column(UUID(as_uuid=True), ForeignKey('experiments.id'))
    variant = Column(String(50))

    __table_args__ = (
        CheckConstraint('truth_score >= 0 AND truth_score <= 1', name='truth_score_check'),
        Index('idx_truth_document_id', 'document_id'),
        Index('idx_truth_score', 'truth_score'),
        Index('idx_truth_scored_at', 'scored_at'),
        Index('idx_truth_experiment', 'experiment_id', 'variant'),
    )


class TruthScoreMetric(Base):
    """Aggregated metrics for monitoring."""
    __tablename__ = "truth_score_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Time bucket for aggregation
    timestamp = Column(TIMESTAMP, nullable=False)
    time_bucket = Column(String(20), nullable=False)

    # Aggregated metrics
    avg_truth_score = Column(Numeric(3, 2))
    median_truth_score = Column(Numeric(3, 2))
    min_truth_score = Column(Numeric(3, 2))
    max_truth_score = Column(Numeric(3, 2))
    stddev_truth_score = Column(Numeric(5, 4))

    # Volume metrics
    total_documents_scored = Column(Integer, default=0)
    total_claims_extracted = Column(Integer, default=0)
    total_verifications = Column(Integer, default=0)

    # Quality metrics
    verification_rate = Column(Numeric(3, 2))
    contradiction_rate = Column(Numeric(3, 2))
    avg_bias_score = Column(Numeric(3, 2))

    # Performance metrics
    avg_processing_time_ms = Column(Integer)
    cache_hit_rate = Column(Numeric(3, 2))

    # Metadata
    recorded_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_metrics_timestamp', 'timestamp'),
        Index('idx_metrics_time_bucket', 'time_bucket', 'timestamp'),
    )


class Alert(Base):
    """System alerts for monitoring."""
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Alert details
    alert_type = Column(String(100), nullable=False)
    severity = Column(ENUM(AlertSeverity, name='alert_severity'), nullable=False)
    status = Column(ENUM(AlertStatus, name='alert_status'), default=AlertStatus.ACTIVE)

    # Message
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Metrics that triggered alert
    trigger_metric = Column(String(100))
    trigger_threshold = Column(Numeric(10, 4))
    actual_value = Column(Numeric(10, 4))

    # Context
    metadata = Column(JSONB, default={})

    # Timestamps
    triggered_at = Column(TIMESTAMP, default=datetime.utcnow)
    acknowledged_at = Column(TIMESTAMP)
    resolved_at = Column(TIMESTAMP)
    acknowledged_by = Column(String(100))
    resolved_by = Column(String(100))

    __table_args__ = (
        Index('idx_alerts_status', 'status', 'severity'),
        Index('idx_alerts_triggered_at', 'triggered_at'),
        Index('idx_alerts_type', 'alert_type'),
    )


class Experiment(Base):
    """A/B testing experiments."""
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Experiment details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    hypothesis = Column(Text)

    # Status
    status = Column(ENUM(ExperimentStatus, name='experiment_status'), default=ExperimentStatus.DRAFT)

    # Variants configuration
    variants = Column(JSONB, nullable=False)
    traffic_split = Column(JSONB, nullable=False)

    # Success metrics
    primary_metric = Column(String(100), nullable=False)
    secondary_metrics = Column(ARRAY(Text))

    # Statistical parameters
    minimum_sample_size = Column(Integer, default=1000)
    confidence_level = Column(Numeric(3, 2), default=0.95)
    minimum_detectable_effect = Column(Numeric(3, 2), default=0.05)

    # Results
    results = Column(JSONB)
    winner = Column(String(50))

    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    started_at = Column(TIMESTAMP)
    ended_at = Column(TIMESTAMP)
    created_by = Column(String(100))

    __table_args__ = (
        Index('idx_experiments_status', 'status'),
        Index('idx_experiments_created_at', 'created_at'),
    )


class ExperimentResult(Base):
    """Results for A/B test variants."""
    __tablename__ = "experiment_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False)

    # Variant
    variant = Column(String(50), nullable=False)

    # Metrics
    sample_size = Column(Integer, nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Numeric(10, 6))

    # Statistics
    mean_value = Column(Numeric(10, 6))
    median_value = Column(Numeric(10, 6))
    stddev = Column(Numeric(10, 6))
    confidence_interval_lower = Column(Numeric(10, 6))
    confidence_interval_upper = Column(Numeric(10, 6))

    # Significance
    p_value = Column(Numeric(10, 8))
    is_significant = Column(Boolean, default=False)

    # Timestamp
    recorded_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_exp_results_experiment', 'experiment_id', 'variant'),
        Index('idx_exp_results_recorded_at', 'recorded_at'),
    )


class AuditLog(Base):
    """Audit log for tracking system changes."""
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Event details
    event_type = Column(String(100), nullable=False)
    event_category = Column(String(50), nullable=False)

    # Actor
    user_id = Column(String(100))
    user_email = Column(String(255))
    ip_address = Column(INET)

    # Action
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(UUID(as_uuid=True))

    # Changes
    old_values = Column(JSONB)
    new_values = Column(JSONB)

    # Metadata
    metadata = Column(JSONB, default={})

    # Timestamp
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_audit_created_at', 'created_at'),
        Index('idx_audit_event_type', 'event_type'),
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )
