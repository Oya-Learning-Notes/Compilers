from copy import copy
from dataclasses import dataclass
from graphviz import Digraph

from cfg import *
from ..items import *
from .. import errors as general_err
from automata import FA, FANode
from automata.visualize import FADiGraph

__all__ = [
    'StackAutomaton',
    'EntryPatternNotMatch',
    'ParserStackItem',
]


@dataclass
class ParserStackItem:
    piece: Piece
    fa_state: set[FANode[list[Item], Piece]]

    def get_valid_items(self) -> list[Item]:
        """
        Get valid items indicated by this set of states.

        Return empty list if valid items not found.
        """
        valid_items: list[Item] = []

        # states empty, no valid item
        if (self.fa_state is None) or (len(self.fa_state) == 0):
            return valid_items

        # loop state
        for st in self.fa_state:
            item_list = st.label
            valid_items.extend(item_list)

        return valid_items


class StackAutomaton:
    cfg_sys: CFGSystem
    _entry_item: Item

    # items helper for this automaton
    _items_helper: ItemHelper

    _fa: FA[list[Item], Piece]

    def __init__(self, cfg_sys: CFGSystem):
        self.cfg_sys = cfg_sys

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

        # generate the node dicts that used for initializing FA
        fa_node_dicts: dict[str, FANode] = {}
        for node in self._items_helper.fa_nodes.values():
            fa_node_dicts[node.nid] = node

        nfa = FA(fa_node_dicts)
        dfa = nfa.to_dfa(new_fa=True, minimize=False)
        dfa.minimize(new_fa=False, skip_if_pointers_empty=True)

        self._fa = dfa
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

    def to_graphviz(self) -> Digraph:
        gv_instance = FADiGraph(get_node_label=self.get_dfa_node_label)
        return gv_instance.from_fa(self._fa).get_graph()

    def match_stack(self, stack: list[Piece], start_states: set[FANode] | None = None) -> list[ParserStackItem] | None:
        """
        Try matching a list of Pieces using this Stack Automaton.

        Params:

        - ``stack`` A list of Pieces. Could be the whole or part of the Stack.
        - ``start_states`` Specified what states the FA should start from when try matching this list of Pieces. Use
        initial state if not specified.

        Rets:

        - ``list[Item]`` If valid for current stack if match success, return list of all valid Items in such state.
        - ``None`` If could not match the stack with viable prefixes.
        """
        # determine and set start state for Stack Automaton.
        if start_states is None:
            self._fa.init_state()
        else:
            self._fa.set_current_state(start_states)

        # store the generated ParserStackItem
        stack_items: list[ParserStackItem] = []

        # iterate through the stack items and try moving the FA.
        for stack_elem in stack:
            valid_move = self._fa.move_next(stack_elem)
            # if matched failed, return None
            if not valid_move:
                return None
            # match success, create new StackItem
            new_stack_item = ParserStackItem(piece=stack_elem, fa_state=self._fa.get_current_state())
            # add new stack item to return list.
            stack_items.append(new_stack_item)

        return stack_items

    @staticmethod
    def get_dfa_node_label(nid: str, node: FANode[list[Item], Piece]) -> str:
        """
        This static method is used when determine how to determine the label when generating DOT graph.

        This method should not be directly called by user, but could be overridden if needed.
        """
        node_label_str = ''
        # deduplicated_label = list(set(node.label))
        deduplicated_label = node.label
        for item in deduplicated_label:
            node_label_str += str(item)
            node_label_str += '\n'

        return node_label_str
        # return str(node.label)


class EntryPatternNotMatch(Exception):
    def __init__(self, entry: Piece, production: Production | None = None):
        super().__init__(
            f'Error occurred when generating Stack Automaton for CLR(1) Parser. '
            f'Provided entry {entry} found as the source of Production {production}, '
            f'However this production do NOT in accordance to the rules of CLR(1) '
            'augmented CFG pattern. Entry production should have the schema S\' -> S$. '
        )
