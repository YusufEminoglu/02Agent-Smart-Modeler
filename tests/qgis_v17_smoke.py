"""QGIS smoke for the v1.7.0 Studio features: start page, QGIS models,
recent workflows, the six everyday starters and Run for each layer.

    python-qgis-ltr.bat -m zero2smartmodeler.tests.qgis_v17_smoke
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsApplication

EVERYDAY = (
    "Dissolve features",
    "Count points in polygons",
    "Distance to the nearest feature",
    "Raster statistics per zone",
    "Repair and reproject",
    "Catchment by distance",
)


class _MemorySettings:
    """Isolated settings store; never touches the user's QGIS profile."""

    store: dict = {}

    def value(self, key, default=None, **_kwargs):
        return self.store.get(key, default)

    def setValue(self, key, value) -> None:  # noqa: N802 - Qt naming
        self.store[key] = value

    def remove(self, prefix) -> None:
        for key in list(self.store):
            if key.startswith(prefix):
                self.store.pop(key)

    def sync(self) -> None:
        return None


def _polygons(name: str, offset: float):
    from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer

    layer = QgsVectorLayer("Polygon?crs=EPSG:3857&field=id:integer", name, "memory")
    feature = QgsFeature(layer.fields())
    feature.setAttributes([1])
    feature.setGeometry(QgsGeometry.fromPolygonXY([[
        QgsPointXY(offset, 0), QgsPointXY(offset + 100, 0),
        QgsPointXY(offset + 100, 100), QgsPointXY(offset, 100), QgsPointXY(offset, 0),
    ]]))
    layer.dataProvider().addFeatures([feature])
    return layer


def run_checks() -> str:
    from qgis.core import QgsProject
    from zero2smartmodeler.core.execution_engine import ExecutionStatus
    from zero2smartmodeler.core.micro_packages import MicroPackageCatalog
    from zero2smartmodeler.core.model3_serializer import Model3Serializer
    from zero2smartmodeler.gui import modeler_window

    notes = []
    models_dir = tempfile.mkdtemp(prefix="sm-models-")
    modeler_window.QgsSettings = _MemorySettings
    modeler_window.model_folders = lambda: [models_dir]
    window = modeler_window.SmartModelerWindow(None)

    # ------------------------------------------------------------ start page
    if window.canvas_stack.currentWidget() is not window.start_page:
        raise RuntimeError("An empty workflow does not open on the start page.")
    everyday = [window.start_page.everyday_list.item(i).text().split("  ·  ")[0]
                for i in range(window.start_page.everyday_list.count())]
    missing = [name for name in EVERYDAY if name not in everyday]
    if missing:
        raise RuntimeError(f"Everyday starters missing from the start page: {missing}")
    for package_id in ("dissolve_features", "count_points_in_polygons", "nearest_feature_join",
                       "zonal_statistics", "repair_and_reproject", "buffer_and_merge"):
        graph = MicroPackageCatalog.instantiate(package_id)
        model, fatal, issues = Model3Serializer.build_native_model(graph)
        if model is None or fatal or issues:
            raise RuntimeError(f"{package_id} is not a valid native model: {fatal or issues}")
    window._start_with_starter("count_points_in_polygons")
    if window.canvas_stack.currentWidget() is not window.view or len(window.graph.nodes) != 3:
        raise RuntimeError("Choosing a starter did not load it onto the canvas.")
    window.document_history.mark_clean()
    window.new_document()
    if window.canvas_stack.currentWidget() is not window.start_page:
        raise RuntimeError("New does not bring the start page back.")
    window._start_blank()
    if window.canvas_stack.currentWidget() is not window.view:
        raise RuntimeError("Blank canvas did not dismiss the start page.")
    window.new_document()
    notes.append("start page lists the six everyday starters, loads one, returns on New")

    # ------------------------------------------------------------ QGIS models + recent
    starter = MicroPackageCatalog.instantiate("dissolve_features")
    model_path = str(Path(models_dir) / "My dissolve.model3")
    saved, error = Model3Serializer.export_to_model3(starter, model_path, allow_invalid=True)
    if not saved:
        raise RuntimeError(f"Could not write the fixture model: {error}")
    window._populate_start_page()
    if window.start_page.models_list.count() != 1:
        raise RuntimeError("The QGIS models folder model is not listed.")
    window._start_with_path(model_path)
    if not window.graph.nodes:
        raise RuntimeError("Opening the listed QGIS model left an empty canvas.")
    window._rebuild_recent_menu()
    titles = [action.text() for action in window.recent_menu.actions()]
    if "My dissolve.model3" not in titles:
        raise RuntimeError(f"Recent menu does not offer the opened model: {titles}")
    window.document_history.mark_clean()
    window.new_document()
    if window.start_page.recent_list.count() != 1 or model_path not in window.start_page.recent_list.item(0).text():
        raise RuntimeError("The start page does not list the recent workflow.")
    notes.append("a model in the QGIS models folder opens in one click and is remembered")

    # ------------------------------------------------------------ run for each layer
    project = QgsProject.instance()
    first, second = _polygons("Block A", 0.0), _polygons("Block B", 500.0)
    project.addMapLayers([first, second])
    window.load_preset_package("vector_buffer")
    original = window.graph.nodes["features"].parameters.get("LAYER", "")
    window.suppress_batch_report = True
    window.start_batch("features", [first.id(), second.id()])
    deadline = time.monotonic() + 60.0
    while window._batch is not None and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.01)
    if window._batch is not None:
        raise RuntimeError("Run for each layer did not finish within 60 s.")
    rows = window.last_batch_rows
    if [row[1] for row in rows] != [ExecutionStatus.COMPLETED] * 2:
        raise RuntimeError(f"Run for each layer did not complete both runs: {rows}")
    groups = [child for child in project.layerTreeRoot().children()
              if child.name().startswith("Run for each layer")]
    if len(groups) != 1:
        raise RuntimeError("The batch results were not collected in one group.")
    names = sorted(child.name() for child in groups[0].children())
    if len(names) != 2 or not names[0].endswith("— Block A") or not names[1].endswith("— Block B"):
        raise RuntimeError(f"Batch results are not named after their layers: {names}")
    if window.graph.nodes["features"].parameters.get("LAYER", "") != original:
        raise RuntimeError("The varied input was not restored after the batch.")
    notes.append("Run for each layer ran twice, named and grouped the results, restored the input")
    window.document_history.mark_clean()
    window.close()
    return "PASS v1.7 Studio smoke: " + "; ".join(notes) + "."


def main() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QgsApplication([], True)
    app.initQgis()
    plugins_path = os.path.normpath(os.path.join(QgsApplication.prefixPath(), "python", "plugins"))
    if plugins_path not in sys.path:
        sys.path.insert(0, plugins_path)
    try:
        from processing.core.Processing import Processing
        from qgis.analysis import QgsNativeAlgorithms

        if QgsApplication.processingRegistry().providerById("native") is None:
            QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
        Processing.initialize()
        print(run_checks(), flush=True)
        return 0
    except Exception as error:  # a failed check is a failed suite
        import traceback

        traceback.print_exc()
        print(f"FAIL v1.7 Studio smoke: {type(error).__name__}: {error}", flush=True)
        return 1
    finally:
        app.exitQgis()
        globals()["_QGIS_APPLICATION"] = app


if __name__ == "__main__":
    _code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(_code)
