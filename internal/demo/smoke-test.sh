#!/usr/bin/env bash
# Smoke test: run a container, poll /healthz, exit 0 on success, 1 on timeout.
#
# Usage:
#   ./demo/smoke-test.sh <image> [port] [--keep]
#
# Flags:
#   --keep   Leave the container running after a successful health-check.
#            Used by the DAST stage so ZAP can scan the live app.
#            The caller is responsible for stopping the container afterward.
#
# Examples:
#   ./demo/smoke-test.sh aisec:smoke 8000
#   ./demo/smoke-test.sh aisec:smoke 8000 --keep
#
# Health endpoint: /healthz (FastAPI apps in this repo)
# Timeout: 90 seconds (18 × 5s polls)
set -euo pipefail

IMAGE="${1:?Usage: smoke-test.sh <image> [port] [--keep]}"
PORT="${2:-8000}"
KEEP=0
if [ "${3:-}" = "--keep" ]; then
  KEEP=1
fi

NAME="smoke-$RANDOM"
# Export so the DAST stage knows which container to stop
echo "$NAME" > /tmp/smoke-container-name

# Minimal runtime env vars so FastAPI app can start without DB
docker run -d --name "$NAME" \
  -p "${PORT}:${PORT}" \
  -e SUPABASE_URL="https://placeholder.supabase.co" \
  -e SUPABASE_ANON_KEY="placeholder" \
  -e SUPABASE_JWT_SECRET="placeholder-32-chars-minimum-here" \
  -e DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test" \
  "$IMAGE"

echo "smoke: container $NAME started on port $PORT, waiting for /healthz..."

for i in $(seq 1 18); do
  sleep 5
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/healthz" 2>/dev/null || echo "000")
  if [ "$HTTP" = "200" ]; then
    echo "smoke: /healthz returned 200 — application healthy (attempt $i)"
    if [ "$KEEP" -eq 1 ]; then
      echo "smoke: --keep set, leaving container $NAME running for DAST scan"
    else
      docker rm -f "$NAME" >/dev/null 2>&1 || true
    fi
    exit 0
  fi
  echo "smoke: attempt $i — got $HTTP, retrying..."
done

echo "smoke: FAILED — /healthz never returned 200 after 90s"
docker logs "$NAME" || true
docker rm -f "$NAME" >/dev/null 2>&1 || true
exit 1
