# Truth-First Search System

A comprehensive production-ready system for evaluating the factual accuracy and truthfulness of content using AI-powered analysis.

## 🎯 Overview

The Truth-First Search System combines multiple AI techniques to score documents based on their factual accuracy:

1. **Claims Extraction** - Identifies factual statements using NLP patterns
2. **Knowledge Verification** - Checks claims against trusted sources (Wikidata, fact-checking APIs)
3. **Bias Detection** - Analyzes language for neutrality and objectivity (8 bias types)
4. **Truth Scoring** - Combines all components into a final truth score (0-1)
5. **Monitoring** - Real-time metrics collection and alerting
6. **A/B Testing** - Framework for optimizing scoring parameters
7. **Search Integration** - OpenSearch deployment for indexing and retrieval

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Input: Document Text                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ├─► Claims Extraction (spaCy NLP)
                 │   ├─ Statistical claims
                 │   ├─ Causal claims
                 │   ├─ Temporal claims
                 │   └─ Definitional claims
                 │
                 ├─► Knowledge Verification
                 │   ├─ Wikidata SPARQL queries
                 │   ├─ Fact-checking APIs
                 │   └─ Source reliability scoring
                 │
                 └─► Bias Detection
                     ├─ Emotional loading
                     ├─ Hyperbole
                     ├─ Ad hominem
                     ├─ Weasel words
                     ├─ Loaded questions
                     ├─ False balance
                     ├─ Cherry-picking
                     └─ Neutrality indicators
                     │
                     ▼
            ┌──────────────────┐
            │  Truth Scoring   │
            │   Engine (0-1)   │
            └────────┬─────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   Monitoring    OpenSearch   A/B Testing
   & Alerts      Indexing     Framework
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker & Docker Compose
- Node.js 18+ (for dashboard)
- 4GB+ RAM

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Start Infrastructure

```bash
cd opensearch
./scripts/start.sh
```

This starts:
- OpenSearch (2 nodes) on ports 9200, 9600
- OpenSearch Dashboards on port 5601
- PostgreSQL on port 5432
- Redis on port 6379

### 3. Run Example

```python
from truth_engine import TruthScorer

# Initialize scorer
scorer = TruthScorer()

# Score a document
text = """
According to recent studies, 75% of users prefer faster search results.
The new algorithm increased accuracy by 30% since January 2024.
Python is a programming language created by Guido van Rossum.
"""

result = scorer.score_document(
    text=text,
    document_title="Tech News Article"
)

print(result.get_summary())
```

Output:
```
Truth Score Summary
===================
Document: Tech News Article
Overall Truth Score: 0.76/1.00 (Good)

Component Scores:
  - Claim Quality: 0.72
  - Verification: 0.78
  - Bias/Neutrality: 0.79

Analysis:
  - 3 claims analyzed
  - 2 claims verified
  - 0 claims contradicted

✓ Document appears factual and neutral
```

### 4. Start Dashboard

```bash
cd dashboard
npm install
npm run dev
```

Access at http://localhost:5173

## 📦 Components

### 1. Claims Extraction Engine

**Location**: `truth_engine/claims/`

Extracts factual claims using spaCy patterns:

```python
from truth_engine import ClaimsExtractor

extractor = ClaimsExtractor()
claims = extractor.extract_claims(text)

for claim in claims:
    print(f"{claim.claim_type}: {claim.text}")
    print(f"Confidence: {claim.confidence:.2f}")
```

**Claim Types**:
- Statistical (e.g., "75% of users...")
- Causal (e.g., "X causes Y...")
- Temporal (e.g., "since January 2024...")
- Definitional (e.g., "Python is...")
- Comparative (e.g., "X is better than Y...")
- Attribution (e.g., "According to...")

### 2. Knowledge Verification

**Location**: `truth_engine/verification/`

Verifies claims against trusted sources:

