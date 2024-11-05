from typing import Callable, Any, Literal
from dataclasses import dataclass, replace
from functools import wraps, partialmethod
import graphviz as gv

from .fa import FA, FANode

__all__ = ["FADiGraph"]

NodeShapeLiteral = Literal[
    "box",
    "polygon",
    "ellipse",
    "oval",
    "circle",
    "point",
    "egg",
    "triangle",
    "plaintext",
    "plain",
    "diamond",
    "trapezium",
    "parallelogram",
    "house",
    "pentagon",
    "hexagon",
    "septagon",
    "octagon",
    "doublecircle",
    "doubleoctagon",
    "tripleoctagon",
    "invtriangle",
    "invtrapezium",
    "invhouse",
    "Mdiamond",
    "Msquare",
    "Mcircle",
    "rect",
    "rectangle",
    "square",
    "star",
    "none",
    "underline",
    "cylinder",
    "note",
    "tab",
    "folder",
    "box3d",
    "component",
]

EPSILON_EDGE_STYLE = "solid"

START_NODE_SHAPE: NodeShapeLiteral = "diamond"
END_NODE_SHAPE: NodeShapeLiteral = "doubleoctagon"
START_AND_END_NODE_SHAPE: NodeShapeLiteral = "tripleoctagon"
NORMAL_NODE_SHAPE: NodeShapeLiteral = "box"


from typing import Literal


@dataclass
class FADiGraphStyle[LabelType, CharType]:
    """
    A util data class used to defined the styles of the generated graphviz
    when using FADiGraph.

    # Refs:

    - [Node Shapes In GraphViz](https://graphviz.org/doc/info/shapes.html)
    """

    epsilon_edge_style: str = EPSILON_EDGE_STYLE
    start_node_shape: NodeShapeLiteral = START_NODE_SHAPE
    end_node_shape: NodeShapeLiteral = END_NODE_SHAPE
    start_and_end_node_shape: NodeShapeLiteral = START_AND_END_NODE_SHAPE
    normal_node_shape: NodeShapeLiteral = NORMAL_NODE_SHAPE
    create_start_pointers: bool = True
    """
    Create a arrow pointers to the start state.
    """

    get_node_label: Callable[[str, FANode[LabelType, CharType]], str] | None = None
    """
    Callback Pattern:
    
    - Parameter: (node_id, node_instance)
    - Returns: str
    """

    get_edge_label: Callable[[tuple[CharType | None, str]], str] | None = None
    """
    Callback Pattern:
    
    - Parameters: (pointers)
    - Returns: str
    """


AutomataStandardStyle = FADiGraphStyle[Any, Any](
    start_node_shape="circle",
    normal_node_shape="circle",
    end_node_shape="doublecircle",
    start_and_end_node_shape="doublecircle",
)


class FADiGraph[LabelType, CharType]:

    def __init__(
        self,
        fa: FA,
        name: str | None = None,
        style: FADiGraphStyle[LabelType, CharType] = AutomataStandardStyle,
        # get_node_label: Callable[[str, FANode[LabelType, CharType]], str] | None = None,
        # get_edge_label: Callable[[tuple[object, str]], str] | None = None,
    ):
        # init name
        self.name = name or "Automata Graph"

        # init styles
        style.get_node_label = style.get_node_label or self.get_node_label_default
        style.get_edge_label = style.get_edge_label or self.get_edge_label_default

        # store styles
        self.style = style

        # init fa
        self._graphviz_obj: gv.Digraph
        if fa is not None:
            self.from_fa(fa)

    @staticmethod
    def get_node_label_default(nid: str, node: FANode[LabelType, CharType]) -> str:
        """
        Default function used to generate the label of a node int .dot file.
        """
        ret_str = f"{nid}"
        if node.label is not None:
            ret_str += f" {node.label}"

        return ret_str

    @staticmethod
    def get_edge_label_default(edge_info: tuple[object, str]):
        ret_str = f" {edge_info[0]} "
        if edge_info[0] is None:
            ret_str = ""
        return ret_str

    def from_fa(self, fa: FA) -> "FADiGraph":
        """
        Generate a graphviz object from an fa.FA object.

        Raise RuntimeError if there is already an object.
        """

        # initialize object
        self._graphviz_obj = gv.Digraph(self.name)

        # add node to digraph
        for nid, node in fa.nodes.items():

            # determine node shape
            node_shape = None
            if node.is_start and node.is_end:
                node_shape = self.style.start_and_end_node_shape
            elif node.is_start:
                node_shape = self.style.start_node_shape

                # add arrow points to start node if configured
                if self.style.create_start_pointers:
                    # create invisible node
                    self._graphviz_obj.node(
                        f"start_pointers_{nid}", label="", shape="plaintext"
                    )
                    # add arrow from invisible node to the start node
                    self._graphviz_obj.edge(
                        f"start_pointers_{nid}",
                        nid,
                    )

            elif node.is_end:
                node_shape = self.style.end_node_shape
            else:
                node_shape = self.style.normal_node_shape

            assert self.style.get_node_label is not None
            self._graphviz_obj.node(
                str(nid), label=self.style.get_node_label(nid, node), shape=node_shape
            )

        # add edges
        for nid, node in fa.nodes.items():
            for next_input, next_node_id in node.pointers:
                edge_style = None
                if next_input is None:
                    edge_style = self.style.epsilon_edge_style

                assert self.style.get_edge_label is not None
                self._graphviz_obj.edge(
                    str(nid),
                    str(next_node_id),
                    label=self.style.get_edge_label((next_input, next_node_id)),
                    style=edge_style,
                )

        return self

    def get_graph(self) -> gv.Digraph:
        if self._graphviz_obj is None:
            raise RuntimeError(
                "FADiGraph.get_graph() called while self._graphviz_obj is None. Make sure you already call self.from_fa() before."
            )
        return self._graphviz_obj

    def render(self):
        self._graphviz_obj.render(
            filename=f"{self.name}",
            directory="./graphviz",
            view=True,
        )
