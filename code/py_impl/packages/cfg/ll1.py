"""
This module contains the implementation of some functionalities
that specifically related to LL(1) specific features.
"""

from .type import *
from typing import Iterable, cast, FrozenSet, Callable, Any, Protocol
from pprint import pformat
from time import sleep

from loguru import logger
from graphviz import Digraph  # type:ignore

from errors import BaseError


__all__ = [
    "LL1CFGSystem",
    "LL1CFGSystemError",
    "SelectSetConflictError",
]


class LL1CFGSystemError(BaseError):
    """
    Error class for LL1CFGSystem.
    """

    def __init__(
        self,
        name: str = "ll_1_cfg_base_error",
        message: str = "An error occurred when deal with a possible LL(1) Context-free Grammar. "
        "However, no further info is provided. ",
    ):
        super().__init__(name, message)


class SelectSetConflictError(LL1CFGSystemError):
    """
    Error class for LL1CFGSystem.
    """

    def __init__(
        self,
        name: str = "select_set_conflict",
        message: str = "Select set conflict occurred when deal with a Context-free Grammar. ",
        lhs: NonTerminal | None = None,
        select_sets: Iterable[Iterable[Terminal | None]] | None = None,
    ):
        if lhs is not None:
            message += f"\nProduction LHS(Left-hand Side): {lhs}"

        if select_sets is not None:
            select_sets_for_repr: list[set[Terminal | None]] = list()
            for s in select_sets:
                select_sets_for_repr.append(set(s))
            message += f"\nSelect sets: \n{pformat(select_sets_for_repr)}. "
            message += (
                "\nSelect sets conflict means there must be some select sets pairs that "
                "with a non-empty intersaction. Check code comment about the detail how this program "
                "detect select sets conflict."
            )
        super().__init__(name, message)


class NoAvailableSymbolNameError(LL1CFGSystemError):
    def __init__(
        self,
        name: str = "no_available_symbol_name",
        message: str = "Could not allocate new symbol name, all available symbol names are used up. ",
    ):
        super().__init__(name=name, message=message)


class PrefixTreeNode:
    """
    Util class that used internally as prefix tree node in the process of
    extract left factors
    """

    def __init__(self, piece: Piece | None, parent: "PrefixTreeNode | None" = None):
        self.piece: Piece | None = piece
        """
        The symbol that current node represents

        Thie field could be `None`, which could indicates two 
        different situations:
        - The original derivation has epsilon RHS.
        - Marks the end of original derivation.
        """

        self.children: "dict[Piece | None, PrefixTreeNode]" = dict()
        """Dict to store set of child nodes"""

        self.parent: "PrefixTreeNode | None" = parent
        """Parent node of this node"""

    def __hash__(self) -> int:
        return hash(self.piece)

    # def __eq__(self, value: object) -> bool:
    #     return isinstance(value, PrefixTreeNode) and hash(self) == hash(value)

    def _add_child_piece(self, piece: Piece | None) -> "PrefixTreeNode":
        """
        Add a child piece to this node, then return the `PrefixTreeNode`
        that represents that child node.
        """
        tree_node = PrefixTreeNode(piece=piece, parent=self)

        return self.children.setdefault(piece, tree_node)

    def _add_child_piece_list(self, pieces: list[Piece] | None):
        """
        Add a list of pieces to this node, then return the last `None` node that has been added.

        Note that there will be a `None` node that added to the end additionally, which is
        to indicate the end of a derivation.
        This prevents program to wrongfully ignore derivations which is completely duplicated
        to other longer derivations.
        For example, if we don't add `None` node as mark, then when we add:

        - `abc`
        - `abcde`

        Then the prefix tree is not able to indicates the existence of `abc` derivations.
        """
        # init pieces list
        if pieces is not None:
            _piece: list[Piece] = pieces
        else:
            _piece = []

        # if there is no piece left, add None node to children, then return the that node.
        if len(_piece) == 0:
            return self._add_child_piece(None)

        else:
            child_node = self._add_child_piece(_piece[0])
            # add pieces recursively
            return child_node._add_child_piece_list(_piece[1:])

    def _pre_iterate(self, operations: "Callable[[PrefixTreeNode], Any]") -> None:
        operations(self)
        for children_node in self.children.values():
            children_node._pre_iterate(operations)


