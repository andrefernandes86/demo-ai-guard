import os
from typing import Dict, Any, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

APP_TITLE = "AI Guard – Chat"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.1.100:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# Vision One AI Guard config
V1_API_KEY = os.getenv("V1_API_KEY", "")
V1_GUARD_ENABLED = os.getenv("V1_GUARD_ENABLED", "false").lower() == "true"
V1_GUARD_DETAILED = os.getenv("V1_GUARD_DETAILED", "true").lower() == "true"
V1_GUARD_URL_BASE = os.getenv("V1_GUARD_URL_BASE", "https://api.xdr.trendmicro.com/beta/aiSecurity/guard")

# Enforce on both sides; any violation => block
ENFORCE_SIDE = os.getenv("ENFORCE_SIDE", "both")  # user | assistant | both

# Optional tuning knobs (kept for future use; not required by current normalize logic)
V1_GUARD_CONFIDENCE_MIN = float(os.getenv("V1_GUARD_CONFIDENCE_MIN", "0.0"))
V1_GUARD_PROMPT_ATTACK_APPLIES = os.getenv("V1_GUARD_PROMPT_ATTACK_APPLIES", "both")

app = FastAPI(title=APP_TITLE)

# CORS for local UI or other frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>AI Guard – Chat</title>
<style>
  :root { --bg:#0b1020; --card:#121a33; --muted:#96a0c8; --text:#e7ecff; --ok:#27c281; --bad:#ff5a73; --rev:#ffb020; }
  *{box-sizing:border-box} body{margin:0;background:#0b1020;color:var(--text);font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto}
  .wrap{max-width:900px;margin:32px auto;padding:0 16px}
  .title{font-size:22px;font-weight:700;margin-bottom:16px}
  .card{background:var(--card);border:1px solid #1c274c;border-radius:16px;padding:16px}
  .chat-box{height:520px;overflow:auto;border:1px solid #1c274c;border-radius:12px;padding:12px;background:#0e1530}
  .msg{margin:10px 0;padding:10px 12px;border-radius:10px;max-width:80%;position:relative}
  .me{background:#1e2a57; margin-left:auto}
  .bot{background:#162455}
  .meta{display:flex;gap:8px;align-items:center;margin-top:6px;font-size:12px;color:var(--muted)}
  .badge{display:inline-block;padding:3px 8px;border-radius:999px;font-size:11px;border:1px solid #2b3f7a}
  .ok{color:#dff7ec;border-color:#2b7a57;background:#123a2c}
  .bad{color:#ffe6ea;border-color:#7a2b3a;background:#3a1220}
  .rev{color:#fff1de;border-color:#7a5a2b;background:#3a2a12}
  .link{cursor:pointer;text-decoration:underline}
  .json{white-space:pre-wrap;background:#0a1330;border:1px solid #22346c;border-radius:10px;padding:8px;margin-top:6px;font-size:12px;color:#cfe1ff;display:none}
  .input-bar{display:flex;gap:8px;margin-top:10px}
  .input{flex:1;padding:12px;border-radius:12px;border:1px solid #263568;background:#0e1530;color:var(--text)}
  .btn{padding:10px 14px;border-radius:12px;border:1px solid #2b4076;background:#1a2a57;color:#fff;cursor:pointer}
  .muted{color:#96a0c8;font-size:13px}
</style>
</head>
<body>
<div class="wrap">
  <div class="title">AI Guard – Chat</div>
  <div class="card">
    <div class="muted">Model: <span id="model-name"></span></div>
    <div id="chat" class="chat-box"></div>
    <div class="input-bar">
      <input id="chat-input" class="input" placeholder="Ask the model…" />
      <button id="send" class="btn">Send</button>
    </div>
  </div>
</div>
<script>
const MODEL = "{{ model }}";
document.getElementById('model-name').textContent = MODEL;

const chatBox = document.getElementById('chat');
const input = document.getElementById('chat-input');
const sendBtn = document.getElementById('send');

let history = [];

function addMsg(role, content, guard) {
  const wrap = document.createElement('div');
  wrap.className = 'msg ' + (role === 'user' ? 'me' : 'bot');

  const text = document.createElement('div');
  text.textContent = content;
  wrap.appendChild(text);

  if (guard && guard.status) {
    const meta = document.createElement('div');
    meta.className = 'meta';

    let cls = 'ok';
    let label = 'OK';
    if (guard.decision === 'block') { cls = 'bad'; label = 'Blocked'; }
    else if (guard.decision === 'review') { cls = 'rev'; label = 'Review'; }

    const badge = document.createElement('span');
    badge.className = 'badge ' + cls;
    badge.textContent = 'AI Guard: ' + label;

    const link = document.createElement('span');
    link.className = 'link';
    link.textContent = 'details';

    const json = document.createElement('div');
    json.className = 'json';
    json.textContent = JSON.stringify(guard, null, 2);

    link.addEventListener('click', () => {
      json.style.display = (json.style.display === 'none' || json.style.display === '') ? 'block' : 'none';
    });

    meta.appendChild(badge);
    meta.appendChild(link);
    wrap.appendChild(meta);
    wrap.appendChild(json);
  }

  chatBox.appendChild(wrap);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  input.value = '';

  history.push({ role: 'user', content: text });
  addMsg('user', text, null);

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: history })
    });
    if (!resp.ok) throw new Error('Chat API error');
    const data = await resp.json();

    if (data.guard && data.guard.user) {
      chatBox.removeChild(chatBox.lastChild);
      addMsg('user', text, data.guard.user);
    }

    const reply = data.reply || '(no reply)';
    addMsg('assistant', reply, data.guard ? data.guard.assistant : null);

    history.push({ role: 'assistant', content: reply });
  } catch (e) {
    addMsg('assistant', 'Error: ' + e.message);
  }
}

sendBtn.addEventListener('click', sendMessage);
input.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMessage(); });
</script>
</body>
</html>
"""

# ------------------ AI Guard helpers ------------------

def _any_violation(items) -> bool:
    if not isinstance(items, list):
        return False
    for it in items:
        if isinstance(it, dict) and any(it.get(k) is True for k in ("content_violation","violation","leakage")):
            return True
    return False

def _block_on_any_violation(guard_json: dict) -> bool:
    if not isinstance(guard_json, dict):
        return False
    reason = str(guard_json.get("reason", "")).lower()

    if _any_violation(guard_json.get("harmful_content")):
        return True
    if _any_violation(guard_json.get("prompt_attack")) or _any_violation(guard_json.get("prompt_attacks")):
        return True
    if (_any_violation(guard_json.get("sensitive_info"))
        or _any_violation(guard_json.get("sensitive_content"))
        or _any_violation(guard_json.get("sensitive_information"))
        or _any_violation(guard_json.get("pii"))):
        return True

    if ("harmful content detected" in reason
        or "sensitive information detected" in reason
        or "prompt attack detected" in reason):
        return True
    return False

def _normalize_decision(guard_json: dict) -> str:
    if not isinstance(guard_json, dict):
        return "allow"
    if _block_on_any_violation(guard_json):
        return "block"
    action = str(guard_json.get("action", "")).lower()
    if action in {"review", "flag", "warn"}:
        return "review"
    return "allow"

def _v1_guard_scan(text: str) -> Optional[Dict[str, Any]]:
    if not V1_GUARD_ENABLED or not V1_API_KEY or not text:
        return None
    try:
        headers = {"Authorization": f"Bearer {V1_API_KEY}", "Content-Type": "application/json"}
        params = {"detailedResponse": str(V1_GUARD_DETAILED).lower()}
        payload = {"guard": text}
        r = requests.post(V1_GUARD_URL_BASE, headers=headers, params=params, json=payload, timeout=30)
        if r.status_code == 200:
            data = r.json()
            decision = _normalize_decision(data)
            return {"status": "ok", "decision": decision, **data}
        return {"status": "error", "decision": "review", "http_status": r.status_code, "text": r.text}
    except requests.RequestException as e:
        return {"status": "error", "decision": "review", "error": str(e)}

def _should_block(decision: str, side: str) -> bool:
    if decision != "block":
        return False
    if ENFORCE_SIDE == "both":
        return True
    return ENFORCE_SIDE == side

# ---------------------- Routes ----------------------

@app.get("/healthz")
def healthz():
    return {"status": "ok", "model": OLLAMA_MODEL, "v1_guard_enabled": V1_GUARD_ENABLED}

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE.replace("{{ model }}", OLLAMA_MODEL)

@app.post("/api/chat")
def chat(payload: Dict[str, Any]):
    messages = payload.get("messages", [])
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="Invalid messages")

    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break

    guard_user = _v1_guard_scan(last_user_msg) if last_user_msg else None
    if guard_user and _should_block(guard_user.get("decision", "allow"), "user"):
        return JSONResponse({
            "reply": "[Blocked by AI Guard]",
            "guard": {"user": guard_user, "assistant": None},
            "blocked": "user"
        })

    try:
        r = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
            timeout=120
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama not reachable: {e}")
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Ollama error: {r.text}")

    data = r.json()
    assistant_text = data.get("message", {}).get("content", "")

    guard_asst = _v1_guard_scan(assistant_text) if assistant_text else None
    if guard_asst and _should_block(guard_asst.get("decision", "allow"), "assistant"):
        return JSONResponse({
            "reply": "[Blocked by AI Guard]",
            "guard": {"user": guard_user, "assistant": guard_asst},
            "blocked": "assistant"
        })

    return JSONResponse({
        "reply": assistant_text,
        "guard": {"user": guard_user, "assistant": guard_asst},
        "blocked": None
    })
