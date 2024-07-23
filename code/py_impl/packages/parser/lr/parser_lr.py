from copy import copy
from cfg import *
from ..items import *
from .stack_automata import *
from .. import errors as general_err
from automata import FA, FANode
from automata.visualize import FADiGraph


class CLRParser:
    """

    ## About Entry of CLR Parser:

    The entry of CLRParser should be in pattern of S' -> S $

    Specifically, the pattern should have a Derivation with two pieces, The first is the true entry, the second is the
    terminal that represent the end of parsing.

    Also in CLR(1) Items, lookahead is None represent reduce with no limitation. This will only be used in the entry
    of the augmented grammar. S' -> S$, this item should have the None as the lookahead.
    """
    cfg_sys: CFGSystem
    stack_automaton: StackAutomaton

    def __init__(self, cfg_sys: CFGSystem):
        self.cfg_sys = cfg_sys
        self.stack_automaton = StackAutomaton(cfg_sys)
