from cfg import CFGSystem, Production, Terminal, NonTerminal, Piece
from .items import ItemCore, Item, IllegalItemOffsetError
from automata import FA, FANode

__all__ = [
    'ItemHelper',
    'UntrackItemError',
]


class ItemHelper:
    """
    Helper class that used to manage Items used when generating CFG Stack Automaton.
    """

    # key is hash of items, value is items
    items_dict: dict[int, Item]

    # store the corresponding fa node of the items instance.
    # the key is the hash of the Item that this fa node represents
    fa_nodes: dict[int, FANode[Item, Piece]]

    def __init__(self):
        self.items_dict = {}
        self.fa_nodes = {}

    def has_item(self, item: Item) -> bool:
        """
        Check if an item has been added to this ItemHelper before
        """
        item_hash = hash(item)
        item_ref = self.items_dict.get(item_hash)
        return item_ref is not None

    def get_item(self, item: Item, write_if_not_exists=True, is_entry: bool = False) -> Item:
        """
        Get item from ItemsHelper. If the items have been added into this helper before, return the reference of the
        previous item. Else, return the item reference that passed into the method.

        Params:

        - ``write_if_not_exists`` If true, ItemHelper will add this items to discovered dict.
        - ``is_entry`` Only available if this item has not been added to ItemHelper before. If `True`, will consider the
        corresponding FANode as the start node.
        """
        item_hash = hash(item)
        dict_value = self.items_dict.get(item_hash)

        # if not exists
        if dict_value is None:
            if write_if_not_exists:
                # write item dict
                self.items_dict[item_hash] = item
                # create fa node and write fa node dict
                new_fa_node = FANode(is_start=is_entry, is_end=True, label=item)
                self.fa_nodes[item_hash] = new_fa_node
            return item

        # exists, return previous reference
        return dict_value

    def get_fa_node(self, item: Item) -> FANode[Item, Piece]:
        """
        Get corresponding FANode of an Item.
        """
        item_hash = hash(item)
        try:
            return self.fa_nodes[item_hash]
        except KeyError:
            raise UntrackItemError(item)

    def get_forward_item(self, item: Item, keep_lookahead: bool = True, write_if_not_exists: bool = True) -> Item:
        prod = item.core.production
        offset = item.core.offset
        lookahead = item.lookahead_set

        # deal with lookahead
        if not keep_lookahead:
            lookahead = None

        # if offset out of range, raise error
        if item.core.all_matched():
            raise IllegalItemOffsetError(prod, offset + 1)

        # generate new item
        new_item = Item(prod, offset, lookahead)

        # get reference of this item
        return self.get_item(new_item, write_if_not_exists)

    def point_to(self, source_item: Item, next_input: Piece | None, target_item: Item) -> bool:
        """
        Add moves with schema source_item ->^(next_input) target_item

        Rets: Return `True` if the target_item is being tracked by this ItemsHelper before. This will be helpful
        when generating FA for Bottom-up parsing. Only nodes that not been tracked should be processed recursively.

        Notice:

        - Will create Item if not been tracked by ItemHelper before.
        """
        target_has_been_tracked = self.has_item(target_item)

        # get item reference, create if not exists
        source_item = self.get_item(source_item)
        target_item = self.get_item(target_item)

        # get corresponding fa node
        source_node = self.get_fa_node(source_item)
        target_node = self.get_fa_node(target_item)

        # pointing items
        source_node.point_to(next_input, target_node.nid)

        return target_has_been_tracked


class UntrackItemError(Exception):

    def __init__(self, item: Item):
        super().__init__(
            f'Try to get reference of an Item that not been tracked by ItemHelper. Item {item} not tracked by '
            'this ItemHelper'
        )
