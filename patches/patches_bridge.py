import importlib.util
import os
import subprocess
from types import SimpleNamespace
from typing import Any, Callable, Dict

ACTIVE_PATCHES: Dict[str, str] = {}
LOADED_PATCHES: Dict[str, Any] = {}
EXEC_HANDLER: Callable[[str], str] | None = None


class BridgeAPI:
    """Runtime bridge object passed into startup patches at boot."""

    def register_exec_handler(self, handler: Callable[[str], str]) -> None:
        global EXEC_HANDLER
        EXEC_HANDLER = handler

    def clear_exec_handler(self) -> None:
        global EXEC_HANDLER
        EXEC_HANDLER = None

    def get_loaded_patch_names(self) -> list[str]:
        return sorted(LOADED_PATCHES.keys())

    def get_active_patch_names(self) -> list[str]:
        return sorted(ACTIVE_PATCHES.keys())


BRIDGE = BridgeAPI()


def _ensure_app_state(app: Any) -> None:
    if not hasattr(app, "state") or app.state is None:
        app.state = SimpleNamespace()

    if not hasattr(app, "extra_instructions"):
        app.extra_instructions = []


def _load_patch_module(patch_name: str):
    patch_name = (patch_name or "").replace(".py", "").strip()
    if not patch_name:
        raise ValueError("Missing patch name")

    path = ACTIVE_PATCHES.get(patch_name) or f"patches/{patch_name}.py"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Patch not found: {patch_name}")

    spec = importlib.util.spec_from_file_location(f"patch_{patch_name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load patch: {patch_name}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _boot_patch(app: Any, patch_name: str):
    module = _load_patch_module(patch_name)
    LOADED_PATCHES[patch_name] = module

    if hasattr(module, "boot"):
        module.boot(app, BRIDGE)
    elif hasattr(module, "patch"):
        module.patch(app)

    return module


def initialize_bus(app: Any, manifest: str) -> None:
    """
    Boot-time patch initialization.

    Behavior:
    - discovers active patches from manifest
    - imports every patch module at startup
    - runs boot(app, bridge) or patch(app) once
    - lets startup patches register system hooks like EXEC
    """
    global EXEC_HANDLER

    _ensure_app_state(app)
    ACTIVE_PATCHES.clear()
    LOADED_PATCHES.clear()
    EXEC_HANDLER = None

    patch_names = [name.strip() for name in (manifest or "").split(",") if name.strip()]
    errors: Dict[str, str] = {}

    for name in patch_names:
        path = f"patches/{name}.py"
        if os.path.exists(path):
            ACTIVE_PATCHES[name] = path

    for name in list(ACTIVE_PATCHES.keys()):
        try:
            _boot_patch(app, name)
        except Exception as e:
            errors[name] = str(e)

    app.state.active_patches = sorted(ACTIVE_PATCHES.keys())
    app.state.loaded_patches = sorted(LOADED_PATCHES.keys())
    app.state.patch_boot_errors = errors

    marker = (
        "PATCH_BUS_ACTIVE: Startup Patches Loaded | Active: "
        f"[{",".join(sorted(ACTIVE_PATCHES.keys()))}]"
    )
    if marker not in app.extra_instructions:
        app.extra_instructions.append(marker)

    if errors:
        app.extra_instructions.append(
            "PATCH_BOOT_ERRORS: " + ", ".join(f"{k}={v}" for k, v in errors.items())
        )


def route(app: Any, patch_name: str, payload: Dict[str, Any] | None = None):
    """
    Internal routed patch path.

    Kept intact for infrastructure patches like tool_driver.
    """
    try:
        module = LOADED_PATCHES.get(patch_name) or _load_patch_module(patch_name)
        if patch_name not in LOADED_PATCHES:
            LOADED_PATCHES[patch_name] = module

        if not hasattr(module, "handle"):
            return f"PATCH_ROUTE_ERROR: {patch_name!r} missing handle(app, payload)"

        return module.handle(app, payload or {})
    except Exception as e:
        return f"PATCH_ROUTE_ERROR: {str(e)}"


def _legacy_exec(command: str) -> str:
    if not command or not isinstance(command, str):
        return "EXEC_ERROR: Invalid command input."

    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=15,
        )
        if result.returncode != 0:
            return f"EXEC_ERROR: {(result.stderr or "").strip()}"
        return (result.stdout or "").strip() or "Success (No Output)."
    except subprocess.TimeoutExpired:
        return "EXEC_ERROR: Command timed out."
    except Exception as e:
        return f"EXEC_ERROR: {str(e)}"


def call(command: str) -> str:
    """
    EXEC hook path.

    If a startup patch registered an exec handler at boot, use it.
    Otherwise fall back to the legacy direct subprocess path.
    """
    if EXEC_HANDLER is not None:
        try:
            return EXEC_HANDLER(command)
        except Exception as e:
            return f"EXEC_ERROR: {str(e)}"

    return _legacy_exec(command)
