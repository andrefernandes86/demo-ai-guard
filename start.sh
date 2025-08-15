#!/usr/bin/env bash
set -e

echo "=== AI Guard Chat – Setup ==="
echo "This script will guide you through initial configuration."
echo

# Prompt for Ollama server
read -rp "Ollama server base URL (default: http://192.168.1.100:11434): " ollama_url
ollama_url=${ollama_url:-http://192.168.1.100:11434}

# Prompt for Ollama model
echo "Example models: llama3.1:8b, llama3:70b, mistral:7b"
read -rp "Ollama model tag (default: llama3.1:8b): " ollama_model
ollama_model=${ollama_model:-llama3.1:8b}

# Prompt for Vision One API key
echo "Your Trend Vision One API key is required to use AI Guard."
echo "Get it from: https://portal.xdr.trendmicro.com"
read -rp "Vision One API key: " v1_api_key

# Prompt for enforcement side
echo "Enforcement options:"
echo "  user      – block only on user prompt violations"
echo "  assistant – block only on assistant response violations"
echo "  both      – block on violations from either side"
read -rp "Enforce side (default: both): " enforce_side
enforce_side=${enforce_side:-both}

# Prompt for AI Guard URL (optional override)
read -rp "Vision One AI Guard API base URL (default: https://api.xdr.trendmicro.com/beta/aiSecurity/guard): " v1_guard_url
v1_guard_url=${v1_guard_url:-https://api.xdr.trendmicro.com/beta/aiSecurity/guard}

# Prompt for external port
read -rp "External port to publish AI Guard Chat (default: 8080): " ext_port
ext_port=${ext_port:-8080}

# Create .env file
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

# Optional knobs
V1_GUARD_CONFIDENCE_MIN=0.95
V1_GUARD_PROMPT_ATTACK_APPLIES=both

# External port
EXT_PORT=${ext_port}
EOF

echo
echo "Configuration saved to .env:"
echo "--------------------------------"
cat .env
echo "--------------------------------"
echo

# Update docker-compose.yml port mapping dynamically
if grep -q "EXT_PORT" docker-compose.yml; then
    echo "docker-compose.yml already configured for EXT_PORT."
else
    echo "Updating docker-compose.yml to use EXT_PORT..."
    sed -i.bak 's|"8080:8080"|"${EXT_PORT}:8080"|' docker-compose.yml
fi

# Start the container
echo "Starting AI Guard Chat..."
docker compose up -d --build

echo
echo "Done! Visit: http://localhost:${ext_port}"
echo "Health check: curl http://localhost:${ext_port}/healthz"
