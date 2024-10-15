from dataclasses import dataclass
from loguru import logger

__all__ = [
    "Piece",
    "Terminal",
    "NonTerminal",
    "CFGSystem",
    "Production",
    "Derivation",
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
    pieces: list[Piece] | None  # None means this production could derive into epsilon

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


class CFGSystem:
    def __init__(
        self, production_list: list[Production], entry: Piece | None = None
    ) -> None:
        self.production_list = production_list
        """list to store all productions in this CFG system."""
        self.used_pieces = set()
        self.entry = entry
        """
        indicate the parsing entry of this CFG.
        Could be NonTerminal or Terminal, usually to be NonTerminal
        """
        self.production_dict: dict[NonTerminal, set[Production]] = {}
        """generated production dict, key is source, value is set of Derivation"""
        self.used_pieces: set[Piece] = set()
        """The pieces used in this CFG"""
        #
        self.first_sets: dict[Piece, set[Terminal | None]]
        """
        store first set of each piece
        """
        self.follow_sets: dict[Piece, set[Terminal]]
        """
        store follow set
        """

        self._recur_runtime_set: set[Piece] = set()
        """a tmp set used to record the parameter stack of recursive runtime"""
        self._recur_piece_detected_in_calc_follow: Piece | None = None
        """store the piece that led to recursive circular if exists"""
        self._is_recur_when_calc_follow: bool = True
        """Temp value used internally"""

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
        self.generate_first_set()
        self.generate_follow_set()

    def get_grammar_type(self):
        """
        Return an `int` number representing the chomsky grammar type
        of this Grammar System.
        """

    def generate_production_dict(self):
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

        Raise KeyError if `source` not in this CFG productions
        """
        # notice the data depend on self.generate_production_dict
        derivations: set[Derivation] = set()
        for prod in self.production_dict[source]:
            derivations.add(prod.target)

        return derivations

    def generate_first_set(self) -> None:
        # enable recursive tracking (circular recursive)

        self._recur_runtime_set_first = set()
        self._recur_piece_detected_in_calc_first = None
        self._is_recur_when_calc_first = True

        while self._is_recur_when_calc_first:
            for piece in self.used_pieces:
                self.calc_first_set(piece)
            self._is_recur_when_calc_first = False

    def calc_first_set_of_pieces(self, pieces: list[Piece]) -> set[Piece | None]:
        """
        Calculate FIRST set of a custom pieces.

        When constructing some LR parse table, we may need to calculate the first set of a list of pieces.

        Notice:

        - All pieces in list should be in used_pieces set.
        - Please ensure call ``generate_first_set()`` before calling this method.
        """
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
        piece: NonTerminal  # type mark
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


# a -> bc
# c -> xa
# a -> bxa


# A -> b|Ax
# Change grammar
# A -> bA'
# A'-> x | xA' | e (e means epsilon here)

# A -> BC
# C -> DA
# A -> BC -> BDA,  A ->* BDA, Follow(A) \subset Follow(A)
# ABDBDBDBDBDBDA
