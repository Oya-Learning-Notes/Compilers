from copy import copy
from cfg import *
from ..items import *
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
    of the augmented grammar. S' -> S$, this item should have the None lookahead.
    """
    pass


class StackAutomaton:
    cfg_sys: CFGSystem
    _entry_item: Item

    # items helper for this automaton
    _items_helper: ItemHelper

    _fa: FA

    def __init__(self):
        self._items_helper = ItemHelper()
        self._generate_entry_item()
        self._fa = self._generate_fa()

    def _generate_entry_item(self):
        entry = self.cfg_sys.entry
        entry_item: Item | None = None

        # error if not specify entry
        if entry is None:
            raise general_err.EntryUndefinedError()

        # find entry production
        for prod in self.cfg_sys.production_list:
            if prod.source != entry:
                continue

            # check if the found production according to the rule
            if prod.target.pieces is None or len(prod.target.pieces) != 2:
                raise EntryPatternNotMatch(entry, prod)

            # create item
            entry_item = self._items_helper.get_item(Item(prod, 0, None), True, True)
            break

        # if no entry found
        if entry_item is None:
            raise EntryPatternNotMatch(entry, None)

        self._entry_item = entry_item

    def _generate_fa(self) -> FA:
        """
        Discover and generate NFA used to match the stacks.
        :return:
        """
        # discover new moves recursively.
        process_list: list[Item] = [self._entry_item]

        while len(process_list) > 0:
            current_item = process_list.pop()

            # if this item is all matched, skip
            if current_item.core.all_matched():
                continue

            # add forward item
            forward_item = self._items_helper.get_forward_item(current_item, write_if_not_exists=False)
            # search forward item too if it's not been tracked
            if not self._items_helper.has_item(forward_item):
                process_list.append(forward_item)
            # add pointer
            self._items_helper.point_to(current_item, current_item.core.get_waiting(), forward_item)

            # found watching piece
            watching_piece = current_item.core.get_waiting()
            # add closure item if waiting item is non-terminal
            if not isinstance(current_item.core.get_waiting(), NonTerminal):
                continue
            watching_piece: NonTerminal
            lookahead_set = self._generate_lookahead(current_item, forward_item)
            # found production that source is the waiting item
            for prod in self.cfg_sys.production_dict[watching_piece]:
                # new item for this production
                new_item = Item(prod, 0, lookahead_set)
                # add to process list if not tracked before
                if not self._items_helper.has_item(new_item):
                    process_list.append(new_item)
                # add pointer with epsilon move
                self._items_helper.point_to(current_item, None, new_item)

        nfa = FA(self._items_helper.fa_nodes)
        dfa = nfa.to_dfa().minimize()

        return dfa

    def _generate_lookahead(self, current_item: Item, forward_item: Item) -> set[Piece] | None:
        """
        Default lookahead generator logic for CLR

        If you want to use SLR, override this method and let it always return None.
        """
        # all item being processed should not be epsilon item. Since epsilon item always satisfy all_matched() == True
        assert current_item.core.production.target.pieces is not None

        max_offset = len(current_item.core.production.target.pieces)
        offset = current_item.core.offset

        assert max_offset > offset

        # no any following piece, use lookahead of current node for all derived node.
        if forward_item.core.all_matched():
            return current_item.lookahead_set

        # has the following pieces, then lookahead should be FIRST(rest_pieces, lookaheads)
        rest_pieces = forward_item.core.rest_pieces()
        first_set_of_rest = self.cfg_sys.calc_first_set_of_pieces(rest_pieces)
        # if epsilon in first set, then add lookahead of current item
        if None in first_set_of_rest:
            first_set_of_rest.remove(None)
            first_set_of_rest.update(current_item.lookahead_set)

        return first_set_of_rest


class EntryPatternNotMatch(Exception):
    def __init__(self, entry: Piece, production: Production | None = None):
        super().__init__(
            f'Error occurred when generating Stack Automaton for CLR(1) Parser. '
            f'Provided entry {entry} found as the source of Production {production}, '
            f'However this production do NOT in accordance to the rules of CLR(1) '
            'augmented CFG pattern. Entry production should have the schema S\' -> S$. '
        )
