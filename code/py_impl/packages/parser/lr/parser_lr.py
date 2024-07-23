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


class LRParserBase:
    """
    Base class for all LR parsers.

    Rewrites:

    To create new LR Parser, we need to re-write the following methods:

    - ``_generate_automaton()`` Rewrite to generate the proper Stack Automaton for the LR Parser.
    - ``_get_lookahead()`` Rewrite if you want to decide how to convert a token to its corresponding lookahead instance.
    - ``_is_lookahead_match()`` Determine how to judge whether current lookahead match the requirement of the Item.

    Fields:
    - ``_parser_type`` The string that represents the type of the parser. E.g.: SLR, CLR, ...
    """
    cfg_sys: CFGSystem

    _parser_type: str = 'Base LR'

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

        # check all items in current states, if they matched the current lookahead?
        matched_items: set[Item] = set()
        for item in valid_items:

            # only all matched items could be used for reduction action.
            if not (item.core.all_matched()):
                continue

            # if lookahead matched, add to matched_item list.
            if self._is_lookahead_match(item):
                matched_items.add(item)

        matched_count = len(matched_items)

        # if no item match, should not reduce
        if matched_count == 0:
            return None

        # there should be at most one matched item
        if matched_count > 1:
            raise ReduceReduceConflict(conflict_item=matched_items, parser_type=self._parser_type)

        # retrieve the only matched item
        single_match_item: Item = None
        for i in matched_items:
            single_match_item = i

        assert single_match_item is not None
        return single_match_item.core.production

    def perform_reduction(self, production: Production) -> None:
        """
        Perform Reduction operation on the Stack with the instruction of given Production.
        """
        # todo

        # retrieve info
        source = production.source
        target_pieces = production.target.pieces

        # determine reduce size.
        # Here reduce size means the count of the stack element that is going to be reduced.
        reduce_size: int = -1
        if target_pieces is None:
            reduce_size = 0
        else:
            reduce_size = len(target_pieces)

        # check if current Reduction could actually be performed.
        # that is: check if the top part of the stack matches the target pieces of this production.
        stack_top = self._stack[-reduce_size:]
        stack_top_pieces = [i.piece for i in stack_top]
        # raise error if pieces not match
        if not (stack_top_pieces == target_pieces):
            raise InvalidReductionError(production_target=target_pieces, stack_top=stack_top_pieces)

        # reduction could be successfully performed.

        # todo
        # remove previous pieces
        self._stack = self._stack[:-reduce_size]

        # generate item for new pieces
        # if the stack is not empty after removing target pieces, means we could start matching at the state of top of
        # the stack.
        start_states: set[FANode] | None = None
        if len(self._stack) > 0:
            start_states = self._stack[-1].fa_state
        new_stack_item_list = self.stack_automaton.match_stack(stack=[source], start_states=start_states)

        # add new item list to stack
        # here new stack item list should always have only one element. This is because the source part of a Production
        # should always be a single NonTerminal.
        assert len(new_stack_item_list) == 1
        self._stack.append(new_stack_item_list[0])

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


class ReduceReduceConflict(Exception):
    """
    Raise when more than one reduce operation could be performed at the same time.
    """

    def __init__(self, conflict_item: set[Item], parser_type: str | None = None):
        """
        Params:

        - conflict_item A set of the conflict item.
        - parser_type String represents the type of the parser. E.g.: CLR, LR(1), ...
        """
        parser_type_str = ''
        if parser_type is not None:
            parser_type_str += f' with type {parser_type}'

        error_msg = f'Reduce-Reduce error occurred in parser{parser_type_str}. Set of conflict items: {conflict_item}'


class InvalidReductionError(general_err.ParseErrorBase):
    """
    Raise when LR Parser is intend to perform a Reduction with instruction of a Production. However the target pieces
    of this production doesn't match the stack top of the parser state.
    """

    def __init__(self, production_target: list[Piece], stack_top: list[Piece]):
        super().__init__(
            f'A Reduction by Production with target pieces {production_target} could not been performed, '
            f'since the top part of parser Stack {stack_top} does not match such pieces.'
        )
