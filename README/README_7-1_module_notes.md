# 7-1 Adapted Core Modules

This handoff package contains three legacy modules rewritten to match the current `7-1` engine contract instead of acting as blank stubs.

## Included Files

- `core/persistence.py`
- `core/manual_manager.py`
- `core/belief_graph.py`
- `CHANGELOG_ADAPTATION_LOG.md`
- `boot_flow_chart.md`

## Purpose of Each Module

### `core/persistence.py`
Responsible for loading and saving system state used by the cognitive loop.

#### What `7-1` calls
- `load_json("chat_history.json", [])`
- `load_json("belief_graph.json", {})`
- `save_json("chat_history.json", history)`
- `save_json("belief_graph.json", beliefs)`
- `get_identity_content("soul.md")`

#### How it works now
- Automatically creates `state/` and `identity/` if they do not exist.
- Stores JSON state in `state/` by default.
- Reads identity text from `identity/soul.md` by default.
- Creates a minimal `identity/soul.md` template if missing, so first boot does not fail.

### `core/manual_manager.py`
Supplies tool documentation to the engine when the model asks for `NEED_TOOL: some_tool`.

#### What `7-1` calls
- `audit_tool_specs(tool_name)`

#### How it works now
- Looks for `tools/<tool_name>.py`
- Looks for `tools/<tool_name>.md`
- If the manual is missing, auto-generates a simple markdown manual from the tool source docstring and public function names
- Returns the exact tuple expected by `engine.py`:
  - `({"manual_text": "..."}, "SUCCESS")`
  - or `(None, "FAIL")`

### `core/belief_graph.py`
Maintains the belief structure loaded into the system prompt.

#### What `7-1` calls
- `resolve_conflicts(beliefs)`
- `prune_low_value_nodes(beliefs)`

#### How it works now
- Normalizes raw belief values into a dict shape
- Preserves or defaults node weight values
- Prunes only clearly low-value nodes
- Retains older helper functions like `merge_beliefs`, `filter_active_beliefs`, and `score_belief_relevance` for future reintegration

## Important Integration Notes

1. These modules are now interface-compatible with `7-1/core/engine.py`.
2. They do **not** complete the unfinished cognitive architecture; they only restore the paths currently called by the new engine.
3. `main.py` mounts `tools_bus` and `patches_bus`, but does not currently call each bridge module's `initialize_bus()`. That means the buses mount, but the active manifest is not preloaded unless you patch startup later.
4. The adapted modules will allow import-time startup to succeed, but runtime tool execution still depends on the rest of the project state and bridge initialization.

## Recommended Placement

Copy the three `.py` files into:

- `7-1/core/persistence.py`
- `7-1/core/manual_manager.py`
- `7-1/core/belief_graph.py`

Copy the markdown documentation files into the project root or your changelog/docs area.
