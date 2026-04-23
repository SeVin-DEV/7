# Adaptation Log for Legacy Core Files → 7-1

## Goal
Adapt older `persistence.py`, `manual_manager.py`, and `belief_graph.py` modules so `7-1` can boot and use real function paths instead of empty placeholders.

---

## 1) `core/persistence.py`

### Legacy behavior
- Stored JSON under `state/`
- Loaded identity text from `identity/`
- Created folders if missing
- Was already very close to `7-1` needs

### Problems against 7-1
- No explicit flexibility for direct path input
- No stable boolean return on `save_json()`
- Identity template behavior was minimal but fine

### Changes made
- Kept the `state/` and `identity/` layout
- Added path resolution helpers so the module tolerates both plain filenames and explicit paths
- Added a clear success return value from `save_json()`
- Preserved auto-template creation for `soul.md`

### Result
Import-safe and runtime-safe for the current engine load/save calls.

---

## 2) `core/manual_manager.py`

### Legacy behavior
- Scanned a hard-coded `/root/kayden/tools/` directory
- Auto-generated markdown manuals for tools missing docs
- Did **not** provide the `audit_tool_specs(tool_name)` function required by `7-1`

### Problems against 7-1
- Hard-coded path would fail in a relocated project
- Missing the exact function `engine.py` imports and calls
- Missing the exact return contract required by the engine

### Changes made
- Replaced absolute path with relative `tools/`
- Added `audit_tool_specs(tool_name)`
- Made it return:
  - `({"manual_text": manual_text}, "SUCCESS")`
  - `(None, "FAIL")`
- Retained and modernized the legacy sweep/manual generation behavior

### Result
The engine can now request a manual for a tool and receive usable prompt text.

---

## 3) `core/belief_graph.py`

### Legacy behavior
- Provided `score_belief_relevance()`
- Provided `merge_beliefs()`
- Provided `filter_active_beliefs()`

### Problems against 7-1
- Missing both required functions:
  - `resolve_conflicts()`
  - `prune_low_value_nodes()`
- Belief node structure was loose and not normalized

### Changes made
- Added `_normalize_node()` to standardize belief shapes
- Added `resolve_conflicts()` as a normalization pass
- Added `prune_low_value_nodes()` for lightweight maintenance pruning
- Retained and adapted legacy helpers for future use

### Result
The belief graph can now survive the current maintenance stage of the engine without breaking serialization or prompt injection.

---

## Overall Outcome
These three modules now satisfy the import and runtime interface currently expected by `7-1/core/engine.py` while preserving as much of the older functional intent as possible.
