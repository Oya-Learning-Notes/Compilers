"""
This module contains the implementation of some functionalities
that specifically related to LL(1) specific features.
"""

from .type import *
from typing import Iterable, cast, FrozenSet, Callable, Any, Protocol
from pprint import pformat

from loguru import logger
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
        select_sets: Iterable[Iterable[Terminal]] | None = None,
    ):
        if lhs is not None:
            message += f"\nProduction LHS(Left-hand Side): {lhs}"

        if select_sets is not None:
            select_sets_for_repr: list[set[Terminal]] = list()
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

    def __init__(self, symbol: Piece):
        self.piece: Piece | None = symbol
        """
        The symbol that current node represents

        Thie field could be `None`, which could indicates two 
        different situations:
        - The original derivation has epsilon RHS.
        - Marks the end of original derivation.
        """

        self.children: "list[Piece]" = []
        """List of child nodes"""


class PerfixTreeManager:
    """
    Util class that used internally to construct prefix tree of a
    derivations.

    Prefix tree could be used to extract shared left factors when
    dealing with possible LL(1) CFG system.
    """

    def __init__(
        self, lhs: NonTerminal, symbol_generator: Callable[[Any], str]
    ) -> None:
        self.lhs = lhs
        self._symbol_generator = symbol_generator

    def add_derivation(self, derivation: Derivation):
        # Todo
        pass


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

        self.select_sets: dict[Production, frozenset[Terminal]] = {}
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

    def _generate_select_sets(self) -> dict[Production, frozenset[Terminal]]:
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
            cur_prod_select_set.discard(None)
            # cast type
            cur_prod_select_set_without_none = cast(
                "frozenset[Terminal]", frozenset(cur_prod_select_set)
            )

            # add select set info to select_sets dict
            self.select_sets[cur_prod] = cur_prod_select_set_without_none

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
            unioned_select_set: set[Terminal] = set()

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

        def new_non_terminal_allocator() -> NonTerminal:
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
                    return NonTerminal(name=c)

            raise NoAvailableSymbolNameError()

        return LL1CFGSystem()
