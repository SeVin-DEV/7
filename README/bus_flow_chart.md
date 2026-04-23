```text
START.SH
  -> scan_plugins()
  -> export SVN_ACTIVE_PATCHES / SVN_ACTIVE_TOOLS
  -> verify bridges + drivers exist
  -> uvicorn main:app

MAIN STARTUP
  -> load_environment()
  -> init_llm_client()
  -> initialize_patch_bus(app)
       -> load patches/patches_bridge.py
       -> mount as app.patches_bus
       -> initialize_bus(app, manifest)
       -> set app.state.patch_bus_ready = True
  -> bind_request_router(app)

CHAT REQUEST
  -> /chat
  -> run_cognitive_cycle(app, client, q)

TOOL ROUTE
  -> engine emits USE_TOOL
  -> engine calls app.route_tool_request(tool_name, args)
  -> main switchboard forwards to patch_bus_driver.route_tool_request(app, ...)
  -> patch bus driver calls app.patches_bus.route(app, "tool_driver", payload)
  -> patches/tool_driver.py handle(app, payload)
       -> ensure_tool_bus(app)
           -> load tools/tools_bridge.py if needed
           -> initialize_bus(app, SVN_ACTIVE_TOOLS)
           -> set app.state.tool_bus_ready = True
       -> app.tools_bus.call(tool_name, args)
  -> tool returns output
  -> output returns via tool_driver -> patch bridge -> patch bus driver -> main -> engine

EXEC ROUTE
  -> engine emits EXEC
  -> engine calls app.route_exec_request(command)
  -> patch bus driver calls app.patches_bus.call(command)
  -> subprocess result returns to engine through main
```
