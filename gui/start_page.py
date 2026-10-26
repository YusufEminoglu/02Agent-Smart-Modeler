"""Start page shown in place of an empty canvas.

An empty canvas tells a first-time user nothing. This page puts the ready
workflows, the user's own QGIS models and their recent files one click away,
and disappears as soon as the workflow has a node.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

_ROLE = Qt.ItemDataRole.UserRole


def _section(title: str, hint: str = "") -> Tuple[QWidget, QVBoxLayout]:
    box = QFrame()
    box.setObjectName("startSection")
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 8, 0, 0)
    layout.setSpacing(4)
    heading = QLabel(title.upper())
    heading.setObjectName("panelEyebrow")
    layout.addWidget(heading)
    if hint:
        note = QLabel(hint)
        note.setObjectName("mutedLabel")
        note.setWordWrap(True)
        layout.addWidget(note)
    return box, layout


def _list(accessible: str) -> QListWidget:
    widget = QListWidget()
    widget.setAccessibleName(accessible)
    widget.setWordWrap(True)
    widget.setUniformItemSizes(False)
    widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    # Follow the column's width: a long path or description must wrap inside
    # it, not widen the page and put a horizontal scrollbar under the canvas.
    widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
    widget.setMinimumWidth(0)
    return widget


def _fit(widget: QListWidget) -> None:
    """Size a list to its rows so the page scrolls, not each list."""
    rows = sum(widget.sizeHintForRow(index) for index in range(widget.count()))
    widget.setFixedHeight(max(28, rows + 2 * widget.frameWidth() + 4))


class StartPage(QWidget):
    """Starter gallery, QGIS models and recent files for an empty workflow."""

    starter_requested = pyqtSignal(str)
    path_requested = pyqtSignal(str)
    blank_requested = pyqtSignal()
    open_requested = pyqtSignal()
    describe_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("startPage")
        self.setAccessibleName("Start a workflow")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)
        body = QWidget()
        scroll.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(10)

        title = QLabel("Start a workflow")
        title.setObjectName("dialogTitle")
        subtitle = QLabel(
            "Pick a ready workflow, open one of your QGIS models, or start from "
            "a blank canvas - double-click any algorithm on the left to add it. "
            "Every workflow runs on your project layers and can be saved as a "
            "QGIS model or a Python script."
        )
        subtitle.setObjectName("dialogSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        actions = QHBoxLayout()
        self.blank_button = QPushButton("Blank canvas")
        self.blank_button.setObjectName("primaryButton")
        self.open_button = QPushButton("Open file…")
        self.describe_button = QPushButton("Describe it to the AI")
        self.describe_button.setToolTip(
            "Type what the workflow should do in the prompt bar above; the "
            "offline planner works without any AI account."
        )
        for button in (self.blank_button, self.open_button, self.describe_button):
            button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        # Two rows, so the actions fit a narrow canvas column without clipping.
        actions.addWidget(self.blank_button)
        actions.addWidget(self.open_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        second = QHBoxLayout()
        second.addWidget(self.describe_button)
        second.addStretch(1)
        layout.addLayout(second)
        self.blank_button.clicked.connect(self.blank_requested)
        self.open_button.clicked.connect(self.open_requested)
        self.describe_button.clicked.connect(self.describe_requested)

        box, section = _section(
            "Everyday GIS", "Ready workflows built from QGIS's own algorithms.")
        self.everyday_list = _list("Everyday GIS workflows")
        section.addWidget(self.everyday_list)
        layout.addWidget(box)

        box, section = _section(
            "Urban analytics showcases",
            "Larger, multi-step studies. They need the plugins named under each.")
        self.showcase_list = _list("Urban analytics showcase workflows")
        section.addWidget(self.showcase_list)
        layout.addWidget(box)

        box, section = _section("Your QGIS models")
        self.models_note = QLabel()
        self.models_note.setObjectName("mutedLabel")
        self.models_note.setWordWrap(True)
        section.addWidget(self.models_note)
        self.models_list = _list("QGIS models in your profile")
        section.addWidget(self.models_list)
        layout.addWidget(box)

        box, section = _section("Recent")
        self.recent_list = _list("Recent workflows")
        section.addWidget(self.recent_list)
        layout.addWidget(box)
        layout.addStretch(1)

        self.everyday_list.itemActivated.connect(self._starter_activated)
        self.showcase_list.itemActivated.connect(self._starter_activated)
        self.everyday_list.itemClicked.connect(self._starter_activated)
        self.showcase_list.itemClicked.connect(self._starter_activated)
        self.models_list.itemActivated.connect(self._path_activated)
        self.models_list.itemClicked.connect(self._path_activated)
        self.recent_list.itemActivated.connect(self._path_activated)
        self.recent_list.itemClicked.connect(self._path_activated)

    # ------------------------------------------------------------------ fill
    def set_starters(self, available: Sequence[Dict[str, object]],
                     unavailable: Iterable[Tuple[str, str, str]] = ()) -> None:
        """``available``: starter summaries; ``unavailable``: (name, description, needs)."""
        self.everyday_list.clear()
        self.showcase_list.clear()
        for starter in available:
            showcase = "showcase" in [str(tag) for tag in starter.get("tags", [])]
            target = self.showcase_list if showcase else self.everyday_list
            name = str(starter["name"]).replace("Showcase · ", "")
            steps = int(starter.get("node_count", 0))
            item = QListWidgetItem(f"{name}  ·  {steps} steps\n{starter['description']}")
            item.setData(_ROLE, str(starter["id"]))
            item.setToolTip(str(starter["description"]))
            target.addItem(item)
        for name, description, needs in unavailable:
            item = QListWidgetItem(f"{name}  ·  needs {needs}\n{description}")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setToolTip(f"Install {needs} to use this workflow.")
            self.showcase_list.addItem(item)
        _fit(self.everyday_list)
        _fit(self.showcase_list)

    def set_models(self, models: Sequence[Dict[str, str]], folders: Sequence[str]) -> None:
        self.models_list.clear()
        for model in models:
            group = f"  ·  {model['group']}" if model.get("group") else ""
            item = QListWidgetItem(f"{model['name']}{group}\n{model['path']}")
            item.setData(_ROLE, model["path"])
            self.models_list.addItem(item)
        if models:
            self.models_note.setText(
                "Models saved by the QGIS Model Designer in your profile. Click to open one here.")
        elif folders:
            self.models_note.setText(
                "No .model3 files yet in " + "; ".join(folders) + ".")
        else:
            self.models_note.setText(
                "No QGIS models folder exists in this profile yet. Models you "
                "save from the QGIS Model Designer will appear here.")
        self.models_list.setVisible(bool(models))
        _fit(self.models_list)

    def set_recent(self, paths: List[str]) -> None:
        self.recent_list.clear()
        for path in paths:
            name = path.replace("\\", "/").split("/")[-1]
            item = QListWidgetItem(f"{name}\n{path}")
            item.setData(_ROLE, path)
            self.recent_list.addItem(item)
        if not paths:
            empty = QListWidgetItem("Workflows you open or save will appear here.")
            empty.setFlags(Qt.ItemFlag.NoItemFlags)
            self.recent_list.addItem(empty)
        _fit(self.recent_list)

    # ------------------------------------------------------------------ signals
    def _starter_activated(self, item: QListWidgetItem) -> None:
        starter_id = item.data(_ROLE)
        if starter_id:
            self.starter_requested.emit(str(starter_id))

    def _path_activated(self, item: QListWidgetItem) -> None:
        path = item.data(_ROLE)
        if path:
            self.path_requested.emit(str(path))
