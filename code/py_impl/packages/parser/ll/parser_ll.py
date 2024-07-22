from copy import copy
import cfg
from lexical_analyzer import TokenPair

from .. import errors as general_err
from ..parse_tree import ParseTree, ParseTreeNode

__all__ = [
    'LLParser',
    'LLParseTable',
    'NoValidMove',
    'ParseTableConflictError',
]


class LLParseTable:
    """
    Implementation of LL(1) parse table, but using dict and hash algorithm instead of 2-dim array.
    """
    # the Context-Free Grammar of this LL parse table
    cfg_system: cfg.CFGSystem

    # dict to store parse table item.
    # Pattern: parse_table[non_terminal][lookahead] = derivation
    parse_dict: dict[cfg.NonTerminal, dict[cfg.Terminal, cfg.Production]]

    def __init__(self, cfg_system: cfg.CFGSystem):
        self.cfg_system = cfg_system
        self.parse_dict = {}
        self.generate_parse_table()

        # raise error if not entry provided
        if self.cfg_system.entry is None:
            raise general_err.EntryUndefinedError()

    def generate_parse_table(self):
        """
        Try generating parse table for CFG
        """
        for prod in self.cfg_system.production_list:
            source = prod.source
            target = prod.target

            # if target is epsilon, add follow set of source
            if target.pieces is None:
                source_follow_set = self.cfg_system.follow_sets[source]
                for terminal in source_follow_set:
                    self.set(source, terminal, prod)
                continue

                # deal with item in first set
            target_first_set = self.cfg_system.first_sets[target.pieces[0]]
            for terminal in target_first_set:
                self.set(source, terminal, prod)

            # if first set could be epsilon, then add epsilon set
            if not (None in target_first_set):
                continue
            target_follow_set = self.cfg_system.follow_sets[target.pieces[0]]
            for terminal in target_follow_set:
                self.set(source, terminal, prod)

    def get(self, non_terminal: cfg.NonTerminal, lookahead: cfg.Terminal | TokenPair) -> cfg.Production:
        """
        Try get item from parse dict

        Exceptions:

        Raise ``DerivationNotFoundError`` when item not found in parse table.
        """
        # convert token pair to Terminal instance if needed
        terminal: cfg.Terminal = lookahead
        if isinstance(lookahead, TokenPair):
            terminal = cfg.Terminal(name=lookahead.token_type)

        try:
            return self.parse_dict[non_terminal][terminal]
        except KeyError:
            raise NoValidMove(non_terminal, terminal)

    def set(self, non_terminal: cfg.NonTerminal, lookahead: cfg.Terminal, production: cfg.Production) -> None:
        """
        Try to set item from parse dict

        Exceptions:
        - ``ParseTableConflictError`` when parse table conflict detected.
        :return:
        """
        # check move conflict
        try:
            res = self.get(non_terminal, lookahead)  # expected to raise DerivationError here

            # item already exists, return
            if res == production:
                return

                # if already have result, then parse table conflict occurred
            raise ParseTableConflictError(
                non_terminal,
                lookahead,
                {res, production}
            )
        except NoValidMove:
            pass

        # add move
        self.parse_dict.setdefault(non_terminal, {})
        self.parse_dict[non_terminal][lookahead] = production


