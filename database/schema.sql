-- Truth-First Search System Database Schema
-- PostgreSQL 14+

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text similarity searches

-- ============================================================================
-- CLAIMS STORAGE
-- ============================================================================

CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_text TEXT NOT NULL,
    claim_type VARCHAR(50) NOT NULL,  -- statistical, causal, temporal, etc.
    confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),

    -- Source information
    source_document_id UUID,
    span_start INTEGER,
    span_end INTEGER,
    context TEXT,

    -- Extracted entities
    entities JSONB DEFAULT '[]'::jsonb,

    -- Linguistic features
    hedge_words TEXT[],
    high_confidence_keywords TEXT[],

    -- Metadata
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexing
    CONSTRAINT claims_confidence_check CHECK (confidence >= 0 AND confidence <= 1)
);

-- Indexes for claims
CREATE INDEX idx_claims_type ON claims(claim_type);
CREATE INDEX idx_claims_confidence ON claims(confidence DESC);
CREATE INDEX idx_claims_extracted_at ON claims(extracted_at DESC);
CREATE INDEX idx_claims_text_gin ON claims USING gin(to_tsvector('english', claim_text));
CREATE INDEX idx_claims_entities ON claims USING gin(entities);

-- ============================================================================
-- VERIFICATION RESULTS
-- ============================================================================

CREATE TYPE verification_status AS ENUM (
    'verified',
    'contradicted',
    'unsupported',
    'uncertain',
    'error'
);

CREATE TABLE IF NOT EXISTS verification_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,

    -- Verification outcome
    status verification_status NOT NULL,
    confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),

    -- Evidence
    evidence JSONB DEFAULT '[]'::jsonb,  -- Array of evidence statements
    contradictions JSONB DEFAULT '[]'::jsonb,  -- Array of contradicting statements
    sources JSONB DEFAULT '[]'::jsonb,  -- Array of source objects

    -- Metadata
    verification_method VARCHAR(100),  -- 'wikidata', 'factcheck_api', 'manual', etc.
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cache_key VARCHAR(64),  -- SHA256 hash for caching
    cache_expires_at TIMESTAMP,

    -- Quality metrics
    sources_consulted INTEGER DEFAULT 0,
    evidence_count INTEGER DEFAULT 0,
    contradiction_count INTEGER DEFAULT 0
);

-- Indexes for verification
CREATE INDEX idx_verification_claim_id ON verification_results(claim_id);
CREATE INDEX idx_verification_status ON verification_results(status);
CREATE INDEX idx_verification_confidence ON verification_results(confidence DESC);
CREATE INDEX idx_verification_cache_key ON verification_results(cache_key);
CREATE INDEX idx_verification_verified_at ON verification_results(verified_at DESC);

-- ============================================================================
-- BIAS DETECTION RESULTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS bias_detection_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Text being analyzed
    text_hash VARCHAR(64) NOT NULL,  -- SHA256 of text for caching
    text_preview TEXT,  -- First 500 chars for reference
    word_count INTEGER,

    -- Overall scores
    overall_bias_score DECIMAL(3,2) NOT NULL CHECK (overall_bias_score >= 0 AND overall_bias_score <= 1),
    neutrality_score DECIMAL(3,2) NOT NULL CHECK (neutrality_score >= 0 AND neutrality_score <= 1),

    -- Bias type breakdowns
    emotional_loading JSONB DEFAULT '{}'::jsonb,
    hedge_words JSONB DEFAULT '{}'::jsonb,
    hyperbole JSONB DEFAULT '{}'::jsonb,
    ad_hominem JSONB DEFAULT '{}'::jsonb,
    weasel_words JSONB DEFAULT '{}'::jsonb,
    loaded_questions JSONB DEFAULT '{}'::jsonb,
    false_balance JSONB DEFAULT '{}'::jsonb,
    cherry_picking JSONB DEFAULT '{}'::jsonb,

    -- Neutrality indicators
    neutrality_indicators JSONB DEFAULT '{}'::jsonb,

    -- Recommendations
    recommendations TEXT[],

    -- Metadata
    context VARCHAR(100),  -- 'news', 'opinion', 'academic', etc.
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for bias detection
CREATE INDEX idx_bias_text_hash ON bias_detection_results(text_hash);
CREATE INDEX idx_bias_overall_score ON bias_detection_results(overall_bias_score DESC);
CREATE INDEX idx_bias_neutrality_score ON bias_detection_results(neutrality_score DESC);
CREATE INDEX idx_bias_analyzed_at ON bias_detection_results(analyzed_at DESC);

-- ============================================================================
-- TRUTH SCORES (Combined scoring)
-- ============================================================================

