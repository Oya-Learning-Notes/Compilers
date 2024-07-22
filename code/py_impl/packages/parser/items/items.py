from copy import copy
from dataclasses import dataclass
from cfg import Production, Terminal, NonTerminal, Piece

__all__ = [
    'ItemCore',
    'Item',
    'IllegalItemOffsetError',
]


class ItemCore:
    """Class to store info of a item core"""
    production: Production
    offset: int

    def __init__(self, production: Production, offset: int):
        # check if the offset legal
        # offset of epsilon production could only be zero
        if (production.target.pieces is None) and (not offset == 0):
            raise IllegalItemOffsetError(production, offset)
        # offset shall NOT exceed the length of production target pieces
        if ((production.target.pieces is not None) and
                (len(production.target.pieces) < offset)):
            raise IllegalItemOffsetError(production, offset)

        self.production = production
        self.offset = offset

    def __copy__(self):
        return ItemCore(self.production, self.offset)

    def __hash__(self):
        """
        The item with same production and same offset will have same hash.
        """
        return hash(tuple([self.production, self.offset]))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def all_matched(self):
        """
        Return True if this Item represent all the pieces is found in stack.
        """
        return (self.production.target.pieces is None) or (self.offset == len(self.production.target.pieces))

    def move_forward(self) -> 'ItemCore':
        """
        Return a new copy of this ItemCore instance with offset add by 1.

        You may not directly use the new ItemCore produced by this method. Use ItemsHelper instead.
        """
        new_item_core = copy(self)
        new_item_core.offset = new_item_core.offset + 1
        return new_item_core

    def rest_pieces(self) -> list[Piece] | None:
        """
        Return the pieces that not been matched for this Item

        Return None if all match
        """
        if self.all_matched():
            return None

        return self.production.target.pieces[self.offset:]

    def get_waiting(self) -> Piece:
        return self.rest_pieces()[0]


class Item:
    """Class that represents Canonical LR(1) Items"""
    core: ItemCore
    lookahead_set: set[Piece] | None = None

    def __init__(
            self,
            production: Production,
            offset: int,
            lookahead: set[Piece] | None = None):
        """
        Initialize Item based on production offset and lookahead.

        Lookahead default to None.
        """
        self.core = ItemCore(production, offset)
        self.lookahead_set = lookahead

    def __copy__(self):
        return Item(self.core.production, self.core.offset, self.lookahead_set)

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __hash__(self) -> int:
        return hash(tuple([self.core, tuple(self.lookahead_set or set())]))

    def hash_of_core(self):
        """
        Return hash value of core of this Item.
        """
        return hash(self.core)

    def could_reduce(self, piece: Piece):
        if self.lookahead_set is None:
            return True

        if piece in self.lookahead_set:
            return True

        return False


class IllegalItemOffsetError(Exception):
    production: Production
    offset: int

    def __init__(self, prod: Production, offset: int):
        self.production = prod
        self.offset = offset

        super().__init__(
            f'Production with target pieces {prod.target.pieces} has length {len(prod.target.pieces)}, '
            f'and could not have an Item with offset {offset}. '
            f'(offset of an Item must less then or equal to the pieces count)'
        )
