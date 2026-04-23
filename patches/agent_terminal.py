import subprocess
from typing import Any, Dict


def execute_terminal(command: str) -> str:
    """Execute a shell command through the patch layer."""
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


def _register(app: Any) -> str:
    """Register patch readiness on the app without monkey-patching routes."""
    if not hasattr(app.state, "agent_terminal_ready"):
        app.state.agent_terminal_ready = True

    # Expose helper for any later internal use.
    setattr(app, "execute_terminal", execute_terminal)

    if not hasattr(app, "extra_instructions"):
        app.extra_instructions = []

    marker = "PATCH_ACTIVE: agent_terminal"
    if marker not in app.extra_instructions:
        app.extra_instructions.append(marker)

    return "PATCH_READY: agent_terminal online."


def handle(app: Any, payload: Dict[str, Any] | None = None) -> str:
    """
    Patch entrypoint for the current bus/bridge architecture.

    Supported payloads:
    - {"action": "init"}
    - {"action": "status"}
    - {"action": "execute_command", "command": "pwd"}
    - {"action": "exec", "command": "ls -la"}
    """
    payload = payload or {}
    _register(app)

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
    Backward-compatible shim for older patch loaders.
    The current system should call handle(app, payload) instead.
    """
    return _register(app)
