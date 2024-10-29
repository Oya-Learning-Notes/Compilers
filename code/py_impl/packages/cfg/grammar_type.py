"""
Including tools to check the chomsky grammar type of certain grammar system.
"""

import traceback
from collections.abc import Sequence, Callable
from functools import cached_property

from rich import print as rprint
from rich.pretty import pprint as rpprint
from rich.pretty import pretty_repr

from loguru import logger

from .type import Piece, NonTerminal, Terminal, Derivation


class ChomskyGrammarError(Exception):
    """
    Raised when failed to check the chomsky grammar type of the `ChomskyGrammarSystem`
    """

    name: str
    message: str

    def __init__(self, name: str, message: str):
        self.name = name
        self.message = message
        super().__init__(message)

    def __repr__(self):
        return f"{self.message} ({self.name})"

    def __str__(self) -> str:
        return repr(self)


class EmptyLHS(ChomskyGrammarError):
    def __init__(self):
        super().__init__(
            "empty_left_hand_side",
            "A valid chomsky production must have a non-empty left-hand side",
        )


class InvalidLHS(ChomskyGrammarError):
    def __init__(self):
        super().__init__(
            name="invalid_left_hand_side",
            message="Left-hand side of a chomsky grammar must contain at least one non-terminal",
        )

class UnprocessableEpsilonRule(ChomskyGrammarError):
    def __init__(self,
                  name='unprocessable_epsilon_rule',
                  message='This epsilon rule could not be handled by current program',
                  production: 'ChomskyProduction | None' = None,
                  ):
        if production is not None:
            message += f" (Production: {production})"
        super().__init__(name, message)

class EpsilonStartSymbolAtRHS(ChomskyGrammarError):
    def __init__(self,
                  name: str='epsilon_entry_at_rhs', 
                  message:str="The grammar contains epsilon rules with start symbol" 
                  "at left-hand side, however, the start symbol appeared as "
                  "non-terminal at some right-hand side of some other productions. ",
                 ):
        super().__init__(name, message)

class ChomskyProduction:
    """
    This class is used to represent a general chomsky grammar, and
    currently only used for the feature of checking grammer systems chomsky level.

    For grammar system class used in Lexical Analyzer and Parser, please
    check out `cfg.CFGSystem`

    Also this class should be considered immutable once created, and some cached_property
    is used.
    """

    def __init__(self, source: Sequence[Piece], target: Sequence[Piece]):
        self.source: Sequence[Piece] = source
        self.target: Sequence[Piece] = target

        # check production validity
        self.check_validity()

    def __repr__(self):
        source_str = ""
        for s in self.source:
            source_str += str(s)

        target_str = ""
        for t in self.target:
            target_str += str(t)

        if target_str == "":
            target_str = "\\e"

        return f"{source_str} -> {target_str}"

    def check_validity(self) -> None:
        # left-hand side must not be empty
        if self.lhs_len == 0:
            raise EmptyLHS()

        # lhs must contains at least one non-terminal
        has_non_terminal = False
        for p in self.source:
            if isinstance(p, NonTerminal):
                has_non_terminal = True
                break

        if not has_non_terminal:
            raise InvalidLHS()

    def is_rhs_epsilon(self) -> bool:
        """
        Return True if the right hand side of this production is epsilon
        (empty string)
        """
        return len(self.target) == 0

    @property
    def lhs_len(self):
        return len(self.source)

    @property
    def rhs_len(self):
        return len(self.target)

    @cached_property
    def chomsky_hierarchy(self) -> int:
        """
        Return the chomsky hierarchy of this production

        - 40: Empty right-hand side or single terminal rhs,
          could exists in all chomsky hierarchies,
          doesn't need to take into consideration
        - 0: Recursive enumerable (...)
        - 1: Context-sensitive (xAy->xBCy)
        - 2: Context-free (P->...)
        - 30: Regular
        - 31: Left Regular (S->Aa)
        - 32: Right Regular (S->aA)
        """

        # if left-hand side is multiple piece
        if self.lhs_len > 1:
            # if rhs is epsilon or has length greater than lhs
            if self.is_rhs_epsilon():
                return 1
            if self.rhs_len >= self.lhs_len:
                return 1
            return 0

        # at this point, lhs could only be 1
        # check if it's a regular production

        if self.is_rhs_epsilon():
            return 40

        if self.rhs_len == 1 and isinstance(self.target[0], Terminal):
            return 40

        has_terminal: bool = False
        has_non_terminal: bool = False

        for p in self.target:
            if isinstance(p, NonTerminal):
                has_terminal = True
            if isinstance(p, Terminal):
                has_non_terminal = True

        if has_terminal and has_non_terminal and self.rhs_len == 2:
            # Left Regular
            if isinstance(self.target[0], NonTerminal):
                return 31
            else:
                return 32

        # only has one non-terminal at lhs, context-free
        return 2


