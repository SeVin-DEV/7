import importlib.util
import os
from typing import Any, Dict


PATCH_BRIDGE_PATH = "patches/patches_bridge.py"


def _load_module_from_path(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec from {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def initialize_patch_bus(app) -> Any:
    """
    Startup-only infrastructure driver for the patch bridge/bus route.
    Loads the patch bridge, mounts it to the app, and initializes bridge context.
    """
    if getattr(app.state, "patch_bus_ready", False) and hasattr(app, "patches_bus"):
        return app.patches_bus

    if not os.path.exists(PATCH_BRIDGE_PATH):
        raise FileNotFoundError(f"Missing patch bridge: {PATCH_BRIDGE_PATH}")

    manifest = os.getenv("SVN_ACTIVE_PATCHES", "")
    module = _load_module_from_path(PATCH_BRIDGE_PATH, "patches_bridge")

    if not hasattr(module, "call"):
        raise RuntimeError("patches_bridge.py missing required call(command) function")

    setattr(app, "patches_bus", module)

    if hasattr(module, "initialize_bus"):
        module.initialize_bus(app, manifest)

    app.state.patch_bus_ready = True
    app.state.patch_manifest = manifest
    return module


def route_exec_request(app, command: str) -> str:
    initialize_patch_bus(app)
    return app.patches_bus.call(command)


def route_tool_request(app, tool_name: str, args: Dict[str, Any] | None = None) -> str:
    initialize_patch_bus(app)

    if not hasattr(app.patches_bus, "route"):
        return "ROUTE_ERROR: Patch bridge missing route(app, patch_name, payload)"

    payload = {
        "action": "execute_tool",
        "tool_name": tool_name,
        "args": args or {},
    }
    return app.patches_bus.route(app, "tool_driver", payload)
