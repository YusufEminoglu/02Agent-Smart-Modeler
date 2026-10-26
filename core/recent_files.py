"""Recently opened or saved workflows, newest first.

The list lives in one QGIS setting as a JSON array of paths; this module
owns its maintenance and never touches QGIS, so it is testable on its own.
Paths are compared case-insensitively on Windows (where ``C:/A.json`` and
``c:\\a.json`` are one file), and a file that no longer exists is dropped when
the list is read for display rather than offered and then failing to open.
"""
from __future__ import annotations

import json
import os
from typing import Callable, List

MAX_RECENT = 8
SUFFIXES = (".smartmodeler.json", ".json", ".model3")


def _key(path: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def loads(text: object) -> List[str]:
    try:
        data = json.loads(str(text or "[]"))
    except (TypeError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    return [str(item) for item in data if isinstance(item, str) and item][:MAX_RECENT]


def dumps(paths: List[str]) -> str:
    return json.dumps(paths[:MAX_RECENT], ensure_ascii=False)


def add(paths: List[str], path: str) -> List[str]:
    """``path`` moved to the front; duplicates removed; capped."""
    if not str(path).lower().endswith(SUFFIXES):
        return list(paths)[:MAX_RECENT]
    key = _key(path)
    kept = [item for item in paths if _key(item) != key]
    return ([str(path)] + kept)[:MAX_RECENT]


def existing(paths: List[str], exists: Callable[[str], bool] = os.path.isfile) -> List[str]:
    return [path for path in paths if exists(path)]
