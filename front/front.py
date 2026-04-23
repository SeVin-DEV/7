import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import uvicorn

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8080/chat")
FRONT_HOST = os.getenv("FRONT_HOST", "127.0.0.1")
FRONT_PORT = int(os.getenv("FRONT_PORT", "7860"))

app = FastAPI(title="Kayden Frontend")

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Kayden Web UI</title>
  <style>
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: #111;
      color: #eee;
    }
    .wrap {
      max-width: 900px;
      margin: 0 auto;
      padding: 16px;
    }
    h1 {
      margin: 0 0 12px 0;
      font-size: 1.4rem;
    }
    .status {
      font-size: 0.9rem;
      opacity: 0.8;
      margin-bottom: 14px;
    }
    #chatbox {
      border: 1px solid #333;
      background: #181818;
      border-radius: 10px;
      padding: 12px;
      min-height: 60vh;
      overflow-y: auto;
      white-space: pre-wrap;
    }
    .msg {
      margin: 10px 0;
      padding: 10px 12px;
      border-radius: 8px;
    }
    .user {
      background: #1f2a44;
    }
    .agent {
      background: #24351f;
    }
    .system {
      background: #333;
      color: #ccc;
      font-size: 0.95rem;
    }
    form {
      display: flex;
      gap: 8px;
      margin-top: 12px;
    }
    input[type=text] {
      flex: 1;
      padding: 12px;
      border-radius: 8px;
      border: 1px solid #444;
      background: #222;
      color: #fff;
    }
    button {
      padding: 12px 16px;
      border: 0;
      border-radius: 8px;
      background: #2d6cdf;
      color: #fff;
      cursor: pointer;
    }
    button:disabled {
      opacity: 0.6;
      cursor: wait;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Kayden Web UI</h1>
    <div class="status">Frontend → backend relay: <span id="backendLabel"></span></div>
    <div id="chatbox">
      <div class="msg system">Connected to frontend. Send a message.</div>
    </div>
    <form id="chatForm">
      <input id="msg" type="text" placeholder="Type a message..." autocomplete="off" />
      <button id="sendBtn" type="submit">Send</button>
    </form>
  </div>

  <script>
    const backendUrl = "/config";
    const chatbox = document.getElementById("chatbox");
    const form = document.getElementById("chatForm");
    const msg = document.getElementById("msg");
    const sendBtn = document.getElementById("sendBtn");
    const backendLabel = document.getElementById("backendLabel");

    async function init() {
      try {
        const r = await fetch(backendUrl);
        const data = await r.json();
        backendLabel.textContent = data.backend_url;
      } catch (e) {
        backendLabel.textContent = "unavailable";
      }
    }

    function addMessage(kind, text) {
      const div = document.createElement("div");
      div.className = "msg " + kind;
      div.textContent = text;
      chatbox.appendChild(div);
      chatbox.scrollTop = chatbox.scrollHeight;
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const value = msg.value.trim();
      if (!value) return;

      addMessage("user", "You: " + value);
      msg.value = "";
      sendBtn.disabled = true;

      try {
        const r = await fetch("/send", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ q: value })
        });
        const data = await r.json();
        if (!r.ok) {
          addMessage("system", "Error: " + (data.error || "request failed"));
        } else {
          addMessage("agent", "Kayden: " + (data.response || ""));
        }
      } catch (err) {
        addMessage("system", "Frontend error: " + err);
      } finally {
        sendBtn.disabled = false;
        msg.focus();
      }
    });

    init();
    msg.focus();
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return HTML

@app.get("/config")
async def config() -> JSONResponse:
    return JSONResponse({"backend_url": BACKEND_URL})

@app.post("/send")
async def send(request: Request) -> JSONResponse:
    payload = await request.json()
    q = str(payload.get("q", "")).strip()
    if not q:
        return JSONResponse({"error": "empty message"}, status_code=400)

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.get(BACKEND_URL, params={"q": q})
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return JSONResponse({"response": data.get("response", str(data))})
            return JSONResponse({"response": str(data)})
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=502)

if __name__ == "__main__":
    uvicorn.run(app, host=FRONT_HOST, port=FRONT_PORT)
