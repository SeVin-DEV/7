import os
import json
from core.persistence import get_identity_content, load_json, save_json
from core.manual_manager import audit_tool_specs
from core.belief_graph import resolve_conflicts, prune_low_value_nodes

MAX_CYCLES = 4

def parse_tool_call(raw: str):
    """Parses: USE_TOOL: tool_name | key=value"""
    try:
        payload = raw.split(":", 1)[1].strip()
        if "|" in payload:
            name, arg_str = payload.split("|", 1)
            args = {k.strip(): v.strip() for pair in arg_str.split(",") if "=" in pair for k, v in [pair.split("=", 1)]}
            return name.strip(), args
        return payload.strip(), {}
    except Exception:
        return None, {}

async def run_cognitive_cycle(app, client, user_input):
    """
    THE 26ai COGNITIVE CORE (v5.0)
    Wired for Oracle Autonomous Database persistence.
    """
    try:
        # === LOAD STATE FROM 26ai BRAIN ===
        # We now pass table names instead of filenames.
        history = load_json("chat_history", [])
        beliefs = load_json("belief_graph", {})
        
        # 'soul' is the key in our identity_matrix table
        identity = get_identity_content("soul")

        patches = os.getenv("SVN_ACTIVE_PATCHES", "None")
        tools = os.getenv("SVN_ACTIVE_TOOLS", "None")

        # === MAINTENANCE ===
        beliefs = resolve_conflicts(beliefs)
        beliefs = prune_low_value_nodes(beliefs)

        # === BUILD WORKING CONTEXT ===
        working_messages = [
            {
                "role": "system",
                "content": f"{identity}\n\n[ACTIVE_PATCHES]\n{patches}\n\n[AVAILABLE_TOOLS]\n{tools}\n\n[KNOWN_BELIEFS]\n{json.dumps(beliefs, indent=2)}"
            },
            *history[-6:],
            {"role": "user", "content": user_input}
        ]

        final_answer = None
        last_msg = None

        # === COGNITIVE LOOP ===
        for _ in range(MAX_CYCLES):
            res = client.chat.completions.create(
                model=os.getenv("MODEL_NAME"),
                messages=working_messages,
                temperature=0.3
            )

            msg = res.choices[0].message.content.strip()
            last_msg = msg
            working_messages.append({"role": "assistant", "content": msg})

            # --- DECISION TREE ---
            if msg.startswith("NEED_TOOL:"):
                tool_name = msg.split(":", 1)[-1].strip().replace(".py", "")
                manual_data, status = audit_tool_specs(tool_name)
                if status != "SUCCESS":
                    final_answer = f"CPU_HALT: Tool '{tool_name}' unavailable."
                    break
                working_messages.append({"role": "system", "content": f"[TOOL_MANUAL:{tool_name}]\n{manual_data.get('manual_text', '')}"})
                continue

            elif msg.startswith("USE_TOOL:"):
                tool_name, args = parse_tool_call(msg)
                result = app.route_tool_request(tool_name, args) if tool_name else "TOOL_ERROR"
                working_messages.append({"role": "system", "content": f"[TOOL_RESULT:{tool_name}]\n{result}"})
                continue

            elif msg.startswith("EXEC:"):
                command = msg.split(":", 1)[-1].strip()
                result = app.route_exec_request(command)
                working_messages.append({"role": "system", "content": f"[SHELL_RESULT]\n{result}"})
                continue

            else:
                final_answer = msg
                break

        if not final_answer:
            final_answer = last_msg or "CPU_FALLBACK: No response."

        # === PERSISTENCE TO 26ai ===
        # persistence.py handles the SQL INSERT logic
        save_json("chat_history", {"role": "user", "content": user_input})
        save_json("chat_history", {"role": "assistant", "content": final_answer})
        save_json("belief_graph", beliefs)

        return final_answer, False

    except Exception as e:
        return f"CPU_EXCEPTION: {str(e)}", False
