#!/bin/bash
# Test the HTTP MCP server with curl
# First start the server:  python http_server.py

URL="http://localhost:8000/mcp"
CT="-H Content-Type:application/json"
ACCEPT="-H Accept:application/json,text/event-stream"

# Helper: POST a JSON-RPC request, extract the data from the SSE response, pretty-print
mcp_call() {
  curl -s -X POST "$URL" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d "$1" \
    | grep '^data: ' | sed 's/^data: //' | python3 -m json.tool
}

echo "============================================================"
echo "  MCP HTTP Server Test — curl edition"
echo "============================================================"
echo
echo "  Server: $URL"
echo

# --- Initialize (silent) ---
mcp_call '{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "capabilities": {},
    "clientInfo": { "name": "curl-test", "version": "1.0" }
  },
  "id": 1
}' > /dev/null

curl -s -X POST "$URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "notifications/initialized"}' > /dev/null

# --- Discover tools ---
echo "--- tools/list ---"
echo
mcp_call '{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 2
}'
echo

# --- Call: get_coordinates ---
echo "--- tools/call: get_coordinates(location=proxima) ---"
echo
mcp_call '{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_coordinates",
    "arguments": { "location": "proxima" }
  },
  "id": 3
}'
echo

# --- Call: plot_course ---
echo "--- tools/call: plot_course(origin=earth, destination=proxima) ---"
echo
mcp_call '{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "plot_course",
    "arguments": { "origin": "earth", "destination": "proxima" }
  },
  "id": 4
}'
echo

# --- Call: nearby_objects ---
echo "--- tools/call: nearby_objects(sector=Alpha-1, radius=5.0) ---"
echo
mcp_call '{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "nearby_objects",
    "arguments": { "sector": "Alpha-1", "radius": 5.0 }
  },
  "id": 5
}'
echo

echo "============================================================"
echo "  Done. All requests were plain HTTP POST with JSON-RPC."
echo "============================================================"