CREATE TABLE IF NOT EXISTS truth_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Document/content reference
    document_id UUID NOT NULL,
    document_url TEXT,
    document_title TEXT,

    -- Component scores
    claim_extraction_score DECIMAL(3,2),
    verification_score DECIMAL(3,2),
    bias_score DECIMAL(3,2),

    -- Final combined score
    truth_score DECIMAL(3,2) NOT NULL CHECK (truth_score >= 0 AND truth_score <= 1),

    -- Score weights used
    weights JSONB DEFAULT '{
        "verification": 0.5,
        "bias": 0.3,
        "claim_quality": 0.2
    }'::jsonb,

    -- References
    claims_analyzed INTEGER DEFAULT 0,
    claims_verified INTEGER DEFAULT 0,
    claims_contradicted INTEGER DEFAULT 0,

    -- Metadata
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score_version VARCHAR(20) DEFAULT '1.0',  -- For tracking algorithm versions

    -- A/B testing
    experiment_id UUID,  -- Reference to active experiment
    variant VARCHAR(50)  -- 'control', 'variant_a', 'variant_b', etc.
);

-- Indexes for truth scores
CREATE INDEX idx_truth_document_id ON truth_scores(document_id);
CREATE INDEX idx_truth_score ON truth_scores(truth_score DESC);
CREATE INDEX idx_truth_scored_at ON truth_scores(scored_at DESC);
CREATE INDEX idx_truth_experiment ON truth_scores(experiment_id, variant);

-- ============================================================================
-- MONITORING & METRICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS truth_score_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Time bucket for aggregation
    timestamp TIMESTAMP NOT NULL,
    time_bucket VARCHAR(20) NOT NULL,  -- 'minute', 'hour', 'day'

    -- Aggregated metrics
    avg_truth_score DECIMAL(3,2),
    median_truth_score DECIMAL(3,2),
    min_truth_score DECIMAL(3,2),
    max_truth_score DECIMAL(3,2),
    stddev_truth_score DECIMAL(5,4),

    -- Volume metrics
    total_documents_scored INTEGER DEFAULT 0,
    total_claims_extracted INTEGER DEFAULT 0,
    total_verifications INTEGER DEFAULT 0,

    -- Quality metrics
    verification_rate DECIMAL(3,2),  -- % of claims verified
    contradiction_rate DECIMAL(3,2),  -- % of claims contradicted
    avg_bias_score DECIMAL(3,2),

    -- Performance metrics
    avg_processing_time_ms INTEGER,
    cache_hit_rate DECIMAL(3,2),

    -- Metadata
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for metrics
CREATE INDEX idx_metrics_timestamp ON truth_score_metrics(timestamp DESC);
CREATE INDEX idx_metrics_time_bucket ON truth_score_metrics(time_bucket, timestamp DESC);

-- ============================================================================
-- ALERTS
-- ============================================================================

CREATE TYPE alert_severity AS ENUM ('info', 'warning', 'error', 'critical');
CREATE TYPE alert_status AS ENUM ('active', 'acknowledged', 'resolved');

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Alert details
    alert_type VARCHAR(100) NOT NULL,  -- 'score_degradation', 'high_error_rate', etc.
    severity alert_severity NOT NULL,
    status alert_status DEFAULT 'active',

    -- Message
    title VARCHAR(255) NOT NULL,
    description TEXT,

    -- Metrics that triggered alert
    trigger_metric VARCHAR(100),
    trigger_threshold DECIMAL(10,4),
    actual_value DECIMAL(10,4),

    -- Context
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    acknowledged_by VARCHAR(100),
    resolved_by VARCHAR(100)
);

-- Indexes for alerts
CREATE INDEX idx_alerts_status ON alerts(status, severity);
CREATE INDEX idx_alerts_triggered_at ON alerts(triggered_at DESC);
CREATE INDEX idx_alerts_type ON alerts(alert_type);

-- ============================================================================
-- A/B TESTING EXPERIMENTS
-- ============================================================================

CREATE TYPE experiment_status AS ENUM ('draft', 'running', 'paused', 'completed', 'cancelled');

CREATE TABLE IF NOT EXISTS experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Experiment details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    hypothesis TEXT,

    -- Status
    status experiment_status DEFAULT 'draft',

    -- Variants configuration
    variants JSONB NOT NULL,  -- Array of variant configs with weights
    traffic_split JSONB NOT NULL,  -- How to split traffic

    -- Success metrics
    primary_metric VARCHAR(100) NOT NULL,  -- 'truth_score', 'user_satisfaction', etc.
    secondary_metrics TEXT[],

    -- Statistical parameters
    minimum_sample_size INTEGER DEFAULT 1000,
    confidence_level DECIMAL(3,2) DEFAULT 0.95,
    minimum_detectable_effect DECIMAL(3,2) DEFAULT 0.05,

    -- Results
    results JSONB,
    winner VARCHAR(50),  -- Winning variant

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_by VARCHAR(100)
);

