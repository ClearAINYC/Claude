#!/usr/bin/env bash
#
# start-agent.sh — sets up and launches the Bytebot computer agent.
# macOS / Linux. Just run:  bash start-agent.sh
#
# It will: check Docker is installed, download the agent the first time,
# ask for your Anthropic API key once, start everything, and open the
# control panel in your browser at http://localhost:9992
#
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
BYTEBOT_DIR="$HERE/bytebot"

# Use "docker compose" (new) or "docker-compose" (old), whichever exists.
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  DC=""
fi

echo "==> Checking Docker..."
if ! command -v docker >/dev/null 2>&1 || [ -z "$DC" ]; then
  echo
  echo "Docker isn't installed (or isn't running)."
  echo "1) Install Docker Desktop:  https://www.docker.com/products/docker-desktop/"
  echo "2) Open the Docker Desktop app and wait until it says 'running'."
  echo "3) Run this script again."
  exit 1
fi

echo "==> Getting the agent..."
if [ ! -d "$BYTEBOT_DIR" ]; then
  git clone --depth 1 https://github.com/bytebot-ai/bytebot.git "$BYTEBOT_DIR"
else
  echo "    already downloaded."
fi

ENV_FILE="$BYTEBOT_DIR/docker/.env"
if ! grep -q "ANTHROPIC_API_KEY=sk-" "$ENV_FILE" 2>/dev/null; then
  echo
  echo "==> I need your Anthropic API key (starts with sk-ant-...)."
  echo "    Get one at https://console.anthropic.com  ->  API Keys."
  printf "    Paste it here and press Enter: "
  read -r KEY
  echo "ANTHROPIC_API_KEY=${KEY}" > "$ENV_FILE"
  echo "    Saved."
fi

echo "==> Starting the agent (first time takes 2-3 minutes to download)..."
$DC -f "$BYTEBOT_DIR/docker/docker-compose.yml" up -d

echo
echo "============================================================"
echo " ✅ Your computer agent is running."
echo
echo "    Open this in your browser:   http://localhost:9992"
echo
echo " Type a task there in plain English and watch it work."
echo " To stop it later, run:  bash stop-agent.sh"
echo "============================================================"

# Try to open the browser automatically.
( command -v open >/dev/null 2>&1 && open http://localhost:9992 ) || \
( command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:9992 ) || true
