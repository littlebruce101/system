# OpenSearch Setup for Truth-First Search

This directory contains the configuration and scripts for running the Truth-First Search system with OpenSearch.

## Overview

The setup includes:

- **OpenSearch Cluster** (2 nodes) - Stores and indexes documents with truth scores
- **OpenSearch Dashboards** - Web UI for visualization and management
- **PostgreSQL** - Stores structured data (claims, verification results, metrics)
- **Redis** - Caching layer for improved performance

## Quick Start

### Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 1.29+)
- Python 3.8+
- 4GB+ RAM available

### 1. Start the Cluster

```bash
cd opensearch
./scripts/start.sh
```

This will:
1. Start all Docker containers
2. Wait for OpenSearch to be ready
3. Create necessary indices
4. Display access information

### 2. Verify Installation

```bash
# Check cluster health
curl -k -u admin:Admin123! https://localhost:9200/_cluster/health?pretty

# List indices
curl -k -u admin:Admin123! https://localhost:9200/_cat/indices?v
```

### 3. Access Services

- **OpenSearch API**: https://localhost:9200
- **OpenSearch Dashboards**: http://localhost:5601
- **PostgreSQL**: localhost:5432 (database: `truth_search`, user: `truth_user`)
- **Redis**: localhost:6379

## Configuration

### Environment Variables

Create a `.env` file in the `opensearch` directory:

```env
OPENSEARCH_ADMIN_PASSWORD=YourSecurePassword123!
POSTGRES_PASSWORD=YourPostgresPassword123!
```

### Resource Allocation

Edit `docker-compose.yml` to adjust resource limits:

```yaml
environment:
  - "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g"  # Adjust heap size
```

## Indices

The following indices are created:

### truth-documents
Stores documents with their truth scores.

**Fields:**
- `document_id`: Unique identifier
- `url`: Document URL
- `title`: Document title
- `content`: Full text content
- `truth_score`: Final truth score (0-1)
- `verification_score`: Verification component score
- `bias_score`: Bias/neutrality score
- `claim_extraction_score`: Claim quality score
- `claims_analyzed`: Number of claims found
- `claims_verified`: Number verified
- `claims_contradicted`: Number contradicted

### truth-claims
Stores extracted claims and verification results.

**Fields:**
- `claim_id`: Unique identifier
- `claim_text`: The claim statement
- `claim_type`: Type (statistical, causal, etc.)
- `confidence`: Extraction confidence
- `entities`: Named entities involved
- `verification_status`: verified/contradicted/unsupported
- `verification_confidence`: Verification confidence

### truth-metrics
Time-series metrics for monitoring.

**Fields:**
- `timestamp`: Metric timestamp
- `avg_truth_score`: Average truth score
- `total_documents_scored`: Count
- `verification_rate`: Percentage verified
- `contradiction_rate`: Percentage contradicted
- `avg_processing_time_ms`: Performance metric

### truth-alerts
System alerts and notifications.

**Fields:**
- `alert_type`: Type of alert
- `severity`: info/warning/error/critical
- `status`: active/acknowledged/resolved
- `title`: Alert title
- `trigger_metric`: Metric that triggered
- `triggered_at`: Timestamp

## Querying

### Search Documents by Truth Score

```bash
curl -k -u admin:Admin123! -X POST "https://localhost:9200/truth-documents/_search?pretty" \
-H 'Content-Type: application/json' -d'
{
  "query": {
    "range": {
      "truth_score": {
        "gte": 0.7
      }
    }
  },
  "sort": [
    { "truth_score": "desc" }
  ]
}
'
```

### Find Contradicted Claims

```bash
curl -k -u admin:Admin123! -X POST "https://localhost:9200/truth-claims/_search?pretty" \
-H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {
      "verification_status": "contradicted"
    }
  }
}
'
```

### Get Recent Metrics

```bash
curl -k -u admin:Admin123! -X POST "https://localhost:9200/truth-metrics/_search?pretty" \
-H 'Content-Type: application/json' -d'
{
  "query": {
    "range": {
      "timestamp": {
        "gte": "now-1h"
      }
    }
  },
  "sort": [
    { "timestamp": "desc" }
  ]
}
'
```

## Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f opensearch-node1
```

### Restart Services

```bash
docker-compose restart
```

### Stop Services

```bash
# Stop (keep data)
docker-compose down

# Stop and remove volumes (delete all data)
docker-compose down -v
```

### Backup Data

```bash
# Backup PostgreSQL
docker exec truth-search-postgres pg_dump -U truth_user truth_search > backup.sql

# Backup OpenSearch indices
# (Use OpenSearch snapshot API - see docs)
```

## Troubleshooting

### OpenSearch won't start

Check if max virtual memory is set:
```bash
# Linux
sudo sysctl -w vm.max_map_count=262144

# Add to /etc/sysctl.conf for persistence
vm.max_map_count=262144
```

### Out of memory errors

Increase Docker memory limit or reduce heap size in docker-compose.yml.

### Connection refused

Ensure ports are not already in use:
```bash
lsof -i :9200  # OpenSearch
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
```

## Performance Tuning

### For Production

1. Increase heap size:
   ```yaml
   OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g
   ```

2. Add more nodes:
   - Copy `opensearch-node2` config
   - Update node name and data volume
   - Add to `cluster.initial_cluster_manager_nodes`

3. Enable monitoring:
   - Use Prometheus exporters
   - Configure alerting

4. Optimize indices:
   - Adjust `refresh_interval`
   - Configure index lifecycle policies
   - Use index templates

## Next Steps

- Configure the Truth Scoring API to use these services
- Set up monitoring dashboards in OpenSearch Dashboards
- Configure backup and disaster recovery
- Set up SSL certificates for production
- Implement authentication and authorization

## Resources

- [OpenSearch Documentation](https://opensearch.org/docs/latest/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
