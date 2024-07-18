from dataclasses import dataclass

import reg_exp as regex
import automata as fa


class TokenDefinition:
    token_type: str

    # smaller number takes precedence of larger number
    priority: int

    regular_expr: regex.RegularExpr

    fa: fa.FA

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


class LexicalAnalyzer:
    # list of available tokens
    token_definitions: list[TokenDefinition]

    # store the parsed token pair
    token_pairs: list[TokenPair]

    def __init__(self, token_definitions: list[TokenDefinition]):
        # initial token definitions
        token_definitions.sort()
        self.token_definitions = token_definitions
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
                if max_match == 0:
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
                raise RuntimeError('Failed to parse token at place')

        return self.token_pairs