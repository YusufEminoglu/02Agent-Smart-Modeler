"""PyQt6 QGraphicsItem node card rendering for 02Agent Smart Modeler."""
from qgis.PyQt.QtCore import QRect, QRectF, Qt
from qgis.PyQt.QtGui import QBrush, QColor, QPen, QFont, QLinearGradient
from qgis.PyQt.QtWidgets import QGraphicsItem
from ..core.graph_model import NodeDefinition
from .port_graphics_item import PortGraphicsItem


class NodeGraphicsItem(QGraphicsItem):
    """Sleek modern node card item on the canvas."""

    WIDTH = 230.0
    HEADER_HEIGHT = 38.0
    PORT_SPACING = 24.0

    CATEGORY_COLORS = {
        "Vector Geometry": "#1B5E20",
        "Vector Overlay": "#0D47A1",
        "Vector Selection": "#4A148C",
        "Vector General": "#1E4D6B",
        "Vector Analysis": "#00695C",
        "Vector Table": "#006064",
        "Raster Analysis": "#8E2A13",
        "Raster Terrain": "#8A3500",
        "Raster Surface": "#795548",
        "Table Operations": "#006064",
        "OpenStreetMap": "#00695C",
        "Parameters": "#704000",
        "Inputs": "#4527A0",
        "General": "#424242",
    }

    @classmethod
    def header_color_for_category(
        cls, category: str, algorithm_id: str = ""
    ) -> str:
        raw = (category or "").strip()
        if raw in cls.CATEGORY_COLORS:
            return cls.CATEGORY_COLORS[raw]
        lowered = raw.casefold()
        for key, color in cls.CATEGORY_COLORS.items():
            if key.casefold() == lowered:
                return color
        alg_lower = (algorithm_id or "").casefold()
        if alg_lower.startswith("smart:"):
            if "layer" in alg_lower or "vector" in alg_lower or "raster" in alg_lower:
                return "#4527A0"
            return "#704000"
        if "osm" in lowered or "openstreetmap" in lowered or "osm" in alg_lower:
            return "#00695C"
        if "geometry" in lowered:
            return "#1B5E20"
        if "overlay" in lowered:
            return "#0D47A1"
        if "selection" in lowered or "extract" in lowered or "filter" in lowered:
            return "#4A148C"
        if "table" in lowered or "field" in lowered or "attribute" in lowered:
            return "#006064"
        if "terrain" in lowered or "surface" in lowered:
            return "#8A3500"
        if "raster" in lowered:
            return "#8E2A13"
        if "network" in lowered or "routing" in lowered or "centrality" in lowered:
            return "#1565C0"
        if "vector" in lowered:
            return "#1E4D6B"
        if "input" in lowered:
            return "#4527A0"
        if "parameter" in lowered:
            return "#704000"
        return "#424242"

    def __init__(self, node: NodeDefinition):
        super().__init__()
        self.node = node
        self.setPos(node.x, node.y)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"{node.algorithm_id}\nDouble-click to configure")
        self.input_ports: dict[str, PortGraphicsItem] = {}
        self.output_ports: dict[str, PortGraphicsItem] = {}
        self._drag_origin = self.pos()
        self.build_ports()

    def calculate_height(self) -> float:
        max_ports = max(len(self.node.inputs), len(self.node.outputs), 1)
        return self.HEADER_HEIGHT + (max_ports * self.PORT_SPACING) + 12.0

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.WIDTH, self.calculate_height())

    def build_ports(self):
        # Input ports on left edge
        y_offset = self.HEADER_HEIGHT + 14.0
        for p_id, port in self.node.inputs.items():
            port_item = PortGraphicsItem(port, self)
            port_item.setPos(0, y_offset)
            self.input_ports[p_id] = port_item
            y_offset += self.PORT_SPACING

        # Output ports on right edge
        y_offset = self.HEADER_HEIGHT + 14.0
        for p_id, port in self.node.outputs.items():
            port_item = PortGraphicsItem(port, self)
            port_item.setPos(self.WIDTH, y_offset)
            self.output_ports[p_id] = port_item
            y_offset += self.PORT_SPACING

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        rect = self.boundingRect()
        # Background Card
        bg_color = QColor("#1D2430") if self.node.is_active else QColor("#161C26")
        state_colors = {
            "running": QColor("#F2C94C"),
            "success": QColor("#57D3A0"),
            "error": QColor("#FF6B7A"),
            "invalid": QColor("#FF6B7A"),
            "needs_input": QColor("#F7B955"),
            "skipped": QColor("#7E8C9F"),
            "canceled": QColor("#E08E45"),
        }
        border_color = QColor("#72A7FF") if self.isSelected() else state_colors.get(
            self.node.execution_state, QColor("#344154"))
        border_pen = QPen(border_color, 2.0 if self.isSelected() else 1.2)
        if not self.node.is_active and not self.isSelected():
            border_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(border_pen)
        painter.drawRoundedRect(rect, 8.0, 8.0)

        # Header bar gradient
        hdr_color = QColor(
            self.header_color_for_category(
                self.node.category, self.node.algorithm_id
            )
        )
        if not self.node.is_active:
            hdr_color = hdr_color.darker(135)
        hdr_rect = QRectF(0, 0, self.WIDTH, self.HEADER_HEIGHT)
        hdr_grad = QLinearGradient(0, 0, 0, self.HEADER_HEIGHT)
        hdr_grad.setColorAt(0.0, hdr_color.lighter(104))
        hdr_grad.setColorAt(1.0, hdr_color)
        painter.setBrush(QBrush(hdr_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(hdr_rect, 8.0, 8.0)
        # Cover bottom corners of header
        painter.drawRect(QRect(0, int(self.HEADER_HEIGHT - 6), int(self.WIDTH), 6))

        # Title Text
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        painter.setPen(
            QPen(QColor("#FFFFFF") if self.node.is_active else QColor("#9AA8BC"))
        )
        title_metrics = painter.fontMetrics()
        elided_title = title_metrics.elidedText(
            self.node.title, Qt.TextElideMode.ElideRight, int(self.WIDTH - 24)
        )
        painter.drawText(
            QRectF(12, 0, self.WIDTH - 24, self.HEADER_HEIGHT),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            elided_title,
        )

        # Port Labels
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QPen(QColor("#B0BEC5")))
        port_metrics = painter.fontMetrics()

        y_offset = self.HEADER_HEIGHT + 18.0
        for p_id, port in self.node.inputs.items():
            elided_port = port_metrics.elidedText(
                port.name, Qt.TextElideMode.ElideRight, 96
            )
            painter.drawText(
                QRectF(14, y_offset - 10, 96, 16),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                elided_port,
            )
            y_offset += self.PORT_SPACING

        y_offset = self.HEADER_HEIGHT + 18.0
        for p_id, port in self.node.outputs.items():
            elided_port = port_metrics.elidedText(
                port.name, Qt.TextElideMode.ElideRight, 96
            )
            painter.drawText(
                QRectF(self.WIDTH - 110, y_offset - 10, 96, 16),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                elided_port,
            )
            y_offset += self.PORT_SPACING


    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.node.x = self.pos().x()
            self.node.y = self.pos().y()
            if self.scene():
                self.scene().update_node_connections(self.node.node_id)
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self._drag_origin = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        scene = self.scene()
        if self.pos() != self._drag_origin and scene is not None:
            scene.graph_changed.emit()

    def refresh(self):
        self.setToolTip(
            f"{self.node.algorithm_id}\n{self.node.execution_message or 'Double-click to configure'}"
        )
        self.update()
