#!/bin/bash
# Startup script for Truth-First Search OpenSearch cluster

set -e

echo "=========================================="
echo "Truth-First Search - OpenSearch Setup"
echo "=========================================="
echo ""

# Set default passwords if not provided
export OPENSEARCH_ADMIN_PASSWORD="${OPENSEARCH_ADMIN_PASSWORD:-Admin123!}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-TruthPass123!}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed"
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Navigate to opensearch directory
cd "$(dirname "$0")/.."

# Start services
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for OpenSearch to be ready..."
sleep 30

# Wait for OpenSearch to be healthy
MAX_RETRIES=30
RETRY_COUNT=0

until curl -k -u "admin:${OPENSEARCH_ADMIN_PASSWORD}" \
    "https://localhost:9200/_cluster/health?wait_for_status=yellow&timeout=5s" \
    > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ OpenSearch failed to start"
        docker-compose logs opensearch-node1
        exit 1
    fi
    echo "Waiting for OpenSearch... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

echo "✓ OpenSearch is ready"
echo ""

# Setup indices
echo "Setting up indices..."
python3 scripts/setup_indices.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Services:"
    echo "  • OpenSearch:          https://localhost:9200"
    echo "  • OpenSearch Dashboard: http://localhost:5601"
    echo "  • PostgreSQL:          localhost:5432"
    echo "  • Redis:               localhost:6379"
    echo ""
    echo "Credentials:"
    echo "  • OpenSearch:  admin / ${OPENSEARCH_ADMIN_PASSWORD}"
    echo "  • PostgreSQL:  truth_user / ${POSTGRES_PASSWORD}"
    echo ""
    echo "To view logs:    docker-compose logs -f"
    echo "To stop:         docker-compose down"
    echo "To stop & clean: docker-compose down -v"
    echo ""
else
    echo "❌ Index setup failed"
    exit 1
fi
