import cfg
from lexical_analyzer import TokenPair
from cfg import Piece

from errors import BaseError

from . import parse_tree

__all__ = [
    "CFGIncompatibleError",
    "ParseErrorBase",
    "TokenNotMatchError",
    "InvalidParseTreeError",
    "EntryUndefinedError",
    "ParseTreeError",
    "DerivationError",
]


class CFGIncompatibleError(BaseError):
    """
    Throw when the input CFG is incompatible with current parser type

    Params:

    - `parser_type` Name of the parser type, e.g.: LL(1), SLR(1)
    """

    def __init__(self, parser_type: str):
        super().__init__(
            name="incompatible_cfg",
            message=f"Input Context Free Grammar is incompatible with {parser_type} Parser",
        )


class ParseErrorBase(BaseError):
    """
    Raise when error occurred while parsing input token pairs.
    """

    def __init__(
        self,
        name: str = "parse_error",
        message: str = "Error occurred when try to parse input",
    ):
        super().__init__(name, message)


class TokenNotMatchError(ParseErrorBase):
    """
    Raised when the derived terminal leaves in the parse tree does not
    match the one in the input.

    This error should be raised in LL parsers.
    """

    def __init__(self, token: TokenPair, piece: Piece, index: int):
        super().__init__(
            "Token not match the corresponding elements in parse tree. "
            f"Token near position {index} with type {token.token_type} could not match CFG piece {piece}"
        )


class InvalidParseTreeError(ParseErrorBase):
    parse_tree_when_err: parse_tree.ParseTree | None

    def __init__(self, parse_tree_when_err: parse_tree.ParseTree | None = None):
        self.parse_tree_when_err = parse_tree_when_err
        super().__init__("Parse tree invalid at the end of input.")


class EntryUndefinedError(Exception):
    def __init__(self):
        super().__init__(
            "Entry undefined in provided CFG to parser. Please set entry for CFG "
            "before pass it to parser"
        )


class ParseTreeError(Exception):
    # init method should not be rewrite here.
    pass


class DerivationError(ParseTreeError):

    def __init__(self, source: cfg.Piece, target: list[cfg.Piece] | None = None):
        part1 = f"Node element type {source} is not a non-terminal type"
        if target is None:
            part2 = "."
        else:
            part2 = f", and could not be derived into {target}."
        super().__init__(part1 + part2)