```python
from truth_engine import KnowledgeBaseVerifier

verifier = KnowledgeBaseVerifier()
result = verifier.verify_claim(
    claim_text="Python was created by Guido van Rossum",
    entities=[{"text": "Python", "label": "PRODUCT"}],
    claim_type="definitional"
)

print(f"Status: {result.status.value}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Sources: {len(result.sources)}")
```

**Data Sources**:
- Wikidata (SPARQL queries)
- Fact-checking APIs (Google Fact Check, FullFact)
- Custom knowledge bases

### 3. Bias Detection

**Location**: `truth_engine/bias/`

Analyzes text for 8 types of bias:

```python
from truth_engine import BiasDetector

detector = BiasDetector()
result = detector.analyze(text)

print(f"Bias Score: {result.overall_bias_score:.2f}")
print(f"Neutrality Score: {result.neutrality_score:.2f}")

for bias_type, data in result.bias_types.items():
    if data["count"] > 0:
        print(f"{bias_type}: {data['count']} instances")
```

**Bias Types**:
1. Emotional Loading (positive/negative/fear)
2. Hedging (uncertainty language)
3. Hyperbole (exaggeration)
4. Ad Hominem (personal attacks)
5. Weasel Words (vague qualifiers)
6. Loaded Questions (presuppositions)
7. False Balance (artificial equivalence)
8. Cherry-Picking (selective presentation)

### 4. Truth Scoring Engine

**Location**: `truth_engine/scoring/`

Combines all components with configurable weights:

```python
from truth_engine import TruthScorer

scorer = TruthScorer(weights={
    "verification": 0.5,
    "bias": 0.3,
    "claim_quality": 0.2
})

result = scorer.score_document(text)
```

### 5. Monitoring & Alerts

**Location**: `truth_engine/monitoring/`

Real-time metrics and alerting:

```python
from truth_engine.monitoring import MetricsCollector, AlertManager

# Collect metrics
collector = MetricsCollector()
collector.record_truth_score(
    truth_score=0.75,
    verification_score=0.80,
    bias_score=0.70,
    # ...
)

# Check for issues
is_degraded, details = collector.detect_score_degradation()

# Manage alerts
alert_manager = AlertManager()
alerts = alert_manager.check_all_rules(context)
```

**Features**:
- Prometheus metrics integration
- Anomaly detection (z-score)
- Score degradation detection
- Customizable alert rules

### 6. A/B Testing Framework

**Location**: `truth_engine/experiments/`

Optimize scoring parameters:

```python
from truth_engine.experiments import ExperimentManager, Variant

manager = ExperimentManager()

# Create experiment
experiment = manager.create_experiment(
    name="Weight Optimization",
    variants=[
        Variant("control", "Current weights", {...}, 0.5),
        Variant("treatment", "New weights", {...}, 0.5)
    ],
    primary_metric="user_satisfaction",
    minimum_sample_size=1000
)

# Start and run
manager.start_experiment(experiment.id)

# Record results
for user in users:
    variant = manager.get_variant_for_user(experiment.id, user.id)
    # ... score document with variant config ...
    manager.record_metric(experiment.id, variant.name, metric)

# Analyze
analysis = experiment.analyze_results()
print(f"Winner: {analysis['winner']}")
```

## 🗄️ Database Schema

**PostgreSQL** stores structured data:

- `claims` - Extracted claims
- `verification_results` - Verification outcomes
- `bias_detection_results` - Bias analysis
- `truth_scores` - Final scores
- `truth_score_metrics` - Aggregated metrics
- `alerts` - System alerts
- `experiments` - A/B tests
- `experiment_results` - Test results
- `audit_log` - Change tracking

**OpenSearch** indexes scored documents for search:

- `truth-documents` - Full-text search with scores
- `truth-claims` - Searchable claims database
- `truth-metrics` - Time-series metrics
- `truth-alerts` - Alert history

## 🎛️ Configuration

### Scoring Weights

Adjust in `truth_engine/scoring/`:

