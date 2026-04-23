import importlib.util
import os
import subprocess


ACTIVE_PATCHES = {}


def initialize_bus(app, manifest):
    """
    Registers patch route awareness and caches patch file paths for routing.
    """
    global ACTIVE_PATCHES
    ACTIVE_PATCHES.clear()

    patch_names = manifest.split(",") if manifest else []
    for name in patch_names:
        path = f"patches/{name}.py"
        if os.path.exists(path):
            ACTIVE_PATCHES[name] = path

    if not hasattr(app, "extra_instructions"):
        app.extra_instructions = []

    app.extra_instructions.append(
        f"PATCH_BUS_ACTIVE: Terminal Access Enabled | Modules: [{manifest}]"
    )


def _load_patch_module(patch_name):
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


def route(app, patch_name, payload=None):
    """
    Routes traffic from main into a specific patch module.
    Intended for handoff into lazy capability layers like tool_driver.
    """
    try:
        module = _load_patch_module(patch_name)
        if not hasattr(module, "handle"):
            return f"PATCH_ROUTE_ERROR: '{patch_name}' missing handle(app, payload)"
        return module.handle(app, payload or {})
    except Exception as e:
        return f"PATCH_ROUTE_ERROR: {str(e)}"


def call(command):
    """
    Executes shell commands safely through controlled subprocess layer.
    """

    if not command or not isinstance(command, str):
        return "EXEC_ERROR: Invalid command input."

    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=15
        )

        if result.returncode != 0:
            return f"EXEC_ERROR: {result.stderr.strip()}"

        return result.stdout.strip() or "Success (No Output)."

    except subprocess.TimeoutExpired:
        return "EXEC_ERROR: Command timed out."

    except Exception as e:
        return f"EXEC_ERROR: {str(e)}"
