# AI Guard Chat


AI Guard Chat is a minimal FastAPI application that integrates with:
- **Ollama** for local or remote LLM inference
- **Trend Vision One AI Guard** for detecting and blocking malicious or unsafe prompts/responses

The app lets you chat with an LLM while automatically scanning both your **prompts** and the **model's responses** using Trend Vision One's AI Guard API.

<p align="center">
  <img src="https://github.com/andrefernandes86/demo-ai-guard/blob/main/ai0guard.png" alt="AI Guard" width="600">
</p>

## Features

- 🚀 **Easy Deployment** – Single container with configurable `.env`
- 🛡 **AI Guard Integration** – Uses Trend Vision One's AI Guard to assess safety
- ⚙ **Customizable Enforcement** – Block unsafe user prompts, model responses, or both
- 🌐 **Remote Ollama Support** – Point to a local or remote Ollama server
- 📊 **Health Endpoint** – `/healthz` for service status and configuration

---

## Quick Start

Make the script executable and run it:

```bash
chmod +x start.sh
./start.sh
```

The script will guide you through:
1. Entering your Ollama server URL and model name
2. Entering your **Trend Vision One API key**
3. Choosing the enforcement side (user / assistant / both)
4. Selecting the external port to publish the chat app

When done, `.env` will be created and the app will start.

---

## Manual Run

If you prefer to set values manually:

```bash
cp .env.example .env
# edit the .env file with your details
docker compose up -d --build
```

---

## Access

- **Chat UI:** `http://localhost:<EXT_PORT>`
- **Health:** `http://localhost:<EXT_PORT>/healthz`

---

## API Endpoints

| Method | Path       | Description |
|--------|-----------|-------------|
| GET    | `/`       | HTML chat UI |
| GET    | `/healthz`| Service health and config |
| POST   | `/api/chat` | Chat with guard scanning |

**Example request body for `/api/chat`:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ]
}
```

---

## Environment Variables

| Variable             | Description |
|----------------------|-------------|
| OLLAMA_BASE_URL      | Base URL of the Ollama server |
| OLLAMA_MODEL         | Model tag to use |
| V1_API_KEY           | Trend Vision One API key |
| V1_GUARD_ENABLED     | Enable/disable AI Guard scanning (true/false) |
| V1_GUARD_DETAILED    | Request detailed AI Guard results (true/false) |
| V1_GUARD_URL_BASE    | AI Guard API endpoint |
| ENFORCE_SIDE         | Which side to enforce blocking: user, assistant, or both |
| EXT_PORT             | External port for chat UI |