class PrefixTreeManager:
    """
    Util class that used internally to construct prefix tree of a
    derivations.

    Prefix tree could be used to extract shared left factors when
    dealing with possible LL(1) CFG system.

    One prefix tree instance is intend to manage all derivations
    come from a single LHS(Left-hand Side).
    """

    def __init__(
        self, lhs: NonTerminal, symbol_generator: Callable[[], NonTerminal]
    ) -> None:
        self.lhs = lhs
        self._symbol_generator = symbol_generator
        self._starting_symbols: dict[Piece | None, PrefixTreeNode] = dict()

        self._is_sub_mgr: bool = True
        """
        If this prefix manager is created internally as a sub manager 
        in the process of generating productions
        """

    def add_derivations(self, derivations: Iterable[Derivation]):
        """
        Add collections of derivation using `self.add_derivation()`

        For detailed info, check `add_derivation()` docstring.
        """
        for d in derivations:
            self.add_derivation(d)

    def add_derivation(self, derivation: Derivation):
        """
        Add a derivation info into this tree manager.

        Note that the derivation should from a Production P -> abc.
        And for a same PrefixTreeManager instance, all LHS should be
        the same.

        In other word, it's inappropriate to add Derivation abc and
        def into the same manager if they comes from productions like:
        - A -> abc
        - B -> def
        Since A and B are not identical LHS.
        """
        pieces = derivation.pieces

        # if pieces is none
        if pieces is None or len(pieces) == 0:
            # add a None node to starting symbols
            return self._starting_symbols.setdefault(None, PrefixTreeNode(piece=None))

        start_piece = pieces[0]
        start_node = self._starting_symbols.setdefault(
            start_piece, PrefixTreeNode(piece=start_piece)
        )

        return start_node._add_child_piece_list(pieces[1:])

    def _add_start_nodes(self, start_nodes: Iterable[PrefixTreeNode]):
        """
        Used internally, add start nodes to this prefix tree manager directly.
        """
        assert (
            self._is_sub_mgr == True
        ), "_add_start_nodes() should only be called in a sub prefix manager"

        for node in start_nodes:
            self._starting_symbols.setdefault(node.piece, node)

    def gather_productions(self, production_set: set[Production]) -> None:
        """
        Generate all productions based on info of this prefix tree manager.
        Add all result productions into the passed-in `production_set` set.

        Note:

        `production_set` will be mutated in-place to contain the generated
        productions.
        """

        for cur_start_symbol in self._starting_symbols.values():
            self._gather_productions_for_one_starting_node(
                node=cur_start_symbol,
                production_set=production_set,
            )

        return None

    def _gather_productions_for_one_starting_node(
        self,
        node: PrefixTreeNode,
        production_set: set[Production],
    ) -> None:
        """
        Used internally, gathering productions based on info of one single starting node.
        """
        left_factors: list[Piece] = []
        working_nodes_set: set[PrefixTreeNode] = set([node])

        # gather symbols while there is only one path (that is actually the shared factor)
        while len(working_nodes_set) == 1:
            # cur single node
            cur_node = working_nodes_set.pop()

            # not reach end
            if cur_node.piece is not None:
                # update left factors
                left_factors.append(cur_node.piece)
                # update working nodes set
                working_nodes_set.update(set(cur_node.children.values()))

            # reach the end, directly added as production
            else:
                production_set.add(
                    Production(source=self.lhs, target=Derivation(pieces=left_factors))
                )
                return

        assert len(working_nodes_set) > 1
        # there are more than one path, which means there is a shared factor

        # allocate a new non-terminal
        new_nt = self._symbol_generator()

        # add the shared factor as production
        production_set.add(
            Production(
                source=self.lhs, target=Derivation(pieces=left_factors + [new_nt])
            )
        )

        # create new sub-prefix manager
        sub_prefix_manager = PrefixTreeManager(
            lhs=new_nt, symbol_generator=self._symbol_generator
        )
        sub_prefix_manager._is_sub_mgr = True
        # add all nodes
        sub_prefix_manager._add_start_nodes(working_nodes_set)

        # gathering all productions from sub manager
        sub_prefix_manager.gather_productions(production_set)

    def to_graphviz(self):
        """
        Convert this prefix tree manager into a graphviz object for visualization.
        """
        graphviz_obj = Digraph(f"Prefix Tree LHS=({self.lhs})")
        graphviz_obj.attr(rankdir="LR")

        def pre_iteration(node: PrefixTreeNode):
            nonlocal graphviz_obj

            # add this node
            graphviz_obj.node(str(id(node)), repr(node.piece))

            # add edges from parent to this node if parent exists
            if node.parent is not None:
                graphviz_obj.edge(str(id(node.parent)), str(id(node)))

        for node in self._starting_symbols.values():
            node._pre_iterate(pre_iteration)

        return graphviz_obj

    def render(self, name: str | None = None, format: str = "pdf") -> None:
        if name is None:
            name = f"Derivation Prefix Tree LHS=({self.lhs})"

        gv_obj = self.to_graphviz()
        gv_obj.render(directory="./graphviz", filename=name, format=format)
        return None


