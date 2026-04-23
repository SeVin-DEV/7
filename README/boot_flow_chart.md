# 7-1 Boot and Runtime Flow Chart

```text
install.sh
  |
  v
Dependency install / environment prep
  |
  v
start.sh
  |
  +--> scan_plugins()
  |      |
  |      +--> checks for patches/patches_bridge.py
  |      +--> checks for tools/tools_bridge.py
  |      +--> builds SVN_ACTIVE_PATCHES
  |      +--> builds SVN_ACTIVE_TOOLS
  |
  +--> handle_git_sync()
  |
  +--> boot_server()
         |
         +--> uvicorn main:app
                |
                v
              main.py import time
                |
                +--> imports core.engine
                         |
                         +--> imports core.persistence
                         +--> imports core.manual_manager
                         +--> imports core.belief_graph


FastAPI startup event
  |
  +--> load_environment()
  |
  +--> init_llm_client(app)
  |
  +--> mount_pnp_buses(app)
         |
         +--> mounts patches_bridge as app.patches_bus
         +--> mounts tools_bridge as app.tools_bus


/chat?q=...
  |
  v
run_cognitive_cycle(app, client, user_input)
  |
  +--> persistence.load_json("chat_history.json", [])
  +--> persistence.load_json("belief_graph.json", {})
  +--> persistence.get_identity_content("soul.md")
  |
  +--> belief_graph.resolve_conflicts(beliefs)
  +--> belief_graph.prune_low_value_nodes(beliefs)
  |
  +--> build working prompt context
  |
  +--> model generates a step
         |
         +--> if NEED_TOOL:
         |      |
         |      +--> manual_manager.audit_tool_specs(tool_name)
         |      +--> returns manual text for prompt continuation
         |
         +--> if USE_TOOL:
         |      |
         |      +--> app.tools_bus.call(tool_name, args)
         |
         +--> if EXEC:
         |      |
         |      +--> app.patches_bus.call(command)
         |
         +--> else final answer
  |
  +--> persistence.save_json("chat_history.json", history)
  +--> persistence.save_json("belief_graph.json", beliefs)
  |
  v
JSON response returned by FastAPI
```

## Practical Meaning

- `start.sh` does **not** directly check for the three core modules.
- Python import of `main.py` causes `core.engine` to load them immediately.
- Once adapted, these files unblock both boot and the early runtime path used by `/chat`.
