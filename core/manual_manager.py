import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

TOOLS_DIR = Path("tools")


def extract_logic_context(file_path: Path) -> Tuple[str, List[str]]:
    """
    Read a tool source file and derive a lightweight manual from its docstring
    and public function names.
    """
    try:
        content = file_path.read_text(encoding="utf-8")

        doc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        purpose = (
            doc_match.group(1).strip()
            if doc_match
            else "Autonomous tool; purpose not explicitly defined in source docstring."
        )

        functions = re.findall(r'^def\s+(\w+)\(', content, re.MULTILINE)
        capabilities = [f"- **{func}**" for func in functions if not func.startswith("_")]
        return purpose, capabilities
    except Exception as exc:
        return f"Error extracting context: {exc}", []


def _manual_path(tool_name: str) -> Path:
    return TOOLS_DIR / f"{tool_name}.md"


def _tool_path(tool_name: str) -> Path:
    return TOOLS_DIR / f"{tool_name}.py"


def _build_manual_text(tool_name: str, purpose: str, capabilities: List[str]) -> str:
    cap_list = "\n".join(capabilities) if capabilities else "- No primary functions detected."
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# {tool_name}.py Manual
*Last System Audit: {timestamp}*

## Purpose
{purpose}

## Capabilities
{cap_list}

## Execution Logic
1. The cognitive engine asks for the tool by name.
2. `audit_tool_specs()` returns this manual text to the engine.
3. The model uses the manual to format a `USE_TOOL:` command.
4. `tools/tools_bridge.py` imports the tool module and calls `run(args)`.

## Expected Runtime Contract
- File path: `tools/{tool_name}.py`
- Entry point: `run(args: dict)`
- Return: string, dict, or JSON-serializable result
"""


def audit_tool_specs(tool_name: str):
    """
    7-1 engine contract:
    returns (manual_data, status)

    - manual_data: {"manual_text": "..."}
    - status: "SUCCESS" | "FAIL"
    """
    if not tool_name:
        return None, "FAIL"

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    tool_path = _tool_path(tool_name)
    manual_path = _manual_path(tool_name)

    if not tool_path.exists():
        return None, "FAIL"

    if not manual_path.exists():
        purpose, capabilities = extract_logic_context(tool_path)
        manual_text = _build_manual_text(tool_name, purpose, capabilities)
        manual_path.write_text(manual_text, encoding="utf-8")

    try:
        manual_text = manual_path.read_text(encoding="utf-8").strip()
        return {"manual_text": manual_text}, "SUCCESS"
    except Exception:
        return None, "FAIL"


def run_sweep() -> List[Dict[str, str]]:
    """
    Legacy utility retained for bulk manual generation.
    Returns a summary list instead of printing only, so it can be reused.
    """
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    generated = []

    for script in sorted(TOOLS_DIR.glob("*.py")):
        if script.name == "tools_bridge.py":
            continue

        manual_path = script.with_suffix(".md")
        if manual_path.exists():
            continue

        purpose, capabilities = extract_logic_context(script)
        manual_text = _build_manual_text(script.stem, purpose, capabilities)
        manual_path.write_text(manual_text, encoding="utf-8")
        generated.append({"tool": script.stem, "manual": manual_path.name})

    return generated


if __name__ == "__main__":
    for item in run_sweep():
        print(f"[SYSTEM] Auto-generated manual for {item['tool']}")