-- Indexes for experiments
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_created_at ON experiments(created_at DESC);

-- ============================================================================
-- EXPERIMENT RESULTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS experiment_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,

    -- Variant
    variant VARCHAR(50) NOT NULL,

    -- Metrics
    sample_size INTEGER NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,6),

    -- Statistics
    mean_value DECIMAL(10,6),
    median_value DECIMAL(10,6),
    stddev DECIMAL(10,6),
    confidence_interval_lower DECIMAL(10,6),
    confidence_interval_upper DECIMAL(10,6),

    -- Significance
    p_value DECIMAL(10,8),
    is_significant BOOLEAN DEFAULT false,

    -- Timestamp
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for experiment results
CREATE INDEX idx_exp_results_experiment ON experiment_results(experiment_id, variant);
CREATE INDEX idx_exp_results_recorded_at ON experiment_results(recorded_at DESC);

-- ============================================================================
-- AUDIT LOG
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Event details
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(50) NOT NULL,  -- 'claim', 'verification', 'score', 'experiment', etc.

    -- Actor
    user_id VARCHAR(100),
    user_email VARCHAR(255),
    ip_address INET,

    -- Action
    action VARCHAR(100) NOT NULL,  -- 'create', 'update', 'delete', 'verify', etc.
    resource_type VARCHAR(100),
    resource_id UUID,

    -- Changes
    old_values JSONB,
    new_values JSONB,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit log
CREATE INDEX idx_audit_created_at ON audit_log(created_at DESC);
CREATE INDEX idx_audit_event_type ON audit_log(event_type);
CREATE INDEX idx_audit_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Recent high-quality verified claims
CREATE OR REPLACE VIEW recent_verified_claims AS
SELECT
    c.id,
    c.claim_text,
    c.claim_type,
    c.confidence as claim_confidence,
    vr.status as verification_status,
    vr.confidence as verification_confidence,
    vr.evidence,
    vr.sources,
    c.extracted_at
FROM claims c
JOIN verification_results vr ON c.id = vr.claim_id
WHERE vr.status = 'verified'
  AND vr.confidence >= 0.7
  AND c.confidence >= 0.6
ORDER BY c.extracted_at DESC;

-- View: Truth score trends
CREATE OR REPLACE VIEW truth_score_trends AS
SELECT
    DATE_TRUNC('day', scored_at) as date,
    AVG(truth_score) as avg_score,
    COUNT(*) as documents_scored,
    AVG(verification_score) as avg_verification,
    AVG(bias_score) as avg_bias
FROM truth_scores
GROUP BY DATE_TRUNC('day', scored_at)
ORDER BY date DESC;

-- View: Active alerts summary
CREATE OR REPLACE VIEW active_alerts_summary AS
SELECT
    severity,
    alert_type,
    COUNT(*) as count,
    MAX(triggered_at) as last_triggered
FROM alerts
WHERE status = 'active'
GROUP BY severity, alert_type
ORDER BY severity DESC, count DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger: Auto-update updated_at for claims
CREATE TRIGGER update_claims_updated_at
    BEFORE UPDATE ON claims
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function: Calculate truth score from components
CREATE OR REPLACE FUNCTION calculate_truth_score(
    verification_score DECIMAL,
    bias_score DECIMAL,
    claim_quality_score DECIMAL,
    weights JSONB DEFAULT '{"verification": 0.5, "bias": 0.3, "claim_quality": 0.2}'::jsonb
)
RETURNS DECIMAL AS $$
DECLARE
    w_verification DECIMAL;
    w_bias DECIMAL;
    w_claim DECIMAL;
    final_score DECIMAL;
BEGIN
    -- Extract weights
    w_verification := (weights->>'verification')::DECIMAL;
    w_bias := (weights->>'bias')::DECIMAL;
    w_claim := (weights->>'claim_quality')::DECIMAL;

    -- Calculate weighted score
    final_score := (
        COALESCE(verification_score, 0.5) * w_verification +
        COALESCE(bias_score, 0.5) * w_bias +
        COALESCE(claim_quality_score, 0.5) * w_claim
    );

    -- Clamp to [0, 1]
    RETURN GREATEST(0, LEAST(1, final_score));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- SAMPLE DATA (for testing)
-- ============================================================================

-- Comment out in production
-- INSERT INTO claims (claim_text, claim_type, confidence, context) VALUES
-- ('75% of users prefer faster search results', 'statistical', 0.85, 'According to recent studies, 75% of users prefer faster search results.'),
-- ('Python is a programming language', 'definitional', 0.95, 'Python is a programming language created by Guido van Rossum.');