HIERARCHY_TEXT: dict[int, str] = {
    0: "Recursive Enumerable",
    1: "Context-sensitive",
    2: "Context-free",
    30: "Regular",
    31: "Left Regular",
    32: "Right Regular",
    40: "Epsilon/Single Terminal",
}


class ChomskyGrammarSystem:
    def __init__(
        self,
        entry: Piece,
        productions: Sequence[ChomskyProduction],
        pieces: Sequence[Piece] | None = None,
    ):
        self.entry: Piece = entry
        self.nonterminals: set[NonTerminal] = set()
        self.terminals: set[Terminal] = set()
        self.productions: Sequence[ChomskyProduction] = productions

        # automatically gathering pieces info from productions
        # if not provided in parameters.
        if pieces is None:
            pieces = []
            for p in self.productions:
                for piece in p.source:
                    pieces.append(piece)
                for piece in p.target:
                    pieces.append(piece)

        # construct terminals and nonterminals from pieces
        for p in pieces:
            if isinstance(p, NonTerminal):
                self.nonterminals.add(p)
            elif isinstance(p, Terminal):
                self.terminals.add(p)
            else:
                raise ValueError(f"Invalid piece: {p}")
        
        # check epsilon rules
        self.check_is_epsilon_rules_valid()

    def check_is_epsilon_rules_valid(self):
        has_epsilon_s_rule: bool = False
        entry_in_rhs: bool = False

        for p in self.productions:
            # found some rules with epsilon rhs
            if len(p.target) == 0:
                # then the rule must be like S->...
                if p.source[0] == self.entry and len(p.source) ==1:
                    has_epsilon_s_rule = True
                else:
                    raise UnprocessableEpsilonRule(production=p)
            
            # in the same loop, check if entry symbol appeared in rhs
            if self.entry in p.target:
                entry_in_rhs = True

        
        if has_epsilon_s_rule == True and entry_in_rhs:
            raise EpsilonStartSymbolAtRHS()
                

    def eliminate_epsilon_rules(self):
        """
        Eliminate the epsilon rules by modifying productions of 
        this grammar.

        Deprecated.
        """
        def replace_epsilon_nonterminal_in_rhs(nt: NonTerminal):
            nonlocal self
            for p in self.productions:
                pass
                

        mutated: bool = True
        while mutated:
            mutated = False

            curr_epsilon_rule: ChomskyProduction | None = None
            for p in self.productions:
                if len(p.target) == 0:
                    curr_epsilon_rule = p
                    break


    def __repr__(self) -> str:
        prod_str = (
            str(self.productions)
            .replace(", ", ", \n    ")
            .replace("[", "[\n    ")
            .replace("]", "\n  ],")
        )

        repr_str = "G={\n"
        repr_str += f"  {str(self.nonterminals)}\n"
        repr_str += f"  {str(self.terminals)}\n"
        repr_str += f"  {prod_str}\n"
        repr_str += f"  {str(self.entry)}\n"
        repr_str += "}"

        return repr_str

    @cached_property
    def chomsky_hierarchy(self) -> int:
        """
        The semantic of the return value concurred with `ChomskyProduction.chomsky_hierarchy`, please check the
        doc for more info.

        - 40: Empty right-hand side, doesn't need to take into consideration
        - 0: Recursive enumerable (...)
        - 1: Context-sensitive (xAy->xBCy)
        - 2: Context-free (P->...)
        - 31: Left Regular (S->Aa)
        - 32: Right Regular (S->aA)
        """
        max_hierarchy = 40

        for p in self.productions:
            current_production_hierarchy = p.chomsky_hierarchy
            logger.debug(
                f"Hierarchy of {repr(p):<10} "
                f"= {HIERARCHY_TEXT[current_production_hierarchy]}' "
                f"({current_production_hierarchy})"
            )

            # epsilon rhs
            if current_production_hierarchy == 40:
                continue

            if max_hierarchy == 40:
                max_hierarchy = current_production_hierarchy
                continue

            # using python chained comparison
            # two are both regular, but with different direction
            # then the final grammar could at most be context-free(2)
            if 30 < current_production_hierarchy != max_hierarchy > 30:
                max_hierarchy = 2

            max_hierarchy = min(current_production_hierarchy, max_hierarchy)

        if max_hierarchy == 40:
            max_hierarchy = 30

        return max_hierarchy


