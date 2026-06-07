# start-agent.ps1 — sets up and launches the Bytebot computer agent on Windows.
# Right-click this file -> "Run with PowerShell", or in PowerShell run:  .\start-agent.ps1
#
# It checks Docker, downloads the agent the first time, asks for your Anthropic
# API key once, starts everything, and opens http://localhost:9992

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$bytebot = Join-Path $here "bytebot"

Write-Host "==> Checking Docker..."
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Host ""
  Write-Host "Docker isn't installed (or isn't running)."
  Write-Host "1) Install Docker Desktop:  https://www.docker.com/products/docker-desktop/"
  Write-Host "2) Open Docker Desktop and wait until it says 'running'."
  Write-Host "3) Run this script again."
  exit 1
}

Write-Host "==> Getting the agent..."
if (-not (Test-Path $bytebot)) {
  git clone --depth 1 https://github.com/bytebot-ai/bytebot.git $bytebot
} else {
  Write-Host "    already downloaded."
}

$envFile = Join-Path $bytebot "docker\.env"
if (-not ((Test-Path $envFile) -and (Select-String -Path $envFile -Pattern "ANTHROPIC_API_KEY=sk-" -Quiet))) {
  Write-Host ""
  Write-Host "==> I need your Anthropic API key (starts with sk-ant-...)."
  Write-Host "    Get one at https://console.anthropic.com  ->  API Keys."
  $key = Read-Host "    Paste it here and press Enter"
  "ANTHROPIC_API_KEY=$key" | Out-File -Encoding ascii $envFile
  Write-Host "    Saved."
}

Write-Host "==> Starting the agent (first time takes 2-3 minutes to download)..."
docker compose -f (Join-Path $bytebot "docker\docker-compose.yml") up -d

Write-Host ""
Write-Host "============================================================"
Write-Host " Your computer agent is running."
Write-Host ""
Write-Host "    Open this in your browser:   http://localhost:9992"
Write-Host ""
Write-Host " Type a task there in plain English and watch it work."
Write-Host " To stop it later:  docker compose -f bytebot\docker\docker-compose.yml down"
Write-Host "============================================================"
Start-Process "http://localhost:9992"
