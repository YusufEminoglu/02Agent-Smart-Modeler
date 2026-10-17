"""Sugiyama-style DAG Auto-Layout Engine for 02Agent Smart Modeler (QGIS 4)."""
from typing import Dict, List, Set
from .graph_model import GraphModel, NodeDefinition


class AutoLayoutEngine:
    """Calculates clean grid coordinates for DAG nodes without overlapping cards or tangled wires."""

    COLUMN_SPACING = 330.0
    ROW_SPACING = 180.0

    @classmethod
    def arrange_patched_graph(cls, before: GraphModel, after: GraphModel) -> None:
        """Give a patched graph its coordinates before it reaches the canvas.

        A ``model_patch`` carries structure, not positions, so every node it
        added arrived at (0, 0) and the cards landed exactly on top of one
        another -- the user had to run Auto layout by hand after each AI edit.

        A graph with nothing arranged yet is laid out whole: that is the ideal
        form for a workflow the AI has just created, and it also repairs a
        graph an earlier patch left stacked at the origin. A graph the user has
        already arranged keeps every position it had; only the new nodes are
        placed, beside the parents that feed them.
        """
        if not any(node.x or node.y for node in before.nodes.values()):
            cls.apply_layout(after)
            return
        cls.place_new_nodes(before, after)

    @classmethod
    def _parent_nodes(
        cls, graph: GraphModel, node: NodeDefinition
    ) -> List[NodeDefinition]:
        seen: Set[str] = set()
        parents: List[NodeDefinition] = []
        for edge in graph.incoming_edges(node.node_id):
            pid = edge.start_node_id
            if pid in graph.nodes and pid not in seen:
                seen.add(pid)
                parents.append(graph.nodes[pid])
        for dep_id in node.dependencies:
            if dep_id in graph.nodes and dep_id not in seen:
                seen.add(dep_id)
                parents.append(graph.nodes[dep_id])
        return parents

    @classmethod
    def place_new_nodes(cls, before: GraphModel, after: GraphModel) -> None:
        """Keep established node positions and place only newly added nodes."""
        existing_ids = set(before.nodes) & set(after.nodes)
        occupied = []
        for node_id in existing_ids:
            after.nodes[node_id].x = before.nodes[node_id].x
            after.nodes[node_id].y = before.nodes[node_id].y
            occupied.append((after.nodes[node_id].x, after.nodes[node_id].y))

        new_ids = set(after.nodes) - set(before.nodes)
        if not new_ids:
            return
        right_edge = max((node.x for node in before.nodes.values()), default=0.0)
        fallback_row = 0
        try:
            ordered = after.get_topological_order()
        except ValueError:
            ordered = list(after.nodes.values())
        for node in ordered:
            if node.node_id not in new_ids:
                continue
            parents = cls._parent_nodes(after, node)
            if parents:
                target_x = max(parent.x for parent in parents) + cls.COLUMN_SPACING
                target_y = sum(parent.y for parent in parents) / len(parents)
                while any(
                    abs(ox - target_x) < 40.0 and abs(oy - target_y) < 40.0
                    for ox, oy in occupied
                ):
                    target_y += cls.ROW_SPACING
                node.x = target_x
                node.y = target_y
                right_edge = max(right_edge, node.x)
            else:
                node.x = right_edge + cls.COLUMN_SPACING
                node.y = fallback_row * cls.ROW_SPACING
                right_edge = node.x
                fallback_row += 1
            occupied.append((node.x, node.y))

    @classmethod
    def apply_layout(cls, graph: GraphModel, start_x: float = 0.0, start_y: float = 0.0) -> None:
        """Assigns (x, y) coordinates to all nodes in the graph based on topological ranks."""
        if not graph.nodes:
            return

        try:
            ordered = graph.get_topological_order()
        except ValueError:
            ordered = list(graph.nodes.values())

        insertion_index = {
            n_id: idx for idx, n_id in enumerate(graph.nodes.keys())
        }
        ranks: Dict[str, int] = {}
        for node in ordered:
            parents = cls._parent_nodes(graph, node)
            if parents:
                ranks[node.node_id] = (
                    max(ranks.get(parent.node_id, 0) for parent in parents) + 1
                )
            else:
                ranks[node.node_id] = 0

        for n_id in graph.nodes:
            if n_id not in ranks:
                ranks[n_id] = 0

        columns: Dict[int, List[NodeDefinition]] = {}
        for n_id, rank in ranks.items():
            columns.setdefault(rank, []).append(graph.nodes[n_id])

        for rank in sorted(columns.keys()):
            nodes = columns[rank]
            if rank > 0:
                def _barycenter(item: NodeDefinition) -> tuple:
                    parents = cls._parent_nodes(graph, item)
                    if not parents:
                        return (0.0, insertion_index.get(item.node_id, 0))
                    avg_y = sum(parent.y for parent in parents) / len(parents)
                    return (avg_y, insertion_index.get(item.node_id, 0))

                nodes.sort(key=_barycenter)
            else:
                nodes.sort(key=lambda item: insertion_index.get(item.node_id, 0))

            col_x = start_x + (rank * cls.COLUMN_SPACING)
            total_height = (len(nodes) - 1) * cls.ROW_SPACING
            initial_y = start_y - (total_height / 2.0)

            for idx, node in enumerate(nodes):
                node.x = col_x
                node.y = initial_y + (idx * cls.ROW_SPACING)