# Some predefined pieces (terminals and non-terminals)
S = NonTerminal("S")
A = NonTerminal("A")
B = NonTerminal("B")
C = NonTerminal("C")
a = Terminal("a")
b = Terminal("b")
c = Terminal("c")


def case_empty_lhs_productions():
    return [ChomskyProduction([], [A])]


def case_invalid_lhs_productions():
    return [ChomskyProduction([a, b], [a, b, c])]


case_0_productions = [
    ChomskyProduction([S], []),
    ChomskyProduction([S], [A]),
    ChomskyProduction([A, B], [A, B, C]),
    ChomskyProduction([B, C], [B]),
    ChomskyProduction([A], [a]),
    ChomskyProduction([B], [b]),
]
case_1_productions = [
    ChomskyProduction([S], [A]),
    ChomskyProduction([A, B], [A, B, C]),
    ChomskyProduction([B, C], [B, C, A]),
    ChomskyProduction([A], [a]),
    ChomskyProduction([B], [b]),
]
case_2_productions = [
    ChomskyProduction([S], [a, A]),
    ChomskyProduction([A], [A, B, C]),
    ChomskyProduction([B], [B, C, A]),
    ChomskyProduction([A], [a]),
    ChomskyProduction([B], [b]),
]
case_3_but_different_side_productions = [
    ChomskyProduction([S], [A]),
    ChomskyProduction([A], [B, a]),
    ChomskyProduction([B], [a, B]),
    ChomskyProduction([A], [a]),
    ChomskyProduction([B], [b]),
]
case_3_productions = [
    ChomskyProduction([S], [A, a]),
    ChomskyProduction([A], [B, a]),
    ChomskyProduction([B], [C, b]),
    ChomskyProduction([A], [a]),
    ChomskyProduction([B], [b]),
]


cases: dict[
    str, Sequence[ChomskyProduction] | Callable[[], Sequence[ChomskyProduction]]
] = {
    "Empty LHS": case_empty_lhs_productions,
    "Invalid LHS": case_invalid_lhs_productions,
    "Recursive Enumerable": case_0_productions,
    "Context-sensitive": case_1_productions,
    "Context-free": case_2_productions,
    "Regular With Different Side": case_3_but_different_side_productions,
    "Regular": case_3_productions,
}


def run_example_cases():
    logger.info("Start running test groups...")
    logger.info(f"Test Cases: {pretty_repr(HIERARCHY_TEXT)}")

    for case_name, case_prod in cases.items():
        if callable(case_prod):
            try:
                case_prod = case_prod()
            except Exception as e:
                logger.error(e)
                continue
        # construct grammar
        grammar = ChomskyGrammarSystem(entry=S, productions=case_prod)

        logger.info(f'Executing Test Case: "{case_name}"')
        logger.info(f"Grammar: \n {grammar}")

        logger.success(
            f"Grammar Chomsky Hierarchy: {HIERARCHY_TEXT[grammar.chomsky_hierarchy]} ({grammar.chomsky_hierarchy})"
        )
