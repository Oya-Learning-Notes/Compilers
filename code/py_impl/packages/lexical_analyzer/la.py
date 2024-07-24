from dataclasses import dataclass

import reg_exp as regex
import automata as fa
from cfg import Terminal, NonTerminal


class TokenDefinition:
    token_type: str

    # smaller number takes precedence of larger number
    priority: int

    regular_expr: regex.RegularExpr

    fa: fa.FA

    def use_dfa(self):
        self.fa = self.fa.to_dfa()

    def __init__(self, token_type: str, regular_expr: regex.RegularExpr, priority: int = 0):
        self.token_type = token_type
        self.priority = priority
        self.regular_expr = regular_expr
        self.fa = self.regular_expr.to_fa()

    def __lt__(self, other):
        return self.priority < other.priority

    def __eq__(self, other):
        return self.token_type == other.token_type


@dataclass
class TokenPair:
    token_type: str
    content: str

    def is_match(self, terminal: Terminal) -> bool:
        """
        Check if this TokenPair match a certain Terminal in CFG.

        By default, this method will consider match if token_type str == terminal.name str
        """
        if not isinstance(terminal, Terminal):
            return False
        if not self.token_type == terminal.name:
            return False
        return True

    def to_terminal(self) -> Terminal:
        """
        Return the corresponding Terminal for this TokenPair.
        :return:
        """
        return Terminal(name=self.token_type)


class LexicalAnalyzer:
    # list of available tokens
    token_definitions: list[TokenDefinition]

    # store the parsed token pair
    token_pairs: list[TokenPair]

    def __init__(self, token_definitions: list[TokenDefinition], use_dfa: bool = True):
        # initial token definitions
        token_definitions.sort()
        self.token_definitions = token_definitions

        # use dfa if needed
        if use_dfa:
            for defs in self.token_definitions:
                defs.use_dfa()

        # init token pairs
        self.token_pairs = []

    def init_state(self):
        self.token_pairs = []

    def parse(self, input_str: str):
        """
        Try parsing input string using this Lexical Analyzer.

        Return List of TokenPair object if success.
        """
        parsed: int = 0

        # parse until all input has been parsed into tokens
        while len(input_str) > 0:
            has_match = False
            # try each token definitions
            for token_defs in self.token_definitions:
                token_defs.fa.test_str(input_str)
                max_match = token_defs.fa.max_match

                # not match at all
                if max_match < 1:
                    continue

                has_match = True
                # has matched prefix in string
                # add token pairs
                self.token_pairs.append(TokenPair(
                    token_type=token_defs.token_type,
                    content=input_str[0:max_match]
                ))
                # update parsed
                parsed += max_match
                # update input str
                input_str = input_str[max_match:]

            # no token matched
            if not has_match:
                raise RuntimeError(f'Failed to parse token, parsed: {parsed}')

        return self.token_pairs
