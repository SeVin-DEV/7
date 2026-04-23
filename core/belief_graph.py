from copy import deepcopy
from typing import Any, Dict, List

DEFAULT_WEIGHT = 1.0
DEFAULT_THRESHOLD = 0.15

def _normalize_node(node: Any) -> Dict[str, Any]:
    """Normalize belief entries into a predictable dict shape."""
    if isinstance(node, dict):
        normalized = deepcopy(node)
        normalized.setdefault("weight", DEFAULT_WEIGHT)
        return normalized

    if isinstance(node, str):
        return {"text": node, "weight": DEFAULT_WEIGHT}

    return {"value": node, "weight": DEFAULT_WEIGHT}

def merge_beliefs(base: Dict[str, Any], updates: Dict[str, Any]):
    """Safe belief merge for DB-backed state updates."""
    if not isinstance(base, dict):
        base = {}
    if not isinstance(updates, dict):
        return base

    for key, value in updates.items():
        if key not in base:
            base[key] = _normalize_node(value)
            continue

        current = _normalize_node(base[key])
        incoming = _normalize_node(value)
        current.update(incoming)
        base[key] = current

    return base

def resolve_conflicts(beliefs: Dict[str, Any]) -> Dict[str, Any]:
    """Normalization pass before DB storage."""
    if not isinstance(beliefs, dict):
        return {}

    normalized = {}
    for key, value in beliefs.items():
        normalized[key] = _normalize_node(value)
    return normalized

def prune_low_value_nodes(beliefs: Dict[str, Any], threshold: float = DEFAULT_THRESHOLD) -> Dict[str, Any]:
    """Keep only beliefs whose weight is above threshold for DB efficiency."""
    if not isinstance(beliefs, dict):
        return {}

    pruned = {}
    for key, value in beliefs.items():
        node = _normalize_node(value)
        if float(node.get("weight", DEFAULT_WEIGHT)) >= threshold:
            pruned[key] = node
    return pruned

# --- 26ai VECTOR PREP HOOK ---
def get_vectorizable_content(beliefs: Dict[str, Any]) -> List[str]:
    """
    New Hook: Converts normalized beliefs into text strings 
    suitable for future Vector Embedding generation.
    """
    output = []
    for key, val in beliefs.items():
        text = val.get("text") or val.get("value") or str(val)
        output.append(f"Concept: {key} | Details: {text}")
    return output
