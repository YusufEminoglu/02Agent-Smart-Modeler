from __future__ import annotations

import unittest
from unittest.mock import patch

from zero2smartmodeler.core.auto_layout import AutoLayoutEngine
from zero2smartmodeler.core.graph_model import (
    GraphModel,
    NodeDefinition,
    SocketType,
)
from zero2smartmodeler.core.proposal_engine import SmartProposalEngine


def _make_node(
    node_id: str,
    alg_id: str = "",
    in_socket: str | None = None,
    in_port: str = "INPUT",
    out_socket: str | None = None,
    out_port: str = "OUTPUT",
) -> NodeDefinition:
    node = NodeDefinition(
        node_id=node_id,
        title=node_id,
        algorithm_id=alg_id or f"test:{node_id}",
    )
    if in_socket:
        node.add_input(in_port, in_port, in_socket, required=True)
    if out_socket:
        node.add_output(out_port, out_port, out_socket)
    return node


class AutoLayoutEngineTests(unittest.TestCase):
    def test_longest_path_rank_and_dependencies_are_respected(self) -> None:
        graph = GraphModel()
        n_a = _make_node("a", out_socket=SocketType.VECTOR)
        n_b = _make_node("b", in_socket=SocketType.VECTOR, out_socket=SocketType.VECTOR)
        n_c = _make_node("c", in_socket=SocketType.VECTOR, out_socket=SocketType.VECTOR)
        n_c.add_input("SECOND", "Second", SocketType.VECTOR, required=False)
        n_d = _make_node("d", out_socket=SocketType.VECTOR)
        n_d.dependencies = ["c"]

        for item in (n_a, n_b, n_c, n_d):
            graph.add_node(item)

        self.assertIsNotNone(graph.add_edge("a", "OUTPUT", "b", "INPUT"))
        self.assertIsNotNone(graph.add_edge("a", "OUTPUT", "c", "SECOND"))
        self.assertIsNotNone(graph.add_edge("b", "OUTPUT", "c", "INPUT"))

        AutoLayoutEngine.apply_layout(graph)
        self.assertEqual(n_a.x, 0.0)
        self.assertEqual(n_b.x, AutoLayoutEngine.COLUMN_SPACING)
        self.assertEqual(n_c.x, AutoLayoutEngine.COLUMN_SPACING * 2)
        self.assertEqual(n_d.x, AutoLayoutEngine.COLUMN_SPACING * 3)

    def test_barycenter_ordering_reduces_branch_crossings(self) -> None:
        graph = GraphModel()
        src_top = _make_node("src_top", out_socket=SocketType.VECTOR)
        src_bot = _make_node("src_bot", out_socket=SocketType.VECTOR)
        dst_for_bot = _make_node("dst_for_bot", in_socket=SocketType.VECTOR)
        dst_for_top = _make_node("dst_for_top", in_socket=SocketType.VECTOR)

        for item in (src_top, src_bot, dst_for_bot, dst_for_top):
            graph.add_node(item)

        self.assertIsNotNone(graph.add_edge("src_top", "OUTPUT", "dst_for_top", "INPUT"))
        self.assertIsNotNone(graph.add_edge("src_bot", "OUTPUT", "dst_for_bot", "INPUT"))

        AutoLayoutEngine.apply_layout(graph)
        self.assertLess(src_top.y, src_bot.y)
        self.assertLess(dst_for_top.y, dst_for_bot.y)

    def test_place_new_nodes_avoids_overlapping_siblings(self) -> None:
        before = GraphModel()
        parent = _make_node("parent", out_socket=SocketType.VECTOR)
        parent.x = 100.0
        parent.y = 200.0
        before.add_node(parent)

        after = GraphModel()
        parent_after = _make_node("parent", out_socket=SocketType.VECTOR)
        child_1 = _make_node("child_1", in_socket=SocketType.VECTOR)
        child_2 = _make_node("child_2", in_socket=SocketType.VECTOR)
        for item in (parent_after, child_1, child_2):
            after.add_node(item)
        self.assertIsNotNone(after.add_edge("parent", "OUTPUT", "child_1", "INPUT"))
        self.assertIsNotNone(after.add_edge("parent", "OUTPUT", "child_2", "INPUT"))

        AutoLayoutEngine.place_new_nodes(before, after)
        self.assertEqual(child_1.x, child_2.x)
        self.assertNotEqual(child_1.y, child_2.y)


