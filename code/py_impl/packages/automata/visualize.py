from typing import Callable
from dataclasses import dataclass
import graphviz as gv

from .fa import FA, FANode, FANodeID

__all__ = ['FADiGraph']

EPSILON_EDGE_STYLE = 'solid'

START_NODE_SHAPE = 'diamond'
END_NODE_SHAPE = 'doubleoctagon'
START_AND_END_NODE_SHAPE = 'tripleoctagon'
NORMAL_NODE_SHAPE = 'box'


class FADiGraph[LabelType, CharType]:
    _graphviz_obj: gv.Digraph = None
    get_node_label: Callable[[FANodeID, FANode[LabelType, CharType]], str]
    get_edge_label: Callable[[tuple[object, FANodeID]], str]

    def __init__(
            self,
            get_node_label: Callable[[FANodeID, FANode[LabelType, CharType]], str] = None,
            get_edge_label: Callable[[tuple[object, FANodeID]], str] = None,
    ):
        self.get_node_label = get_node_label or self.get_node_label_default
        self.get_edge_label = get_edge_label or self.get_edge_label_default

    @staticmethod
    def get_node_label_default(nid: FANodeID, node: FANode[LabelType, CharType]) -> str:
        """
        Default function used to generate the label of a node int .dot file.
        """
        ret_str = f'{nid}'
        if node.label is not None:
            ret_str += f' {node.label}'

        return ret_str

    @staticmethod
    def get_edge_label_default(edge_info: tuple[object, FANodeID]):
        ret_str = f' "{edge_info[0]}" '
        if edge_info[0] is None:
            ret_str = ''
        return ret_str

    def from_fa(self, fa: FA) -> 'FADiGraph':
        """
        Generate a graphviz object from an fa.FA object.

        Raise RuntimeError if there is already an object.
        """
        # raise error if already exist an object
        if self._graphviz_obj is not None:
            raise RuntimeError('Graph already defined for this FADigraph object')

        # initialize object
        self._graphviz_obj = gv.Digraph('Graph')

        # add node to digraph
        for nid, node in fa.nodes.items():

            # determine node shape
            node_shape = None
            if node.is_start and node.is_end:
                node_shape = START_AND_END_NODE_SHAPE
            elif node.is_start:
                node_shape = START_NODE_SHAPE
            elif node.is_end:
                node_shape = END_NODE_SHAPE
            else:
                node_shape = NORMAL_NODE_SHAPE

            self._graphviz_obj.node(str(nid), label=self.get_node_label(nid, node), shape=node_shape)

        # add edges
        for nid, node in fa.nodes.items():
            for (next_input, next_node_id) in node.pointers:
                edge_style = None
                if next_input is None:
                    edge_style = EPSILON_EDGE_STYLE
                self._graphviz_obj.edge(
                    str(nid),
                    str(next_node_id),
                    label=self.get_edge_label((next_input, next_node_id)),
                    style=edge_style,
                )

        return self

    def get_graph(self):
        return self._graphviz_obj
