#!/usr/bin/env bash
set -euo pipefail

echo "=== AI Guard Chat – Setup ==="
echo "This script will guide you through initial configuration."
echo

# 1) Prompt for Ollama server (can be remote IP)
read -rp "Ollama server base URL (e.g., http://192.168.1.77:11434) [default: http://192.168.1.100:11434]: " ollama_url
ollama_url=${ollama_url:-http://192.168.1.100:11434}

# 2) Prompt for model
echo "Examples: llama3.1:8b, llama3:70b, mistral:7b, qwen2.5:7b"
read -rp "Ollama model tag [default: llama3.1:8b]: " ollama_model
ollama_model=${ollama_model:-llama3.1:8b}

# 3) Vision One API key
echo "Your Trend Vision One API key is required to use AI Guard."
read -rp "Vision One API key: " v1_api_key

# 4) Enforcement side
echo "Enforcement options:"
echo "  user      – block only on user prompt violations"
echo "  assistant – block only on assistant response violations"
echo "  both      – block on violations from either side"
read -rp "Enforce side [default: both]: " enforce_side
enforce_side=${enforce_side:-both}

# 5) Optional: override AI Guard base URL
read -rp "Vision One AI Guard API base URL [default: https://api.xdr.trendmicro.com/beta/aiSecurity/guard]: " v1_guard_url
v1_guard_url=${v1_guard_url:-https://api.xdr.trendmicro.com/beta/aiSecurity/guard}

# 6) External port for users to access the chat
read -rp "External port to publish AI Guard Chat [default: 8080]: " ext_port
ext_port=${ext_port:-8080}

echo
echo ">>> Validating Ollama server connectivity..."
if ! curl -fsS "${ollama_url}/api/tags" >/tmp/ollama_tags.json 2>/dev/null; then
  echo "ERROR: Could not reach ${ollama_url}."
  echo "Check IP, port, firewall, and that Ollama is running."
  exit 1
fi
echo "OK: ${ollama_url} is reachable."

echo ">>> Checking if model '${ollama_model}' exists on the Ollama server..."
if grep -q "\"name\"[[:space:]]*:[[:space:]]*\"${ollama_model}\"" /tmp/ollama_tags.json; then
  echo "OK: Model '${ollama_model}' found."
else
  echo "WARN: Model '${ollama_model}' not found in /api/tags."
  echo "Pull it on that host:  ollama pull ${ollama_model}"
fi

# 7) Write .env
cat > .env <<EOF
# Ollama
OLLAMA_BASE_URL=${ollama_url}
OLLAMA_MODEL=${ollama_model}

# Trend Vision One AI Guard
V1_GUARD_ENABLED=true
V1_GUARD_DETAILED=true
V1_API_KEY=${v1_api_key}
V1_GUARD_URL_BASE=${v1_guard_url}

# Enforcement
ENFORCE_SIDE=${enforce_side}

# External port
EXT_PORT=${ext_port}
EOF

echo
echo "Configuration saved to .env:"
echo "--------------------------------"
cat .env
echo "--------------------------------"
echo

# 8) Start the container
echo "Starting AI Guard Chat with docker compose..."
docker compose up -d --build

# 9) Health check
echo
echo "Waiting for the app to become ready..."
sleep 2
if curl -fsS "http://localhost:${ext_port}/healthz" >/tmp/aiguard_health.json 2>/dev/null; then
  echo "Health:"
  cat /tmp/aiguard_health.json
  echo
  echo "Open: http://localhost:${ext_port}"
else
  echo "The app is starting, but /healthz was not reachable yet."
fi
