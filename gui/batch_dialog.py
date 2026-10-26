"""Choose which workflow input to vary and the project layers to run it on."""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

_ROLE = Qt.ItemDataRole.UserRole


class BatchRunDialog(QDialog):
    """``inputs``: (node id, title, kind) with kind 'vector' or 'raster';
    ``layers``: kind -> [(layer id, layer name)]."""

    def __init__(self, inputs: Sequence[Tuple[str, str, str]],
                 layers: Dict[str, List[Tuple[str, str]]], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Run for each layer")
        self.setMinimumWidth(460)
        self._inputs = list(inputs)
        self._layers = layers
        layout = QVBoxLayout(self)
        intro = QLabel(
            "The workflow runs once per checked layer, one after another. Each "
            "run's results are named after its layer and collected in one group "
            "in the Layers panel."
        )
        intro.setWordWrap(True)
        intro.setObjectName("dialogSubtitle")
        layout.addWidget(intro)
        form = QFormLayout()
        self.input_combo = QComboBox()
        for node_id, title, kind in self._inputs:
            self.input_combo.addItem(f"{title}  ({kind})", node_id)
        form.addRow("Input to vary", self.input_combo)
        layout.addLayout(form)
        self.layer_list = QListWidget()
        self.layer_list.setAccessibleName("Layers to run the workflow on")
        layout.addWidget(self.layer_list, 1)
        row = QHBoxLayout()
        select_all = QPushButton("Check all")
        clear = QPushButton("Clear")
        select_all.clicked.connect(lambda: self._check_all(True))
        clear.clicked.connect(lambda: self._check_all(False))
        row.addWidget(select_all)
        row.addWidget(clear)
        row.addStretch(1)
        layout.addLayout(row)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Run")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.input_combo.currentIndexChanged.connect(self._fill_layers)
        self.layer_list.itemChanged.connect(self._update_ok)
        self._fill_layers()

    def _kind(self) -> str:
        index = self.input_combo.currentIndex()
        return self._inputs[index][2] if 0 <= index < len(self._inputs) else "vector"

    def _fill_layers(self, *_args) -> None:
        self.layer_list.blockSignals(True)
        self.layer_list.clear()
        for layer_id, name in self._layers.get(self._kind(), []):
            item = QListWidgetItem(name)
            item.setData(_ROLE, layer_id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.layer_list.addItem(item)
        self.layer_list.blockSignals(False)
        self._update_ok()

    def _check_all(self, checked: bool) -> None:
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for index in range(self.layer_list.count()):
            self.layer_list.item(index).setCheckState(state)

    def _update_ok(self, *_args) -> None:
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(
            len(self.selected_layers()) >= 1)

    def selected_input(self) -> str:
        return str(self.input_combo.currentData() or "")

    def selected_layers(self) -> List[str]:
        return [
            str(self.layer_list.item(index).data(_ROLE))
            for index in range(self.layer_list.count())
            if self.layer_list.item(index).checkState() == Qt.CheckState.Checked
        ]
