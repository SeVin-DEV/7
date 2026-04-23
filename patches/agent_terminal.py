import subprocess
from types import SimpleNamespace
from typing import Any, Dict


def execute_terminal(command: str) -> str:
    if not command or not isinstance(command, str):
        return "EXEC_ERROR: Invalid command input."

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
        )

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()

        if result.returncode == 0:
            return stdout if stdout else "Success (No Output)."
        return f"EXEC_ERROR [Code {result.returncode}]: {stderr or 'Command failed.'}"

    except subprocess.TimeoutExpired:
        return "EXEC_ERROR: Command timed out after 15s."
    except Exception as e:
        return f"EXEC_ERROR: {e}"


def boot(app: Any, bridge: Any) -> str:
    """
    Startup patch contract.

    This patch:
    - comes online at boot
    - registers the EXEC hook with the patch bridge
    - exposes terminal capability as a system function
    """
    if not hasattr(app, "state") or app.state is None:
        app.state = SimpleNamespace()

    if not hasattr(app.state, "agent_terminal_ready"):
        app.state.agent_terminal_ready = True

    setattr(app, "execute_terminal", execute_terminal)

    if not hasattr(app, "extra_instructions"):
        app.extra_instructions = []

    marker = "PATCH_ACTIVE: agent_terminal"
    if marker not in app.extra_instructions:
        app.extra_instructions.append(marker)

    if hasattr(bridge, "register_exec_handler"):
        bridge.register_exec_handler(execute_terminal)

    return "PATCH_READY: agent_terminal online."


def handle(app: Any, payload: Dict[str, Any] | None = None) -> str:
    """
    Optional compatibility route.

    Not required for normal EXEC use, but retained so the module can still be
    queried or manually routed if needed.
    """
    payload = payload or {}
    action = str(payload.get("action", "status")).strip().lower()

    if action in {"init", "install", "ensure_online", "status"}:
        return "PATCH_READY: agent_terminal online."

    if action in {"execute_command", "exec", "run"}:
        command = payload.get("command") or payload.get("cmd")
        if not command:
            return "PATCH_ERROR: Missing command."
        return execute_terminal(str(command))

    return f"PATCH_ERROR: Unsupported action '{action}'."


def patch(app: Any) -> str:
    """
    Backward-compatible shim if an older bootloader still calls patch(app).
    """
    class _BridgeShim:
        def register_exec_handler(self, handler):
            return None

    return boot(app, _BridgeShim())
