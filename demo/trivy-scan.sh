#!/usr/bin/env bash
set -euo pipefail
IMAGE="$1"
OUT=trivy-result.json

# run trivy; exit code 1 if vulnerabilities found per severity
trivy image --format json --output "$OUT" "$IMAGE"

# simple check for HIGH/CRITICAL using jq if available
if command -v jq >/dev/null 2>&1; then
  high=$(jq '.Results[].Vulnerabilities[]? | select(.Severity=="CRITICAL" or .Severity=="HIGH")' "$OUT" | wc -l)
  if [ "$high" -gt 0 ]; then
    echo "trivy: found HIGH/CRITICAL vulnerabilities"
    jq . "$OUT"
    exit 1
  fi
fi

echo "trivy: no HIGH/CRITICAL vulnerabilities (or jq not installed)"
exit 0