```python
weights = {
    "verification": 0.5,    # How much to weight verification
    "bias": 0.3,            # How much to weight neutrality
    "claim_quality": 0.2    # How much to weight claim extraction
}
```

### Bias Detection Thresholds

Adjust in `truth_engine/bias/lexicons.py`:

```python
# Add custom bias patterns
CUSTOM_PATTERNS = ["pattern1", "pattern2"]

# Adjust severity weights
BIAS_WEIGHTS = {
    "emotional_loading": 0.8,
    "ad_hominem": 1.0,  # Maximum severity
}
```

### Alert Rules

Customize in `truth_engine/monitoring/alerts.py`:

```python
alert_manager.add_rule(AlertRule(
    name="custom_rule",
    alert_type="custom_alert",
    severity=AlertSeverity.WARNING,
    condition=lambda ctx: (ctx["metric"] > threshold, {"data": ...}),
    title_template="Custom Alert: {metric}",
    description_template="Details: {data}",
    cooldown_minutes=30
))
```

## 📊 Dashboard

React-based monitoring dashboard at http://localhost:5173

**Pages**:
- **Dashboard** - System overview, key metrics, recent activity
- **Metrics** - Time-series charts, performance tracking
- **Experiments** - A/B test management and results
- **Alerts** - Active alerts and notification history
- **Documents** - Search and analyze scored content

## 🧪 Testing

Run component tests:

```bash
# Claims extraction
python -m truth_engine.claims.extractor

# Bias detection
python -m truth_engine.bias.detector

# Monitoring
python -m truth_engine.monitoring.metrics

# A/B testing
python -m truth_engine.experiments.ab_testing
```

## 🔧 Development

### Adding a New Bias Type

1. Add patterns to `truth_engine/bias/lexicons.py`
2. Add detection method to `truth_engine/bias/detector.py`
3. Update weight in `get_bias_weights()`

### Adding a New Claim Type

1. Add patterns to `truth_engine/claims/patterns.py`
2. Register with matcher in `ClaimsExtractor._register_patterns()`
3. Update confidence calculation

### Integrating New Data Sources

1. Add source to `truth_engine/verification/knowledge_base.py`
2. Implement query method
3. Update `verify_claim()` to call new source

## 📈 Production Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - OPENSEARCH_URL=https://opensearch:9200
      - REDIS_URL=redis://redis:6379
    depends_on:
      - opensearch
      - postgres
      - redis
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/truth_search
REDIS_URL=redis://localhost:6379

# OpenSearch
OPENSEARCH_URL=https://localhost:9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=secret

# APIs (optional)
GOOGLE_FACTCHECK_API_KEY=...
WIKIDATA_ENDPOINT=https://query.wikidata.org/sparql

# Monitoring
PROMETHEUS_PORT=9090
ENABLE_METRICS=true
```

### Scaling

- **Horizontal**: Run multiple API instances behind load balancer
- **Vertical**: Increase heap size for OpenSearch nodes
- **Database**: Use read replicas for PostgreSQL
- **Caching**: Redis cluster for distributed caching

## 🔒 Security

- HTTPS for all external connections
- API key authentication
- Rate limiting (per-user, per-IP)
- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- XSS protection in dashboard

## 📚 Documentation

- **API Docs**: `/docs` (FastAPI auto-generated)
- **Database Schema**: `database/schema.sql`
- **OpenSearch Setup**: `opensearch/README.md`
- **Dashboard**: `dashboard/README.md`

## 🤝 Contributing

1. Fix the critical drift keywords bug ✅
2. Implement core components ✅
3. Add comprehensive tests
4. Deploy to production
5. Monitor and optimize

## 📄 License

MIT License - See LICENSE file

## 🎉 Credits

Built with:
- spaCy for NLP
- OpenSearch for search
- PostgreSQL for data storage
- React + MUI for dashboard
- Prometheus for metrics

---

**Truth-First Search System v1.0.0**

*Bringing factual accuracy to search results*
