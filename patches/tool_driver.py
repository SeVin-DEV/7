import importlib.util
import os
from typing import Any, Dict


TOOLS_BRIDGE_PATH = "tools/tools_bridge.py"


def _load_module_from_path(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec from {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_tool_bus(app):
    """
    Lazy bus driver patch.
    It only brings the tools bridge online when a request is actually routed here.
    """
    if getattr(app.state, "tool_bus_ready", False) and hasattr(app, "tools_bus"):
        return app.tools_bus

    if not os.path.exists(TOOLS_BRIDGE_PATH):
        raise FileNotFoundError(f"Missing tools bridge: {TOOLS_BRIDGE_PATH}")

    manifest = os.getenv("SVN_ACTIVE_TOOLS", "")
    module = _load_module_from_path(TOOLS_BRIDGE_PATH, "tools_bridge")

    if not hasattr(module, "call"):
        raise RuntimeError("tools_bridge.py missing required call(tool_name, args) function")

    setattr(app, "tools_bus", module)

    if hasattr(module, "initialize_bus"):
        module.initialize_bus(app, manifest)

    app.state.tool_bus_ready = True
    app.state.tool_manifest = manifest
    return module


def handle(app, payload: Dict[str, Any] | None = None):
    payload = payload or {}
    action = payload.get("action", "ensure_online")

    bus = ensure_tool_bus(app)

    if action == "ensure_online":
        return f"TOOL_BUS_READY: [{getattr(app.state, 'tool_manifest', '')}]"

    if action == "execute_tool":
        tool_name = payload.get("tool_name")
        args = payload.get("args", {}) or {}
        return bus.call(tool_name, args)

    return f"TOOL_DRIVER_ERROR: Unsupported action '{action}'"
