#!/usr/bin/env bash
set -e
BASE="${1:-http://localhost:8080}"

echo "Testing LLM Serving API at $BASE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "1. Health check"
curl -s "$BASE/health" | python3 -m json.tool

echo ""
echo "2. Non-streaming chat"
curl -s -X POST "$BASE/chat" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Reply with only: Hello, World!"}],"max_tokens":20}' \
  | python3 -m json.tool

echo ""
echo "3. Streaming chat (raw SSE)"
curl -s -N -X POST "$BASE/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Count from 1 to 5 slowly."}],"max_tokens":64}' \
  --max-time 30

echo ""
echo "4. Metrics"
curl -s "$BASE/metrics" | python3 -m json.tool

echo ""
echo "5. Detailed metrics"
curl -s "$BASE/metrics/detail" | python3 -m json.tool
