from copy import deepcopy
from typing import Any, Dict, List


DEFAULT_WEIGHT = 1.0
DEFAULT_THRESHOLD = 0.15


def _normalize_node(node: Any) -> Dict[str, Any]:
    """
    Normalize belief entries into a predictable dict shape.
    Supports loose legacy values like raw strings or partial dicts.
    """
    if isinstance(node, dict):
        normalized = deepcopy(node)
        normalized.setdefault("weight", DEFAULT_WEIGHT)
        return normalized

    if isinstance(node, str):
        return {"text": node, "weight": DEFAULT_WEIGHT}

    return {"value": node, "weight": DEFAULT_WEIGHT}


def merge_beliefs(base: Dict[str, Any], updates: Dict[str, Any]):
    """Safe belief merge retained from the legacy module."""
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
    """
    Minimal 7-1 maintenance pass.

    For now this normalizes node shapes and preserves the latest field values.
    It does not attempt advanced contradiction resolution yet, but it gives
    engine.py a stable belief object to serialize and reuse.
    """
    if not isinstance(beliefs, dict):
        return {}

    normalized = {}
    for key, value in beliefs.items():
        normalized[key] = _normalize_node(value)
    return normalized


def prune_low_value_nodes(beliefs: Dict[str, Any], threshold: float = DEFAULT_THRESHOLD) -> Dict[str, Any]:
    """
    Keep only beliefs whose weight is above threshold.
    Missing weights are treated as meaningful and preserved by default.
    """
    if not isinstance(beliefs, dict):
        return {}

    pruned = {}
    for key, value in beliefs.items():
        node = _normalize_node(value)
        if float(node.get("weight", DEFAULT_WEIGHT)) >= threshold:
            pruned[key] = node
    return pruned


def filter_active_beliefs(beliefs: Dict[str, Any], threshold: float = 0.5):
    """Legacy helper retained as a stricter filter alias."""
    return prune_low_value_nodes(beliefs, threshold=threshold)


def score_belief_relevance(client, beliefs: Dict, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
    """
    Legacy LLM-scored relevance helper retained for future retrieval hooks.
    Not used by 7-1 engine yet, but kept functional for later reintegration.
    """
    scored = []

    for _, raw_node in beliefs.items():
        node = _normalize_node(raw_node)
        text = node.get("text") or node.get("concept") or str(node)

        prompt = (
            "Score relevance from 0 to 1.\n\n"
            f"Query: {query}\n"
            f"Belief: {text}\n\n"
            "Return ONLY a float."
        )

        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            score = float(res.choices[0].message.content.strip())
        except Exception:
            score = 0.0

        scored.append((score, node))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [node for _, node in scored[:top_k]]
