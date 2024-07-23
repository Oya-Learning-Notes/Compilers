from copy import copy
from dataclasses import dataclass

from cfg import *
from automata import FA, FANode
from automata.visualize import FADiGraph
from lexical_analyzer import TokenPair

from ..items import *
from .stack_automata import *
from .. import errors as general_err

__all__ = [
    'LRParserBase'
]


@dataclass
class ParserStackItem:
    token: TokenPair
    fa_state: set[FANode[list[Item], Piece]]

    def get_valid_items(self) -> list[Item]:
        """
        Get valid items indicated by this set of states.

        Return empty list if valid items not found.
        """
        valid_items: list[Item] = []

        # states empty, no valid item
        if (self.fa_state is None) or (len(self.fa_state) == 0):
            return valid_items

        # loop state
        for st in self.fa_state:
            item_list = st.label
            valid_items.extend(item_list)

        return valid_items


class LRParserBase:
    """
    Base class for all LR parsers.

    To create new LR Parser, we need to re-write the following methods:

    - ``_generate_automaton()`` Rewrite to generate the proper Stack Automaton for the LR Parser.
    - ``_get_lookahead()`` Rewrite if you want to decide how to convert a token to its corresponding lookahead instance.
    - ``_is_lookahead_match()`` Determine how to judge whether current lookahead match the requirement of the Item.
    """
    cfg_sys: CFGSystem

    _token_list: list[TokenPair]

    # working stack of this parser
    _stack: list[ParserStackItem]

    # list of unexamined token of the parser
    _unexamined: list[TokenPair]

    # store the stack automaton for this parser
    stack_automaton: StackAutomaton

    def __init__(self, cfg_sys: CFGSystem):
        self.cfg_sys = cfg_sys
        self._generate_automaton()

    def init_state(self, token_list: list[TokenPair]) -> 'LRParserBase':
        """
        Prepare the parser, make it ready to parse the input list of token.
        """
        # shadow copy the received token list.
        self._token_list = token_list[:]
        self._unexamined = token_list[:]
        # initialize the stack
        self._stack = []
        return self

    def _get_lookahead(self) -> Terminal | None:
        """
        Return the lookahead terminal type of current state.

        Return None if no lookahead found.
        """
        if len(self._unexamined) == 0:
            return None

        return Terminal(name=self._unexamined[-1].token_type)

    def _is_lookahead_match(self, item: Item) -> bool:
        """
        Check if input item could match current lookahead of this parser.
        """
        # In convention of this package, lookahead set is None represents that no limitation on lookahead.
        # So here always return True.
        if item.lookahead_set is None or (None in item.lookahead_set):
            return True

        # get current lookahead
        lookahead_terminal = self._get_lookahead()
        # return compare result
        return lookahead_terminal in item.lookahead_set

    def _should_reduce(self) -> Production | None:
        """
        Check if the parser should perform reduction at current state of affairs.

        Rets:

        - ``Production`` Returns Production which should be used for Reduction if should reduce.
        - ``None`` If should NOT reduce at this time.
        """
        # if stack is empty, impossible to reduce
        if len(self._stack) == 0:
            return None

        # get current valid items
        valid_items = self._stack[-1].get_valid_items()

        # no valid items
        if len(valid_items) == 0:
            return None

        # check if lookahead matches.
        # todo

    def _generate_automaton(self):
        """
        Generate Stack Automaton for this parser.

        Notice:

        Make sure self.cfg_sys has been input successfully.

        Override:

        Should be overridden by subclasses to generate proper Stack Automaton for different LR Parser.
        """
        self.stack_automaton = StackAutomaton(self.cfg_sys)


class CLRParser(LRParserBase):
    """
    ## About Entry of CLR Parser:

    The entry of CLRParser should be in pattern of S' -> S $

    Specifically, the pattern should have a Derivation with two pieces, The first is the true entry, the second is the
    terminal that represent the end of parsing.

    Also in CLR(1) Items, lookahead is None represent reduce with no limitation. This will only be used in the entry
    of the augmented grammar. S' -> S$, this item should have the None as the lookahead.
    """
    pass
