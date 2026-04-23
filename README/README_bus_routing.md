# 7-1 Bus Routing Refactor

## What changed

This refactor makes `main.py` a traffic-control switchboard and moves bus readiness into dedicated route support layers.

### Startup path
1. `start.sh` scans patch and tool manifests.
2. `start.sh` verifies both bridge files plus the new bus-driver files exist.
3. FastAPI starts.
4. `main.py` initializes the patch bus driver at startup.
5. The patch bus driver loads `patches_bridge.py`, mounts it to the app, and runs `initialize_bus(...)`.
6. `main.py` binds switchboard routes for tool and exec requests.

### Lazy tool path
1. `engine.py` decides a tool is needed and sends that request through `main`.
2. `main.py` calls `route_tool_request(...)`.
3. `core/patch_bus_driver.py` routes that traffic into `patches_bridge.route(...)`.
4. `patches/tool_driver.py` receives the request as a patch module.
5. `patches/tool_driver.py` lazily loads and initializes `tools_bridge.py` if the tool bus is not ready yet.
6. `tools_bridge.py` delivers the request to the target tool.
7. The result returns back through tool driver -> patch bridge -> main -> engine.

## Files added
- `core/patch_bus_driver.py`
- `patches/tool_driver.py`
- `README_bus_routing.md`

## Files modified
- `start.sh`
- `main.py`
- `core/engine.py`
- `patches/patches_bridge.py`

## Routing contracts
- Shell execution: `engine -> main -> patch_bus_driver -> patches_bridge.call(command)`
- Tool execution: `engine -> main -> patch_bus_driver -> patches_bridge.route(app, "tool_driver", payload) -> tool_driver.handle(app, payload) -> tools_bridge.call(tool_name, args)`

## State flags
- `app.state.patch_bus_ready`
- `app.state.tool_bus_ready`

These make route readiness visible and avoid repeated initialization.
