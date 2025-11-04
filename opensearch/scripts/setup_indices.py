#!/usr/bin/env python3
"""
Setup OpenSearch indices for truth-first search.
Creates indices with appropriate mappings and settings.
"""

import os
import sys
import logging
from typing import Dict
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import RequestError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Index mappings and settings

DOCUMENTS_INDEX = {
    "settings": {
        "number_of_shards": 2,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "truth_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "asciifolding",
                        "stop",
                        "snowball"
                    ]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "document_id": {"type": "keyword"},
            "url": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "truth_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "content": {
                "type": "text",
                "analyzer": "truth_analyzer"
            },
            "truth_score": {"type": "float"},
            "verification_score": {"type": "float"},
            "bias_score": {"type": "float"},
            "claim_extraction_score": {"type": "float"},
            "claims_analyzed": {"type": "integer"},
            "claims_verified": {"type": "integer"},
            "claims_contradicted": {"type": "integer"},
            "score_version": {"type": "keyword"},
            "experiment_id": {"type": "keyword"},
            "variant": {"type": "keyword"},
            "indexed_at": {"type": "date"},
            "scored_at": {"type": "date"}
        }
    }
}

CLAIMS_INDEX = {
    "settings": {
        "number_of_shards": 2,
        "number_of_replicas": 1
    },
    "mappings": {
        "properties": {
            "claim_id": {"type": "keyword"},
            "claim_text": {
                "type": "text",
                "analyzer": "truth_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "claim_type": {"type": "keyword"},
            "confidence": {"type": "float"},
            "document_id": {"type": "keyword"},
            "entities": {
                "type": "nested",
                "properties": {
                    "text": {"type": "keyword"},
                    "label": {"type": "keyword"},
                    "start": {"type": "integer"},
                    "end": {"type": "integer"}
                }
            },
            "verification_status": {"type": "keyword"},
            "verification_confidence": {"type": "float"},
            "evidence_count": {"type": "integer"},
            "contradiction_count": {"type": "integer"},
            "extracted_at": {"type": "date"},
            "verified_at": {"type": "date"}
        }
    }
}

METRICS_INDEX = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "index": {
            "lifecycle": {
                "name": "metrics_policy",
                "rollover_alias": "truth-metrics"
            }
        }
    },
    "mappings": {
        "properties": {
            "timestamp": {"type": "date"},
            "time_bucket": {"type": "keyword"},
            "avg_truth_score": {"type": "float"},
            "median_truth_score": {"type": "float"},
            "min_truth_score": {"type": "float"},
            "max_truth_score": {"type": "float"},
            "stddev_truth_score": {"type": "float"},
            "total_documents_scored": {"type": "integer"},
            "total_claims_extracted": {"type": "integer"},
            "total_verifications": {"type": "integer"},
            "verification_rate": {"type": "float"},
            "contradiction_rate": {"type": "float"},
            "avg_bias_score": {"type": "float"},
            "avg_processing_time_ms": {"type": "integer"},
            "cache_hit_rate": {"type": "float"}
        }
    }
}

ALERTS_INDEX = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1
    },
    "mappings": {
        "properties": {
            "alert_id": {"type": "keyword"},
            "alert_type": {"type": "keyword"},
            "severity": {"type": "keyword"},
            "status": {"type": "keyword"},
            "title": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "description": {"type": "text"},
            "trigger_metric": {"type": "keyword"},
            "trigger_threshold": {"type": "float"},
            "actual_value": {"type": "float"},
            "triggered_at": {"type": "date"},
            "acknowledged_at": {"type": "date"},
            "resolved_at": {"type": "date"},
            "acknowledged_by": {"type": "keyword"},
            "resolved_by": {"type": "keyword"}
        }
    }
}


def get_opensearch_client() -> OpenSearch:
    """Create OpenSearch client."""
    host = os.getenv("OPENSEARCH_HOST", "localhost")
    port = int(os.getenv("OPENSEARCH_PORT", "9200"))
    username = os.getenv("OPENSEARCH_USERNAME", "admin")
    password = os.getenv("OPENSEARCH_PASSWORD", "Admin123!")

    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=(username, password),
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False,
        connection_class=RequestsHttpConnection
    )

    return client


def create_index(client: OpenSearch, index_name: str, index_config: Dict):
    """Create an index with given configuration."""
    try:
        if client.indices.exists(index=index_name):
            logger.info(f"Index '{index_name}' already exists")
            return

        client.indices.create(
            index=index_name,
            body=index_config
        )
        logger.info(f"Created index: {index_name}")

    except RequestError as e:
        logger.error(f"Error creating index {index_name}: {e}")
        raise


def setup_index_templates(client: OpenSearch):
    """Setup index templates for time-series data."""
    metrics_template = {
        "index_patterns": ["truth-metrics-*"],
        "template": {
            "settings": METRICS_INDEX["settings"],
            "mappings": METRICS_INDEX["mappings"]
        }
    }

    try:
        client.indices.put_index_template(
            name="truth-metrics-template",
            body=metrics_template
        )
        logger.info("Created index template: truth-metrics-template")
    except RequestError as e:
        logger.error(f"Error creating template: {e}")


def main():
    """Setup all indices."""
    logger.info("Starting OpenSearch index setup...")

    try:
        client = get_opensearch_client()
        logger.info("Connected to OpenSearch")

        # Create indices
        indices = {
            "truth-documents": DOCUMENTS_INDEX,
            "truth-claims": CLAIMS_INDEX,
            "truth-metrics": METRICS_INDEX,
            "truth-alerts": ALERTS_INDEX
        }

        for index_name, index_config in indices.items():
            create_index(client, index_name, index_config)

        # Setup templates
        setup_index_templates(client)

        logger.info("✓ All indices created successfully")

        # Print cluster health
        health = client.cluster.health()
        logger.info(f"Cluster health: {health['status']}")
        logger.info(f"Number of nodes: {health['number_of_nodes']}")
        logger.info(f"Active shards: {health['active_shards']}")

        return 0

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