class LLParser:
    parse_table: LLParseTable

    _token_list: list[TokenPair]
    _parsed_count: int
    _total_token_count: int
    _parse_tree: ParseTree
    _lookahead: TokenPair | None
    _epsilon_terminal: cfg.Terminal | None

    def __init__(self, cfg_system: cfg.CFGSystem, epsilon_terminal: cfg.Terminal | None = None):
        self._epsilon_terminal = epsilon_terminal
        try:
            # init parse table
            self.parse_table = LLParseTable(cfg_system)
        except Exception as e:
            raise general_err.CFGIncompatibleError(parser_type='LL(1)') from e

    def init_state(self, token_list: list[TokenPair]) -> None:
        """
        Initialize parser for next parsing.
        """
        self._token_list = token_list
        self._total_token_count = len(token_list)
        self._parsed_count = 0

        # init parse tree
        entry_piece = self.parse_table.cfg_system.entry
        if entry_piece is None:
            raise general_err.EntryUndefinedError()
        self._parse_tree = ParseTree(
            start_nodes=[ParseTreeNode(node_type=self.parse_table.cfg_system.entry)],
            epsilon_terminal=self._epsilon_terminal,
        )
        self._lookahead = self._token_list[0]

    def parse_token(self, token_list: list[TokenPair]) -> ParseTree:
        """
        Try to parse the input token list.

        Return ParseTree object if success.

        Errors:
        - ``InvalidParseTreeError``
        - ``ParseError``
        - ...
        """
        self.init_state(token_list)

        # set token list
        self._token_list = copy(token_list)

        # loop while not fully parsed
        while self._total_token_count > self._parsed_count:
            self._match_terminal_forward()
            self._derive_leftmost_non_terminal()

        # check if parse tree valid
        if not self._parse_tree.is_valid():
            raise general_err.InvalidParseTreeError(self._parse_tree)

        return self._parse_tree

    def _derive_leftmost_non_terminal(self):
        non_terminal_info = self._parse_tree.get_first_non_terminal_info()
        # no terminal found
        if non_terminal_info is None:
            return
            # retrieve info
        index = non_terminal_info[0]
        node = non_terminal_info[1]

        # get source of production
        source = node.node_type
        if not isinstance(source, cfg.NonTerminal):
            raise general_err.DerivationError(source)

        # use parse table to get move
        move_info = self.parse_table.get(source, self._lookahead)

        # update parse tree
        new_pieces = move_info.target.pieces
        self._parse_tree.derive_non_terminal(index, new_pieces)

    def _match_terminal_forward(self):
        """
        Try match token list with terminal leaves in parse tree.

        If match success, will update ``_parsed_count`` and ``lookahead``

        Exceptions:
        - ``TokenNotMatchError``
        :return:
        """
        info = self._parse_tree.get_first_non_terminal_info()

        # match range: [match_start, match_end)
        match_start: int = self._parsed_count
        match_end: int = -1
        if info is None:
            match_end = self._total_token_count
        else:
            match_end = info[0]

        # skip if no need to forward
        if match_start >= match_end:
            return

            # loop to check if all newly derived terminal match the corresponding token pair
        for idx in range(match_start, match_end):
            # retrieve info
            token_pair = self._token_list[idx]
            node_type: cfg.Piece = self._parse_tree.leaves[idx].node_type

            node_type: cfg.Terminal  # it should be terminal if the get_first_non_terminal_info() method is correct
            is_match = token_pair.is_match(node_type)

            # if piece and token not match, raise error
            if not is_match:
                raise general_err.TokenNotMatchError(token=self._token_list[idx], piece=node_type, index=idx)

        # match success, update parsed index and lookahead
        self._parsed_count = match_end
        if self._parsed_count >= self._total_token_count:
            self._lookahead = None
        else:
            self._lookahead = self._token_list[match_end]


class NoValidMove(Exception):
    def __init__(self, non_terminal: cfg.NonTerminal, lookahead: cfg.Terminal):
        super().__init__(f'Could not found derivation for NonTerminal {non_terminal} with lookahead {lookahead}')


class ParseTableConflictError(Exception):
    def __init__(
            self,
            non_terminal: cfg.NonTerminal,
            lookahead: cfg.Terminal,
            conflict_moves: set[cfg.Production],
    ):
        super().__init__(
            f'Move conflict occurred when generating LL(1) Parse Table on '
            f'NonTerminal {non_terminal} with lookahead {lookahead}. '
            f'Sets of conflict moves: {conflict_moves}, '
            f'perhaps a left factoring is needed. '
        )
