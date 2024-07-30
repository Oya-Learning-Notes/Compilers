# from loguru import logger
from typing import Union
from copy import copy
from collections import namedtuple
import graphviz as gv

import cfg
from cfg import Production
from lexical_analyzer import TokenPair

from . import errors

__all__ = [
    "ParseTreeNode",
    "ParseTree",
]


class ParseTreeNode:
    node_type: cfg.Piece
    node_content: TokenPair | None
    pointers: list["ParseTreeNode"]

    # store the corresponding production info for this node.
    #
    # For more info about Corresponding Production, 
    # checkout docs/parse_tree.md -> Corresponding Production Info
    production: Production

    def __copy__(self) -> "ParseTreeNode":
        return ParseTreeNode(self.node_type, self.node_content, self.pointers)

    def __init__(
            self,
            node_type: cfg.Piece,
            node_content: TokenPair = None,
            pointers: list["ParseTreeNode"] | None = None,
    ):
        self.pointers = pointers or []
        self.node_type = node_type
        self.node_content = node_content

    def __repr__(self) -> str:
        repr_str = f"Node: {self.node_type} (Point To: "
        for i in self.pointers:
            repr_str += f"{i.node_type}, "
        repr_str += ")"
        return repr_str

    def point_to(self, nodes: Union["ParseTreeNode", list["ParseTreeNode"]]) -> None:
        """
        Add a single node or list of nodes to the pointers of this node.
        """

        def should_add(current_instance: "ParseTreeNode", node: "ParseTreeNode"):
            return current_instance != node and node not in current_instance.pointers

        # if the input is list
        if isinstance(nodes, list):
            # iterate through all nodes
            for n in nodes:
                # do not add if duplicated or self recur
                if not should_add(self, n):
                    continue
                # add nodes
                self.pointers.append(n)
            return

        if should_add(self, nodes):
            self.pointers.append(nodes)

        return


class ParseTree:
    """
    Data structure for parse tree in Parsing Algorithm.

    Support both Top-down and Bottom-up Parsing.

    Docs:

    For more info, checkout `parser/docs/parse_tree.md`.
    """

    entries: list[ParseTreeNode]
    leaves: list[ParseTreeNode]
    epsilon_leaf: ParseTreeNode

    _first_non_terminal_cache: int

    def __init__(
            self,
            start_nodes: list[ParseTreeNode],
            epsilon_terminal: cfg.Terminal | None = None,
    ):
        """
        Initialize this parse tree with some nodes.

        - Top-down: pass a list with only Entry NonTerminal to `start_nodes`
        - Bottom-up: pass a list with Terminal that match TokenPair to `start_nodes`

        For more info about ``epsilon_terminal``, checkout ``docs/parse_tree.md`` Epsilon Nodes.
        """
        # shadow copy start_nodes to entries and leaves
        self.entries = copy(start_nodes)
        self.leaves = copy(start_nodes)

        # generate epsilon node
        self.epsilon_leaf = ParseTreeNode(epsilon_terminal or cfg.Piece("[e]"))
        self._first_non_terminal_cache = 0

    def get_first_non_terminal_info(
            self, use_cache: bool = True
    ) -> tuple[int, ParseTreeNode] | None:
        """
        Return index of first node in leaves that with NonTerminal type.

        Rets:

        - ``ParseTableNode`` If successfully found a NonTerminal node in leaves.
        - ``None`` If no NonTerminal nodes in leaves
        """
        scan_start: int = 0
        scan_end: int = len(self.leaves)

        # if use cache, the scan should start at index where previous non-terminal was found
        if use_cache:
            scan_start = self._first_non_terminal_cache

        # start scanning from begin to end
        for idx in range(scan_start, scan_end):
            current_node = self.leaves[idx]
            # check if the type is non-terminal
            if isinstance(current_node.node_type, cfg.NonTerminal):
                self._first_non_terminal_cache = idx
                return idx, current_node

        # not found
        return None

    def derive_non_terminal(
            self,
            non_terminal_index: int,
            new_pieces: list[cfg.Piece] | None,
            corresponding_production: Production,
    ) -> None:
        """
        Derive the left-most NonTerminal leaves into new pieces.

        Params:

        - ``non_terminal_index`` Index of the NonTerminal node in leaves that you want to derive.
        - ``new_pieces`` List of CFG pieces that you want to replace the NonTerminal with.

        General Usage:

        - Use to derive non-terminal when using LL(1) Parser.
        """
        # get the node to derive
        non_terminal_node = self.leaves[non_terminal_index]

        # check if it could be derived
        if not isinstance(non_terminal_node.node_type, cfg.NonTerminal):
            raise errors.DerivationError(non_terminal_node.node_type, new_pieces)

        # update corresponding production of the node to be derived
        non_terminal_node.production = corresponding_production

        # create nodes list for new pieces
        if new_pieces is not None:
            # not epsilon moves, generate new node and ready for insertion
            new_nodes: list[ParseTreeNode] = [
                ParseTreeNode(node_type=piece) for piece in new_pieces
            ]
        else:
            # epsilon, the new nodes will be empty
            non_terminal_node.pointers.append(copy(self.epsilon_leaf))
            new_nodes: list[ParseTreeNode] = []

        # could be derived, add pointers to parent node
        non_terminal_node.pointers.extend(new_nodes)

        # insert new nodes to previous place of the parent node
        self.leaves = (
                self.leaves[:non_terminal_index]
                + new_nodes
                + self.leaves[non_terminal_index + 1:]
        )

    def is_valid(self) -> bool:
        """
        Check if current parse tree is a valid parse tree.

        A valid parse tree means that:
        - Only one piece in entry
        - All leaves node has Terminal type.
        """

        if len(self.entries) > 1:
            return False

        for node in self.leaves:
            if isinstance(node.node_type, cfg.NonTerminal):
                return False

        return True

    def to_graphviz(self) -> gv.Digraph:
        graph = gv.Digraph(name="Parse Tree")

        tree_node_list: list[ParseTreeNode] = copy(self.entries)

        # dfs
        while len(tree_node_list) > 0:
            # current node
            current_node = tree_node_list.pop()

            # add node to graph
            # here we must use id as the node name (unique identifier for each node)
            graph.node(str(id(current_node)), str(current_node.node_type))

            # add newly found nodes to graph, also to process list
            for new_node in current_node.pointers:
                graph.edge(str(id(current_node)), str(id(new_node)))
                tree_node_list.append(new_node)

        return graph
