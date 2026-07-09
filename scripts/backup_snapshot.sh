#!/usr/bin/env bash
# Создание snapshot коллекции products (алиас) в Qdrant.
# Запуск: ./scripts/backup_snapshot.sh

set -euo pipefail

QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
COLLECTION="${COLLECTION:-products}"
API_KEY="${QDRANT_API_KEY:-}"
SNAPSHOT_URL="${QDRANT_URL}/collections/${COLLECTION}/snapshots"

curl_snapshot() {
  local method="$1"
  if [[ -n "${API_KEY}" ]]; then
    curl -s -X "${method}" "${SNAPSHOT_URL}" -H "api-key: ${API_KEY}"
  else
    curl -s -X "${method}" "${SNAPSHOT_URL}"
  fi
}

echo "Создание snapshot для ${COLLECTION}..."
curl_snapshot POST

echo ""
echo "Список snapshots:"
curl_snapshot GET
echo ""
