from dataclasses import dataclass
from collections import defaultdict
from typing import cast
from pprint import pformat

from loguru import logger

from errors import BaseError

__all__ = [
    "Piece",
    "Terminal",
    "NonTerminal",
    "CFGSystem",
    "Production",
    "Derivation",
    "NoValidDerivationError",
]


class Piece:
    def __init__(self, name: str):
        self.name: str = name

    # here we actually promise terminal and non-terminal will NEVER has same name
    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if other is None:
            return False

        return self.name == other.name

    def __repr__(self):
        return self.name


class Terminal(Piece):
    pass


class NonTerminal(Piece):
    pass


@dataclass
class Derivation:
    """
    Class that represents the RHS(Right-hand side)
    of a production in CFG(Context-free grammar)
    """

    pieces: list[Piece] | None

    def __init__(self, pieces: list[Piece] | None):

        if pieces is not None and len(pieces) == 0:
            pieces = None

        # None means this production could derive into epsilon
        self.pieces: list[Piece] | None = pieces

    def __hash__(self):
        if self.pieces is None:
            return hash(None)
        return hash(tuple(self.pieces))

    def __repr__(self) -> str:
        repr_str = ""
        if self.pieces is None:
            return "\\e"
        for piece in self.pieces:
            repr_str += repr(piece)
        return repr_str


@dataclass
class Production:
    source: NonTerminal
    target: Derivation

    def __hash__(self):
        return hash(tuple([self.source, self.target]))

    def __repr__(self) -> str:
        repr_str = f"{repr(self.source)} -> {repr(self.target)}"
        return repr_str


class NoValidDerivationError(BaseError):
    """
    Raised when CFGSystem could not found any derivations of a NonTerminal.
    """

    def __init__(
        self,
        name: str = "no_valid_derivation",
        message: str | None = None,
        lhs: NonTerminal | None = None,
    ):
        if message is None:
            message = (
                f"Could not found any derivations that use a certain non terminal."
            )
        if lhs is not None:
            message += f" (Non terminal: {lhs})"
            message += (
                " This non terminal is most likely to be unused terminal and "
                "all productions relavant to this non terminal should be removed from grammar."
            )
        super().__init__(name=name, message=message)