class SmartProposalEngineTests(unittest.TestCase):
    def test_extent_crs_field_and_self_loop_demotion(self) -> None:
        fake_nodes = {
            "smartmodeler:osm_download_polygons": _make_node(
                "osm_poly",
                "smartmodeler:osm_download_polygons",
                in_socket=SocketType.EXTENT,
                in_port="EXTENT",
                out_socket=SocketType.VECTOR,
            ),
            "native:reprojectlayer": _make_node(
                "reproj",
                "native:reprojectlayer",
                in_socket=SocketType.CRS,
                in_port="TARGET_CRS",
                out_socket=SocketType.VECTOR,
            ),
            "native:dissolve": _make_node(
                "dissolve",
                "native:dissolve",
                in_socket=SocketType.FIELD,
                in_port="FIELD",
                out_socket=SocketType.VECTOR,
            ),
            "native:buffer": _make_node(
                "buffer",
                "native:buffer",
                in_socket=SocketType.VECTOR,
                in_port="INPUT",
                out_socket=SocketType.VECTOR,
            ),
        }

        with (
            patch(
                "zero2smartmodeler.core.proposal_engine.AlgorithmCatalog.algorithm_exists",
                side_effect=lambda alg_id: alg_id in fake_nodes,
            ),
            patch(
                "zero2smartmodeler.core.proposal_engine.AlgorithmCatalog.create_node",
                side_effect=lambda alg_id: fake_nodes[alg_id],
            ),
        ):
            extent_src = _make_node("ext", "smart:extent", out_socket=SocketType.EXTENT)
            extent_recs = SmartProposalEngine.get_proposals_for_port(
                extent_src.outputs["OUTPUT"], extent_src
            )
            self.assertEqual(len(extent_recs), 1)
            self.assertEqual(extent_recs[0].alg_id, "smartmodeler:osm_download_polygons")
            self.assertEqual(extent_recs[0].target_port_id, "EXTENT")

            crs_src = _make_node("crs", "smart:crs", out_socket=SocketType.CRS)
            crs_recs = SmartProposalEngine.get_proposals_for_port(
                crs_src.outputs["OUTPUT"], crs_src
            )
            self.assertEqual(len(crs_recs), 1)
            self.assertEqual(crs_recs[0].alg_id, "native:reprojectlayer")
            self.assertEqual(crs_recs[0].target_port_id, "TARGET_CRS")

            field_src = _make_node("fld", "smart:field", out_socket=SocketType.FIELD)
            field_recs = SmartProposalEngine.get_proposals_for_port(
                field_src.outputs["OUTPUT"], field_src
            )
            self.assertEqual(len(field_recs), 1)
            self.assertEqual(field_recs[0].alg_id, "native:dissolve")
            self.assertEqual(field_recs[0].target_port_id, "FIELD")

            vec_src = _make_node("vec", "smart:input_layer", out_socket=SocketType.VECTOR)
            normal_score = SmartProposalEngine.get_proposals_for_port(
                vec_src.outputs["OUTPUT"], vec_src
            )[0].score
            buf_src = _make_node("buf", "native:buffer", out_socket=SocketType.VECTOR)
            self_loop_score = SmartProposalEngine.get_proposals_for_port(
                buf_src.outputs["OUTPUT"], buf_src
            )[0].score
            self.assertEqual(self_loop_score, normal_score - 12)


if __name__ == "__main__":
    unittest.main()
