#!/bin/bash
# MCP Facade startup script.
# Waits for the Mimir web service, fetches a DRF auth token, then launches
# the facade server.  All config comes from environment variables.
set -e

SERVER_URL="${MIMIR_SERVER_URL:-http://web:8000}"
TOKEN="${MIMIR_TOKEN:-}"
USER="${MIMIR_USER:-admin}"
PASSWORD="${MIMIR_PASSWORD:-changeme}"
TRANSPORT="${MCP_TRANSPORT:-sse}"
PORT="${MCP_PORT:-8001}"
HOST="${MCP_HOST:-0.0.0.0}"

echo "═══════════════════════════════════════════════════════"
echo "🔌 Mimir MCP Facade"
echo "═══════════════════════════════════════════════════════"
echo "  Web service : $SERVER_URL"
echo "  Transport   : $TRANSPORT  ($HOST:$PORT)"
echo "═══════════════════════════════════════════════════════"

# ── 1. Wait for the web service to become healthy ────────────────────────────
echo ""
echo "⏳ Waiting for web service at $SERVER_URL/health/ ..."
MAX_WAIT=120
ELAPSED=0
until curl -sf "$SERVER_URL/health/" > /dev/null 2>&1; do
    if [ "$ELAPSED" -ge "$MAX_WAIT" ]; then
        echo "❌ Web service did not become healthy after ${MAX_WAIT}s. Aborting."
        exit 1
    fi
    echo "   ... still waiting (${ELAPSED}s elapsed)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done
echo "✅ Web service is healthy"

# ── 2. Obtain a DRF token if one was not explicitly provided ─────────────────
if [ -z "$TOKEN" ]; then
    echo ""
    echo "🔑 Fetching auth token for user '$USER' ..."
    RESPONSE=$(curl -sf -X POST "$SERVER_URL/api/auth/token/" \
        -d "username=$USER&password=$PASSWORD" 2>&1) || {
        echo "❌ Token request failed: $RESPONSE"
        exit 1
    }
    TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null) || {
        echo "❌ Could not parse token from response: $RESPONSE"
        exit 1
    }
    echo "✅ Token obtained (${#TOKEN} chars)"
fi

# ── 3. Launch the facade server ──────────────────────────────────────────────
echo ""
echo "🚀 Starting MCP facade server ..."
echo "═══════════════════════════════════════════════════════"
exec python -m mcp_integration.facade.server \
    --token="$TOKEN" \
    --server="$SERVER_URL" \
    --transport="$TRANSPORT" \
    --host="$HOST" \
    --port="$PORT"