class LL1CFGSystem(CFGSystem):
    """
    A CFGSystem that is specifically used for LL(1) grammar.
    """

    def __init__(
        self,
        production_list: list[Production],
        entry: Piece | None = None,
        allow_conflict: bool = False,
    ):
        # call super init method to init CFGSystem
        super().__init__(production_list=production_list, entry=entry)

        self.select_sets: dict[Production, frozenset[Terminal | None]] = {}
        """
        A dict that stores the select set of each production.
        """

        self._generate_select_sets()

        # will raise `SelectSetConflictError` if cfg not LL(1) compatible
        # that is, raise when select set conflict detected
        try:
            self._check_select_set_conflict()
        except SelectSetConflictError as e:
            if allow_conflict:
                # logger.error(e)
                logger.warning(
                    "LL(1) CFG System instance created even conflict detected, "
                    "since allow_conflict=True passed to init function. "
                )
            else:
                raise

    @classmethod
    def from_cfg(cls, cfg: CFGSystem, allow_conflict: bool = True) -> "LL1CFGSystem":
        """Construct LL(1)CFGSystem instance from its super class"""
        return cls(
            production_list=cfg.production_list,
            entry=cfg.entry,
            allow_conflict=allow_conflict,
        )

    def _generate_select_sets(self) -> dict[Production, frozenset[Terminal | None]]:
        """
        Generate select set for each productions in this grammar. Then
        store in `self.select_sets` and return it.

        Require first set and follow set already generated.
        """
        # clear
        self.select_sets = dict()

        # iterate every productions P -> abc...
        for cur_prod in self.production_list:
            cur_prod_select_set: set[Terminal | None] = set()

            # get first set of RHS of this production abc...
            cur_prod_derive_first_set = self.calc_first_set_of_pieces(
                pieces=cur_prod.target.pieces
            )
            cur_prod_select_set.update(cur_prod_derive_first_set)

            # if RHS could produce epsilon, add follow(A) to select
            if None in cur_prod_derive_first_set:
                cur_prod_select_set.update(self.follow_sets[cur_prod.source])

            # epsilon not allowed in select set, remove it
            # cur_prod_select_set.discard(None)

            # # cast type
            # cur_prod_select_set_without_none = cast(
            #     "frozenset[Terminal | None]", frozenset(cur_prod_select_set)
            # )

            # add select set info to select_sets dict
            self.select_sets[cur_prod] = frozenset(cur_prod_select_set)

        return self.select_sets

    def _check_select_set_conflict(self) -> None:
        # deal with each LHS (non terminal)
        for cur_nonterminal, cur_productions in self.production_dict.items():
            # get select set of each production
            cur_productions_select_sets = [self.select_sets[p] for p in cur_productions]

            # Here the thought is:
            #
            # If all of this select set has no conflict, then if I
            # union all of this set, the number of elements should be
            # the sum of the number of elements in all select sets
            #
            # If after union all select sets, the number become smaller,
            # then it means there must be some duplicated elements
            # between some of them. Therefore, a select set conflict
            # is detected
            individual_count = 0
            unioned_select_set: set[Terminal | None] = set()

            for s in cur_productions_select_sets:
                individual_count += len(s)
                unioned_select_set.update(s)

            if len(unioned_select_set) != individual_count:
                raise SelectSetConflictError(
                    lhs=cur_nonterminal,
                    select_sets=cur_productions_select_sets,
                )

    def is_ll_1(self) -> bool:
        """Return `True` if this grammar is LL(1) compatible."""
        try:
            self._check_select_set_conflict()
            return True
        except SelectSetConflictError:
            return False

    def extract_left_factors(self) -> "LL1CFGSystem":
        """
        Return a new LL1CFGSystem with all left factors
        extracted using new non terminals.
        """

        new_nonterminals_set: set[NonTerminal] = set()
        """
        Store new nonterminals that used as util symbol 
        to extract left factor
        """

        new_productions_set: set[Production] = set()
        """
        Store all newly generated productions by prefix tree

        Will be used to generate new CFGGrammar
        """

        _tmp_used_pieces_names_set: set[str] = set([p.name for p in self.used_pieces])

        def new_non_terminal_allocator(*_, **__) -> NonTerminal:
            """
            Function used to allocate a valid new nonterminal
            symbol name.

            Also update new_nonterminal_set temporary sets to
            make sure allocated names is not duplicated
            """
            nonlocal self
            nonlocal new_nonterminals_set

            available_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

            # calculate used name
            used_name_set: set[str] = set()
            used_name_set.update(_tmp_used_pieces_names_set)
            used_name_set.update([n.name for n in new_nonterminals_set])

            # loop through available chars to find valid one
            # here we want to allocates from Z to A
            # which will help us to distinguish the util symbol
            # more quickly.
            for c in reversed(available_chars):
                if not c in used_name_set:
                    _tmp_used_pieces_names_set.add(c)
                    return NonTerminal(name=c)

            raise NoAvailableSymbolNameError()

        # all non terminals used in this CFGSystem
        used_nonterminal = set(
            [p for p in self.used_pieces if isinstance(p, NonTerminal)]
        )

        # for all nonterminals, extract left factors of all it's derivations
        for cur_nt in used_nonterminal:
            cur_nt_derivations_set = self.get_all_derivation(cur_nt)

            # construct prefixs tree manager
            ptree_mgr = PrefixTreeManager(
                lhs=cur_nt, symbol_generator=new_non_terminal_allocator
            )
            ptree_mgr.add_derivations(cur_nt_derivations_set)

            # gathering all new productions based on the info of prefix tree manager
            ptree_mgr.gather_productions(production_set=new_productions_set)

        return LL1CFGSystem(
            production_list=list(new_productions_set),
            entry=self.entry,
            allow_conflict=True,
        )
