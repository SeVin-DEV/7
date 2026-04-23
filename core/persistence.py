import json
from pathlib import Path
from typing import Any, Iterable

STATE_DIR = Path("state")
IDENTITY_DIR = Path("identity")


def _ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    IDENTITY_DIR.mkdir(parents=True, exist_ok=True)


_ensure_dirs()


def _candidate_paths(filename: str, base_dir: Path) -> Iterable[Path]:
    name_path = Path(filename)

    if name_path.is_absolute():
        yield name_path
        return

    # Prefer explicit subdirectories first for 7-1 compatibility.
    yield base_dir / name_path.name

    # Fall back to the raw relative path for older layouts.
    if name_path.parent != Path('.'):
        yield name_path


def load_json(filename: str, default: Any):
    """
    Load JSON state with a forgiving fallback strategy.

    7-1 passes plain filenames like 'chat_history.json'. This loader stores them
    under ./state by default, while still tolerating direct relative/absolute
    paths from older layouts.
    """
    _ensure_dirs()

    for path in _candidate_paths(filename, STATE_DIR):
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return default

    return default


def save_json(filename: str, data: Any) -> bool:
    """
    Persist JSON state to ./state unless an explicit path is provided.
    Returns bool so callers can treat write success as a signal if desired.
    """
    _ensure_dirs()

    name_path = Path(filename)
    target = name_path if name_path.is_absolute() else STATE_DIR / name_path.name
    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)

    return True


def get_identity_content(filename: str) -> str:
    """
    Read identity text from ./identity by default.

    If the file does not exist, create a minimal template so first boot can
    proceed without manual setup.
    """
    _ensure_dirs()

    for path in _candidate_paths(filename, IDENTITY_DIR):
        if path.exists():
            return path.read_text(encoding="utf-8").strip()

    target = IDENTITY_DIR / Path(filename).name
    target.write_text(
        "# soul.md Template\n\n"
        "Define system identity, tone, rules, or persistent role prompts here.\n",
        encoding="utf-8",
    )
    return ""
