from dataclasses import dataclass
from loguru import logger


@dataclass
class Piece:
    name: str

    # here we actually promise terminal and non-terminal will NEVER has same name
    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
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
        repr_str = ''
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
        repr_str = f'{repr(self.source)} -> {repr(self.target)}'
        return repr_str


class CFGSystem:
    # list to store all productions in this CFG system.
    production_list: list[Production]

    # generated production dict, key is source, value is set of Derivation
    production_dict: dict[NonTerminal, set[Derivation]]

    # record all used pieces
    used_pieces: set[Piece]

    # store first set of each piece
    first_sets: dict[Piece, set[Terminal | None]]

    # store follow set
    follow_sets: dict[Piece, set[Terminal]]

    def __init__(self, production_list: list[Production]) -> None:
        self.production_list = production_list
        self.used_pieces = set()
        # init used_pieces
        for prod in self.production_list:
            self.used_pieces.add(prod.source)
            for t in prod.target.pieces:
                # None should not be included in used_pieces
                if t is None:
                    continue
                self.used_pieces.add(t)

        self.generate_production_dict()

        self.first_sets = {}
        self.follow_sets = {}

        self.generate_first_set()
        self.generate_follow_set()

    def generate_production_dict(self):
        # init dict
        self.production_dict = {}

        for prod in self.production_list:
            source = prod.source

            # if dict key non exist, init set first
            if self.production_dict.get(source) is None:
                self.production_dict[source] = set()

            # add new derivation to set
            self.production_dict[source].add(prod.target)

    def get_all_derivation(self, source: NonTerminal) -> set[Derivation]:
        """
        Return a set of all derivations of the received `source`.

        Raise KeyError if `source` not in this CFG productions
        """
        # notice the data depend on self.generate_production_dict
        return self.production_dict[source]

    def generate_first_set(self) -> None:
        for piece in self.used_pieces:
            self.calc_first_set(piece)

    def calc_first_set(self, piece: Piece) -> set[Terminal | None]:
        """
        Calculate the first set of a piece.

        This method currently do NOT support CFG system that may cause Left Recursive.
        """
        try:
            return self.first_sets[piece]
        except KeyError:
            pass

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

        # update catch and return
        self.first_sets[piece] = first_set
        return first_set

    def generate_follow_set(self) -> None:
        """
        Calculate the follow set of a piece.

        Must call generate_first_set() before calling this method.
        """

        for piece in self.used_pieces:
            self.calc_follow_set(piece)

    def calc_follow_set(self, piece: Piece) -> set[Terminal | None]:
        # try using cache
        try:
            return self.follow_sets[piece]
        except KeyError:
            pass

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
                        follow_set.update(self.calc_first_set(prod.target.pieces[i + 1]))

                # update states
                if not (None in cur_piece_first_set):
                    all_contains_epsilon_until_now = False

        # remove epsilon (we don't need it in follow set)
        try:
            follow_set.remove(None)
        except KeyError:
            pass

        # update cache
        self.follow_sets[piece] = follow_set
        return follow_set


def main():
    terminal_int = Terminal(name='int')
    terminal_add = Terminal(name='+')
    terminal_mul = Terminal(name='*')
    terminal_eof = Terminal(name='$')
    terminal_left_para = Terminal(name='(')
    terminal_right_para = Terminal(name=')')
    non_terminal_s = NonTerminal(name='S')
    non_terminal_e = NonTerminal(name='E')
    non_terminal_t = NonTerminal(name='T')

    cfg_sys = CFGSystem(production_list=[
        # S = E EOF
        Production(source=non_terminal_s, target=Derivation(pieces=[non_terminal_e, terminal_eof])),
        # E = T + E
        Production(source=non_terminal_e, target=Derivation(pieces=[non_terminal_t, terminal_add, non_terminal_e])),
        # E = T
        Production(source=non_terminal_e, target=Derivation(pieces=[non_terminal_t])),
        # T = (E)
        Production(source=non_terminal_t,
                   target=Derivation(pieces=[terminal_left_para, non_terminal_e, terminal_right_para])),
        # T = int * T
        Production(source=non_terminal_t, target=Derivation(pieces=[terminal_int, terminal_mul, non_terminal_t])),
        # T = int
        Production(source=non_terminal_t, target=Derivation(pieces=[terminal_int])),
    ])

    print('Used pieces:\n', cfg_sys.used_pieces)
    print('Used Non Terminal:\n', set([i for i in cfg_sys.used_pieces if isinstance(i, NonTerminal)]))

    for k, v in cfg_sys.first_sets.items():
        print(f'First({k}) = {v}')

    for k, v in cfg_sys.follow_sets.items():
        print(f'Follow({k}) = {v}')

    for k, v in cfg_sys.production_dict.items():
        print(f'{k} -> {v}')


if __name__ == '__main__':
    main()

# a -> bc
# c -> xa
# a -> bxa
