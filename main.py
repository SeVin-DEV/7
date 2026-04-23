import os

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from core.engine import run_cognitive_cycle
from core.patch_bus_driver import initialize_patch_bus, route_exec_request, route_tool_request

from openai import OpenAI


app = FastAPI()


# =========================
# 🌱 ENVIRONMENT LOAD
# =========================

def load_environment():
    load_dotenv()
    required = ["MODEL_NAME"]
    for var in required:
        if not os.getenv(var):
            print(f"[ENV WARNING] Missing {var}")
    print("[ENV] Loaded.")


# =========================
# 🤖 LLM CLIENT INIT
# =========================

def init_llm_client(app_instance):
    """
    Initializes an OpenAI-compatible client.
    Works with:
    - OpenAI
    - LM Studio
    - Ollama (via proxy)
    - Custom endpoints
    """
    api_key = os.getenv("API_KEY", "none")
    base_url = os.getenv("API_BASE_URL", "http://localhost:1234/v1")
    model = os.getenv("MODEL_NAME")

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    except Exception as e:
        print(f"Client initialization failed: {e}")
        client = None

    try:
        if not model:
            raise Exception("MODEL_NAME not set")

        app_instance.state.client = client
        print(f"[BOOT] LLM client ready → {base_url} | model={model}")

    except Exception as e:
        print(f"[BOOT ERROR] LLM init failed: {e}")
        app_instance.state.client = None


# =========================
# 🚦 REQUEST ROUTER
# =========================

def bind_request_router(app_instance):
    app_instance.route_exec_request = lambda command: route_exec_request(app_instance, command)
    app_instance.route_tool_request = lambda tool_name, args=None: route_tool_request(app_instance, tool_name, args)
    print("[BOOT] Main switchboard routes bound")


# =========================
# 🚀 STARTUP
# =========================

@app.on_event("startup")
async def startup_event():
    print("[SYSTEM] Boot sequence initiated")
    load_environment()
    init_llm_client(app)
    initialize_patch_bus(app)
    bind_request_router(app)
    print("[SYSTEM] Online")


# =========================
# 💬 CHAT ENDPOINT
# =========================

@app.get("/chat")
async def chat(q: str = Query(...)):
    try:
        client = getattr(app.state, "client", None)

        if client is None:
            return JSONResponse({
                "error": "LLM client not initialized"
            })

        response, _ = await run_cognitive_cycle(app, client, q)

        return JSONResponse({
            "response": response
        })

    except Exception as e:
        return JSONResponse({
            "error": f"KERNEL_EXCEPTION: {str(e)}"
        })


# =========================
# ❤️ HEALTH
# =========================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": os.getenv("MODEL_NAME"),
        "base_url": os.getenv("API_BASE_URL"),
        "tools": os.getenv("SVN_ACTIVE_TOOLS"),
        "patches": os.getenv("SVN_ACTIVE_PATCHES"),
        "patch_bus_ready": getattr(app.state, "patch_bus_ready", False),
        "tool_bus_ready": getattr(app.state, "tool_bus_ready", False)
    }
