#!/usr/bin/env bash
# stop-agent.sh — stops the Bytebot computer agent.  Run:  bash stop-agent.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
if docker compose version >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi
$DC -f "$HERE/bytebot/docker/docker-compose.yml" down
echo "✅ Agent stopped. Start it again any time with:  bash start-agent.sh"
