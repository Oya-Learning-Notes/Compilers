from copy import copy
from cfg import *
from ..items import *
from .. import errors as general_err
from ..parse_tree import ParseTree, ParseTreeNode
from .stack_automata import StackAutomaton

__all__ = [
    'LRParserBase',
]


class LRParserBase:
    """

    ## About Entry of CLR Parser:

    The entry of CLRParser should be in pattern of S' -> S $

    Specifically, the pattern should have a Derivation with two pieces, The first is the true entry, the second is the
    terminal that represent the end of parsing.

    Also in Canonical LR(1) Items, lookahead is None represent reduce with no limitation. This will only be used in the
    entry of the augmented grammar. S' -> S$, this item should have the None lookahead.
    """

    _parse_tree: ParseTree
    _stack_automata: StackAutomaton
