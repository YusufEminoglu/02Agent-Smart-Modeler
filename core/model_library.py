"""The user's own QGIS Processing models, found where QGIS keeps them.

Model Designer saves to the profile's ``processing/models`` folder, plus any
extra folders listed in the Processing "Models folder(s)" setting. Users rarely
know those paths, so the Studio lists what is there and opens a model in one
click instead of asking for a file.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

from qgis.core import QgsApplication, QgsProcessingModelAlgorithm, QgsSettings

MAX_MODELS = 200


def model_folders() -> List[str]:
    """Every folder QGIS reads models from, existing ones only, de-duplicated."""
    folders = [str(Path(QgsApplication.qgisSettingsDirPath()) / "processing" / "models")]
    configured = QgsSettings().value("Processing/Configuration/MODELS_FOLDER", "")
    if configured:
        folders.extend(part for part in str(configured).split(";") if part.strip())
    seen, result = set(), []
    for folder in folders:
        key = os.path.normcase(os.path.abspath(folder))
        if key in seen or not os.path.isdir(folder):
            continue
        seen.add(key)
        result.append(folder)
    return result


def list_models(folders: List[str] | None = None) -> List[Dict[str, str]]:
    """``{name, group, path}`` for every readable ``.model3``, sorted by name.

    A file that QGIS itself cannot parse is skipped rather than listed: the
    list is a set of things that will open.
    """
    models = []
    for folder in folders if folders is not None else model_folders():
        for root, _dirs, files in os.walk(folder):
            for file_name in sorted(files):
                if not file_name.lower().endswith(".model3"):
                    continue
                path = os.path.join(root, file_name)
                model = QgsProcessingModelAlgorithm()
                if not model.fromFile(path):
                    continue
                models.append({
                    "name": model.displayName() or model.name() or Path(path).stem,
                    "group": model.group() or "",
                    "path": path,
                })
                if len(models) >= MAX_MODELS:
                    break
    return sorted(models, key=lambda item: (item["name"].casefold(), item["path"]))