class CFGSystem:
    def __init__(
        self, production_list: list[Production], entry: Piece | None = None
    ) -> None:
        self.production_list = production_list
        """list to store all productions in this CFG system."""

        self.entry = entry
        """
        indicate the parsing entry of this CFG.
        Could be NonTerminal or Terminal, usually to be NonTerminal
        """

        self.production_dict: dict[NonTerminal, set[Production]] = {}
        """generated production dict, key is source, value is set of Derivation"""

        self.used_pieces: set[Piece] = set()
        """The pieces used in this CFG"""

        self.first_sets: dict[Piece, set[Terminal | None]] = {}
        """
        store first set of each piece
        """
        self.follow_sets: dict[Piece, set[Terminal | None]] = {}
        """
        store follow set of NonTerminal
        
        Follow set of terminal has no use cases in parser. 
        
        For the meaning of `None` inside follow set, checkout docstring 
        of follow set generating function `generate_follow_set_iteratively()`
        """

        self._recur_runtime_set: set[Piece] = set()
        """a tmp set used to record the parameter stack of recursive runtime"""
        self._recur_piece_detected_in_calc_follow: Piece | None = None
        """store the piece that led to recursive circular if exists"""
        self._is_recur_when_calc_follow: bool = True
        """Temp value used internally"""

        # following are also temporary values.
        # the meaning and usage is similar to variables above,
        # with the only difference that these values are used
        # when calculating first sets.
        self._recur_runtime_set_first: set[Piece] = set()
        self._recur_piece_detected_in_calc_first: Piece | None = None
        self._is_recur_when_calc_first: bool = True

        # init used_pieces
        for prod in self.production_list:
            # add source
            self.used_pieces.add(prod.source)

            # add target
            if prod.target.pieces is None:  # skip epsilon pieces
                continue
            for t in prod.target.pieces:
                # None should not be included in used_pieces
                if t is None:
                    continue
                self.used_pieces.add(t)

        # check if entry is in the used pieces
        if (self.entry is not None) and (self.entry not in self.used_pieces):
            raise RuntimeError(
                "Defined CFG entry must in the used pieces of this CFG. "
                f"Current entry {self.entry} not in set of used pieces."
            )

        self.generate_production_dict()

        # here use newly created iterative method instead of old
        # patched recursive method (since the new one is more elegant lol)
        self.generate_first_set_iteratively()
        self.generate_follow_set_iteratively()

    def generate_production_dict(self):
        """
        Generate production dictionary based on `self.production_list`
        """
        # init dict
        self.production_dict = {}

        for prod in self.production_list:
            source = prod.source

            # if dict key non exist, init set first
            if self.production_dict.get(source) is None:
                self.production_dict[source] = set()

            # add new derivation to set
            self.production_dict[source].add(prod)

    def get_all_derivation(self, source: NonTerminal) -> set[Derivation]:
        """
        Return a set of all derivations of the received `source`.

        Return empty set if `source` not in any RHS this CFG productions
        """
        # notice the data depend on self.generate_production_dict
        derivations: set[Derivation] = set()
        try:
            for prod in self.production_dict[source]:
                derivations.add(prod.target)
        except KeyError as e:
            raise NoValidDerivationError(lhs=source) from e

        return derivations

    def generate_first_set(self) -> None:
        """
        Deprecated. Generate first set recursively for all pieces in this CFG.

        Use generate_first_set_iteratively() instead.
        """
        # enable recursive tracking (circular recursive)

        self._recur_runtime_set_first = set()
        self._recur_piece_detected_in_calc_first = None
        self._is_recur_when_calc_first = True

        while self._is_recur_when_calc_first:
            for piece in self.used_pieces:
                self.calc_first_set(piece)
            self._is_recur_when_calc_first = False

    def calc_first_set_of_pieces(
        self, pieces: list[Piece] | None
    ) -> set[Terminal | None]:
        """
        Calculate first set of a custom pieces.

        Notice:

        - All pieces in list should be in used_pieces set.
        - Please ensure `generate_first_set_iteratively()` be called before calling this method.
        """
        if pieces is None:
            return {None}

        # raise runtime error if list empty
        if len(pieces) == 0:
            raise RuntimeError(
                "Pieces could not be empty when calculating its FIRST set."
            )

        # the flag indicates if all previous scanned piece could be None.
        contains_epsilon_until_now: bool = True

        # store the result of calculated first set
        res_first_set: set[Terminal | None] = set()

        for piece in pieces:
            # retrieve first set for this piece
            first_set_for_current_piece = self.first_sets[piece]

            # Add the first set of current piece to the result if previous pieces could all be derived into epsilon
            if contains_epsilon_until_now:
                res_first_set.update(first_set_for_current_piece)
            else:
                break

            # if current piece could not be derived into epsilon, update flag to false.
            if not (None in first_set_for_current_piece):
                contains_epsilon_until_now = False

        # if not all pieces could be converted into epsilon, then epsilon not in ret_first_set
        if not contains_epsilon_until_now:
            try:
                res_first_set.remove(None)
            except KeyError:
                pass
        else:
            res_first_set.add(None)

        return res_first_set

    def calc_first_set(
        self, piece: Piece, enable_recur_detect: bool = True
    ) -> set[Terminal | None]:
        """
        Calculate the first set of a piece.

        This method currently do NOT support CFG system that may cause Left Recursive.
        """
        try:
            return self.first_sets[piece]
        except KeyError:
            pass

        # circular dependency detected, return empty set first
        if enable_recur_detect and (piece in self._recur_runtime_set_first):
            self._recur_piece_detected_in_calc_first = piece
            self._is_recur_when_calc_first = True
            return set()
        self._recur_runtime_set_first.add(piece)

        # if piece is terminal, return set with only itself inside.
        if isinstance(piece, Terminal):
            self.first_sets[piece] = {piece}
            return {piece}

        # if it's non-terminal, first of all, get all possible derivation
        piece = cast("NonTerminal", piece)
        first_set: set[Terminal | None] = set()
        contains_epsilon: bool = False
        derivations_set: set[Derivation] = self.get_all_derivation(piece)

        # deal with each RHS with current NonTerminal as source.
        for derivation in derivations_set:

            # if this non-terminal could be derived to epsilon, then first set contains epsilon
            if derivation.pieces is None:
                contains_epsilon = True
                continue

            # loop through each part of the derivation
            all_contains_epsilon_until_now: bool = True
            for cur_piece in derivation.pieces:
                # not need to continue in this case
                if not all_contains_epsilon_until_now:
                    break

                # calc first set of current part
                cur_piece_first_set = self.calc_first_set(cur_piece)

                # if all first set of the parts before contains epsilon
                # then first set of this part should be added to first set of the source
                if all_contains_epsilon_until_now:
                    first_set.update(cur_piece_first_set)

                if not (None in cur_piece_first_set):
                    all_contains_epsilon_until_now = False

            if all_contains_epsilon_until_now:
                contains_epsilon = True

        # add epsilon into the set if needed
        if contains_epsilon:
            first_set.add(None)
        else:
            try:
                first_set.remove(None)
            except KeyError:
                pass

        # check if that the circular dependency error is cause by this piece
        if (
            enable_recur_detect
            and (self._recur_piece_detected_in_calc_first is not None)
            and (piece == self._recur_piece_detected_in_calc_first)
        ):
            # remove the recur flag
            self._recur_piece_detected_in_calc_first = None

        # update catch if this result is final and valid
        if (not enable_recur_detect) or (
            self._recur_piece_detected_in_calc_first is None
        ):
            self.first_sets[piece] = first_set
        return first_set

    def generate_first_set_iteratively(self) -> None:
        """
        Generate first set of all used pieces using iterative method.
        """

        current_first_sets_state: dict[Piece, set[Terminal | None]] = defaultdict(set)
        """
        Store current state of first sets info.
        
        This state will mutated with the iteration going forward, 
        and at the time that iteration will not make any update 
        on the state, the algorithm finished.
        """
        # for more info about default dict, checkout:
        # https://docs.python.org/3/library/collections.html#collections.defaultdict

        def calc_first_set_based_on_curr_state() -> bool:
            nonlocal current_first_sets_state

            mutated: bool = False

            for piece in self.used_pieces:

                piece_fisrt_set = current_first_sets_state[piece]
                """Current first set state of currently processing piece"""

                prev_first_set_size = len(piece_fisrt_set)

                # if piece is terminal, return set with only itself inside.
                if isinstance(piece, Terminal):
                    piece_fisrt_set.add(piece)
                    if len(piece_fisrt_set) > prev_first_set_size:
                        mutated = True
                    continue

                # if it's non-terminal, first of all, get all possible derivation

                piece = cast("NonTerminal", piece)  # type narrowed to non-terminal

                # record that if this non-terminal could deduce to epsilon
                contains_epsilon: bool = False

                # all possible derivation sequence that use this non-terminal as LHS
                derivations_set: set[Derivation] = self.get_all_derivation(piece)

                # deal with each RHS with current NonTerminal as source
                # update first set state in plcae
                for derivation in derivations_set:

                    # if this non-terminal could be derived to epsilon, then first set contains epsilon
                    if derivation.pieces is None:
                        contains_epsilon = True
                        continue

                    # loop through each part of the derivation
                    all_contains_epsilon_until_now: bool = True
                    for cur_piece_in_derivation in derivation.pieces:

                        # here means some symbol before this piece is non-epsilonable
                        # not need to continue in this case, this symbol will not affect first set
                        if not all_contains_epsilon_until_now:
                            break

                        # use current first set state
                        cur_piece_first_set = current_first_sets_state[
                            cur_piece_in_derivation
                        ]

                        # if all first set of the parts before contains epsilon
                        # then first set of this part should be added to first set of the source
                        piece_fisrt_set.update(cur_piece_first_set)

                        if not (None in cur_piece_first_set):
                            all_contains_epsilon_until_now = False

                    if all_contains_epsilon_until_now:
                        contains_epsilon = True

                # add epsilon into the set if needed
                if contains_epsilon:
                    piece_fisrt_set.add(None)
                else:
                    try:
                        piece_fisrt_set.remove(None)
                    except KeyError:
                        pass

                # check if first set size changed
                if len(piece_fisrt_set) > prev_first_set_size:
                    mutated = True

            return mutated

        # if the state mutated, calc_first_set_based_on_curr_state will return True
        # which will cause loop continue, until nothing changed anymore.
        while calc_first_set_based_on_curr_state():
            pass

        # adopt the final state as the result of first sets
        self.first_sets = current_first_sets_state

    def generate_follow_set(self) -> None:
        """
        Calculate the follow set of a piece.

        Must call generate_first_set() before calling this method.
        """
        # enable recursive tracking
        self._recur_runtime_set = set()
        self._recur_piece_detected_in_calc_follow = None
        self._is_recur_when_calc_follow = True

        while self._is_recur_when_calc_follow:
            self._is_recur_when_calc_follow = False
            for piece in self.used_pieces:
                self.calc_follow_set(piece)

    def calc_follow_set(
        self, piece: Piece, enable_recur_detect: bool = True
    ) -> set[Terminal | None]:
        logger.debug(f"Calculating follow set of {self}")
        # try using cache
        try:
            return self.follow_sets[piece]
        except KeyError:
            pass

        # if detected recursive call, return an empty set
        if enable_recur_detect and (piece in self._recur_runtime_set):
            self._recur_piece_detected_in_calc_follow = piece
            self._is_recur_when_calc_follow = True
            return set()
        self._recur_runtime_set.add(piece)

        follow_set: set[Terminal | None] = set()

        # iterate through each production
        for prod in self.production_list:
            source = prod.source
            all_contains_epsilon_until_now: bool = True

            # if the RHS is epsilon, skip processing
            if prod.target.pieces is None:
                continue

            # get number of pieces
            pieces_count = len(prod.target.pieces)

            # loop through each part in derivation from end to beginning
            for i in range(pieces_count - 1, -1, -1):
                cur_piece = prod.target.pieces[i]
                cur_piece_first_set = self.first_sets[cur_piece]

                # only try updating follow set if current piece it the one we are processing
                if cur_piece == piece:

                    # if this is the last element || not the last, but all part behind it could become epsilon
                    # then follow(source) \subset follow(piece)
                    if all_contains_epsilon_until_now:
                        # logger.debug(f'In production: {prod}, Piece: {cur_piece}')
                        # logger.debug(f'Request calculate Following({source})')
                        if source != piece:
                            follow_set.update(self.calc_follow_set(source))

                    # if not the last one, add the first set of the following piece
                    if i < pieces_count - 1:
                        follow_set.update(
                            self.calc_first_set(prod.target.pieces[i + 1])
                        )

                # update states
                if not (None in cur_piece_first_set):
                    all_contains_epsilon_until_now = False

        # remove epsilon (we don't need it in follow set)
        try:
            follow_set.remove(None)
        except KeyError:
            pass

        # if current recur pieces not None, we need to check if this piece is the one that cause recur circle
        # if it is, then after this, the flag should be removed since the recur circle has been resolved
        if (
            enable_recur_detect
            and (self._recur_piece_detected_in_calc_follow is not None)
            and (piece == self._recur_piece_detected_in_calc_follow)
        ):
            # update recur piece flag if it's not in stack anymore
            self._recur_piece_detected_in_calc_follow = None

        # update cache when this result is the final
        if (not enable_recur_detect) or (
            self._recur_piece_detected_in_calc_follow is None
        ):
            self.follow_sets[piece] = follow_set

        # remove piece from runtime stack
        try:
            self._recur_runtime_set.remove(piece)
        except KeyError:
            pass

        return follow_set

    def generate_follow_set_iteratively(self) -> None:
        """
        Generate follow set of all used pieces using iterative method.
        Must call generate_first_set_iterative() before calling this method.

        Note that `None` in follow set indicates that
        this symbol is deductable/productable under any condition.

        In the following algorithm, we put `None` inside the follow set of start symbol,
        essentially means:
        - In LL parser, When faced with any production with start symbol as LHS, perform production.
          (Actually there should be only one production use start symbol as LHS, so there
          should NOT be a chance that program use start set or follow set to resolve conflict)
        - When faced with any reducable-string that reduced to the start symbol using Bottom-up parser,
          reduce with no limit.
          This indicates that there should be NO any production that has
          a reduce-reduce conflict with Production that use start symbol as left-hand side.
          (In augmented grammar, there should be only one grammar related to start symbol S')
          Or in another case,  such conflict doesn't matter. (For example, start symbol S could produce lot of
          different derivation which may cause reduce-reduce error, however they all reduced to
          start symbol, so conflict doesn't matter)
        """
        logger.debug("Start generating follow set iteratively...")
        current_follow_sets_state: dict[Piece, set[Terminal | None]] = defaultdict(set)

        # Start symbol's follow set includes end-of-input marker (None or "$")
        start_symbol = self.entry
        if start_symbol is not None:
            # None in follow set represent reducuction with no limit.
            current_follow_sets_state[start_symbol].add(None)

        def calc_follow_set_based_on_curr_state() -> bool:
            nonlocal current_follow_sets_state
            mutated: bool = False

            # iterate all productions
            for cur_prod in self.production_list:
                cur_prod_source = cur_prod.source

                # If RHS is epsilon, skip processing
                if cur_prod.target.pieces is None:
                    continue

                # Temporary follow set for lhs of currently processing production
                # used in later loop to update follow set of rhs
                cur_lhs_follow_set: set[Terminal | None] = current_follow_sets_state[
                    cur_prod_source
                ]

                # at this point, RHS must NOT be empty

                # For production A -> ab...xyz, add follow(A) to follow(z) unconditionally
                right_most_symbol_follow_set = current_follow_sets_state[
                    cur_prod.target.pieces[-1]
                ]
                prev_len = len(right_most_symbol_follow_set)

                right_most_symbol_follow_set.update(cur_lhs_follow_set)

                if len(right_most_symbol_follow_set) > prev_len:
                    mutated = True

                # bool flag used in following loop
                all_contains_epsilon_until_now: bool = True

                pieces_count = len(cur_prod.target.pieces)
                # loop through each part in derivation in reverse order
                for i in range(pieces_count - 1, -1, -1):

                    # extract some values for later ref

                    cur_piece = cur_prod.target.pieces[i]

                    cur_piece_follow_set = current_follow_sets_state[cur_piece]

                    # first set should be calculated already by calling generated_first_set_iteratively()
                    cur_piece_first_set = self.first_sets[cur_piece]

                    # store size of follow set of current piece before change
                    # used later to decided if state mutated
                    cur_piece_prev_len = len(cur_piece_follow_set)

                    # read next piece first set and follow set if exists
                    # (that is, if this is not the last piece, and for follow set, this is nonterminal)
                    # used later to update follow set of current piece
                    next_piece_first_set = None
                    next_piece_follow_set = None

                    if i != pieces_count - 1:
                        next_piece = cur_prod.target.pieces[i + 1]

                        # get first set
                        next_piece_first_set = self.first_sets[next_piece]
                        # get follow set if it's nonterminal
                        if isinstance(cur_prod.target.pieces[i + 1], NonTerminal):
                            next_piece_follow_set = current_follow_sets_state[
                                next_piece
                            ]

                    # if next symbol could produce epsilon, add follow(next) to follow(cur)
                    if (
                        next_piece_first_set is not None  # exists
                        and None in next_piece_first_set  # could produce epsilon
                    ):
                        if (
                            next_piece_follow_set is not None
                        ):  # follow set exists (is nonterminal)
                            cur_piece_follow_set.update(next_piece_follow_set)

                    # # then add follow(source) to follow(piece)
                    # if all_contains_epsilon_until_now:
                    #     # DEBUG
                    #     if None in cur_lhs_follow_set:
                    #         breakpoint()

                    #     cur_piece_follow_set.update(cur_lhs_follow_set)

                    #     # if this piece could not reduce to epsilon (None not in the first set)
                    #     # then update flag
                    #     if None not in cur_piece_first_set:
                    #         all_contains_epsilon_until_now = False

                    # if not the last one, add the first set of the following piece
                    # to the follow set of current piece
                    if next_piece_first_set is not None:
                        cur_piece_follow_set.update(next_piece_first_set - {None})

                    # check if cur_piece is mutated
                    if len(cur_piece_follow_set) > cur_piece_prev_len:
                        mutated = True

            return mutated

        # Iterate until no mutation occurs
        while calc_follow_set_based_on_curr_state():
            pass

        # Adopt the final state as the result of follow sets
        self.follow_sets = current_follow_sets_state

    def eliminate_left_recursive(self) -> "CFGSystem":
        """
        Return a NEW CFGSystem instance that based on current instance
        but with all direct and indirect left recursions eliminated

        Left recursive elimination algorithm is based on the one on Wikipedia:
        https://en.wikipedia.org/wiki/Left_recursion
        """

        # record a set of non-terminals that already does not contains
        processed_derivations_set: set[NonTerminal] = set()

        # record the newly generated source and derivations pairs.
        # used later to generate new productions.
        new_derivations_dict: dict[NonTerminal, set[Derivation]] = defaultdict(set)

        def _replace_beginning_non_terminal_using_processed(
            derivations: set[Derivation],
        ) -> tuple[set[Derivation], bool]:
            """
            Returns a new set of replaced derivations, and a flag that indicates
            if a replaced occurred.

            For a set of derivations(RHS), if the first symbol is non-terminal,
            and that non-terminal is in processed non-terminal set, then
            replace that non-terminal with all possible derivations from it.

            This is in order to gradually convert indirect left recursive to
            direct left recursive.

            Checkout the detail of left recursive algorithm for more info.
            """

            nonlocal processed_derivations_set
            nonlocal new_derivations_dict

            # store the modified derivations set
            new_derivations_set: set[Derivation] = set()

            # flag to indicate replace occurred
            replace_occurred: bool = False

            # deal with all input derivations
            for cur_derivation in derivations:

                # epsilon production, skip
                if cur_derivation.pieces is None:
                    new_derivations_set.add(cur_derivation)
                    continue

                cur_deri_first_piece = cur_derivation.pieces[0]

                # if the first symbol is not a non-terminal, skip
                if not isinstance(cur_deri_first_piece, NonTerminal):
                    new_derivations_set.add(cur_derivation)
                    continue

                # at this point, first symbol is a non-terminal

                # that first non-terminal is not in processed list, skip
                if not cur_deri_first_piece in processed_derivations_set:
                    new_derivations_set.add(cur_derivation)
                    continue

                # at this point, a replace must happen
                replace_occurred = True

                # replace it with all possible derivations
                # e.g.: For a derivation [A]bc, we are doing [...]bc where
                # [...] is all possible derivation of A.
                #
                # And based on the left recursion eliminate algorithm,
                # here A must already be in the new_derivations_dict,
                # or you can say, it must be in the list of already-processed nonterminal
                all_possible_derivations = new_derivations_dict[cur_deri_first_piece]
                rest_pieces_without_first_symbol = cur_derivation.pieces[1:]

                for replace_deri in all_possible_derivations:
                    # construct new list of pieces
                    # [replace_part_pieces] + [original_pieces_without_first_symbol]
                    new_pieces: list[Piece] | None = []
                    if replace_deri.pieces is not None:
                        new_pieces.extend(replace_deri.pieces)  # type:ignore
                    new_pieces.extend(rest_pieces_without_first_symbol)  # type:ignore

                    if len(new_pieces) == 0:  # type:ignore
                        new_pieces = None

                    new_derivations_set.add(Derivation(pieces=new_pieces))

            return (new_derivations_set, replace_occurred)

        def replace_beginning_non_terminal_using_processed(
            derivations: set[Derivation],
        ) -> set[Derivation]:
            new_derivations = derivations

            _iteration_count = 0

            while True:
                _iteration_count += 1
                (new_derivations, replace_occurred) = (
                    _replace_beginning_non_terminal_using_processed(new_derivations)
                )
                if not replace_occurred:
                    break

                if _iteration_count > 50:
                    raise RuntimeError(
                        "Too many iterations when replacing non-terminal "
                        "in left recursive eliminination process which is unusual. "
                        "Check if the algorithm is correct. "
                    )
            logger.debug(
                f"Nonterminal replacement finished within {_iteration_count} iteration(s)"
            )

            return new_derivations

        def generate_new_nonterminal(base_symbol: str) -> NonTerminal:
            """
            Return a new NonTerminal instance generated based on `base_symbol`

            When eliminating direct left recursive, we may need to create set of
            new productions with new NonTerminal as LHS.
            For example, A -> Ab | c may be converted to A -> bA' | c,
            where A' -> x | xA' | e (A' is a new NonTerminal instance)

            This function will return a non terminal symbol that not appeared in:
            - Symbol name in `self.used_pieces`
            - Symbol name in `new_derivations_dict`
            """
            nonlocal self
            nonlocal new_derivations_dict

            used_name_set: set[str] = set()

            for p in self.used_pieces:
                used_name_set.add(p.name)

            for p in new_derivations_dict.keys():
                used_name_set.add(p.name)

            new_symbol_name = base_symbol + "'"

            while new_symbol_name in used_name_set:
                new_symbol_name += "'"

            return NonTerminal(name=new_symbol_name)

        def eliminate_direct_left_recursive(
            source: NonTerminal, derivations: set[Derivation]
        ) -> set[Production]:
            """
            This function focus on all productions that shares identical LHS.
            Productions passed in a form of single LHS as `source` and
            set of all possible derivations(RHS) as `derivations`

            Detect direct left recursive in given productions,
            output a new set of derivations that without direct recursive.

            If no left recursive detected, return the derivations unchanged.
            """

            logger.debug(f"Checking direct left recursive relavant to {source}")

            recursive_derivations_set: set[Derivation] = set()
            non_recursive_derivations_set: set[Derivation] = set()

            modified_productions_set: set[Production] = set()

            # iterate through all derivations
            # seperate recursive and non-recursive derivations
            for cur_derivation in derivations:
                cur_pieces = cur_derivation.pieces

                # epsilon derivations, skip
                if cur_pieces is None:
                    non_recursive_derivations_set.add(cur_derivation)
                    continue

                cur_first_piece = cur_pieces[0]
                # first piece is source, this is left recursive derivation
                if cur_first_piece == source:
                    recursive_derivations_set.add(cur_derivation)
                # first piece is not source, non recursive
                else:
                    non_recursive_derivations_set.add(cur_derivation)

            # if no recursive detected, return original derivations unchanged
            if len(recursive_derivations_set) == 0:
                logger.debug("No direct left recursive detected")

                for cur_derivation in derivations:
                    modified_productions_set.add(
                        Production(source=source, target=cur_derivation)
                    )

                return modified_productions_set

            # at this point, there must be some left-recursive derivations
            # deal with them

            # create new util LHS symbol
            new_lhs: NonTerminal = generate_new_nonterminal(source.name)

            logger.debug(
                f"Direct left recursive detected, creating new util non terminal {new_lhs}"
            )
            logger.debug(
                f"Direct recursive derivations: \n {pformat(recursive_derivations_set)}"
            )

            # For all A -> y, Add A -> yA'
            for cur_derivation in non_recursive_derivations_set:

                # get "y" part
                cur_pieces = cur_derivation.pieces
                if cur_pieces is None:
                    cur_pieces = []

                cur_pieces = cast("list[Piece]", cur_pieces)  # for type hint

                # construct new pieces
                new_pieces = cur_pieces + [new_lhs]  # y + A' = yA'
                # add derivations to modified set
                modified_productions_set.add(
                    Production(source=source, target=Derivation(pieces=new_pieces))
                )  # A' -> yA'

            # For all A -> Ax, change it to A' -> xA'
            for cur_derivation in recursive_derivations_set:
                cur_pieces = cur_derivation.pieces

                # the pieces should not be none, because at least, there would be
                # a single non-terminal "A" at the first that causes left recursive
                assert (
                    cur_pieces is not None
                ), "Recursive derivations produce epsilon, which is impossible."

                # get "x" part
                non_recursive_pieces = cur_pieces[1:]

                # construct new pieces
                new_pieces = cur_pieces[1:] + [new_lhs]  # x + A' = xA'
                # add derivations to modified set
                modified_productions_set.add(
                    Production(source=new_lhs, target=Derivation(pieces=new_pieces))
                )

            # add A' -> epsilon
            modified_productions_set.add(
                Production(source=new_lhs, target=Derivation(pieces=None))
            )

            logger.debug(f"Modified productions: \n{pformat(modified_productions_set)}")

            return modified_productions_set

        # get all nonterminal
        non_terminals = [p for p in self.used_pieces if isinstance(p, NonTerminal)]

        # iterate through each non-terminal, eliminate it's recursive, then generate new productions
        for cur_nonterminal in non_terminals:
            logger.debug(f"Processing non terminal {cur_nonterminal}")
            # get all derivations of current nonterminal
            cur_derivations = self.get_all_derivation(cur_nonterminal)

            # replace beginning non-terminal with processed derivations
            cur_derivations = replace_beginning_non_terminal_using_processed(
                cur_derivations
            )

            # eliminate direct left recursive
            modified_productions_set = eliminate_direct_left_recursive(
                cur_nonterminal, cur_derivations
            )

            # add to new derivations dict
            for p in modified_productions_set:
                new_derivations_dict[p.source].add(p.target)

            # add this nonterminal to processed
            processed_derivations_set.add(cur_nonterminal)

        # construct all new productions based on derivations set
        new_productions: set[Production] = set()
        for source, derivations in new_derivations_dict.items():
            for target in derivations:
                new_productions.add(Production(source=source, target=target))

        return CFGSystem(production_list=list(new_productions), entry=self.entry)
