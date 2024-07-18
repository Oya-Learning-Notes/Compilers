import automata as fa


class RegularExpr:
    def to_fa(self) -> fa.FA:
        pass


class CharExpr(RegularExpr):
    _char: str

    def __init__(self, char: str) -> None:
        if len(char) != 1:
            raise ValueError("Char must be a single character")
        super().__init__()
        self._char = char

    def to_fa(self) -> fa.FA:
        start_node = fa.FANode(is_start=True)
        end_node = fa.FANode(is_end=True)
        start_node.point_to(self._char, end_node.nid)
        return fa.FA([start_node, end_node])


class AddExpr(RegularExpr):
    """
    Implement `+` in RegExp.

    AddExpr(A, B) -> A+B
    """
    _left: RegularExpr
    _right: RegularExpr

    def __init__(self, left: RegularExpr, right: RegularExpr) -> None:
        super().__init__()
        self._left = left
        self._right = right

    def to_fa(self) -> fa.FA:
        start_node = fa.FANode(is_start=True, label='And_S')
        end_node = fa.FANode(is_end=True, label='And_E')

        # convert two sub regex to fa
        left_fa = self._left.to_fa()
        right_fa = self._right.to_fa()

        # add epsilon moves to this two sub regex
        for node in left_fa.get_start_states():
            node.is_start = False
            start_node.point_to(None, node.nid)

        for node in right_fa.get_start_states():
            node.is_start = False
            start_node.point_to(None, node.nid)

        # point the sub finished state to end node
        for node in left_fa.get_end_states():
            node.is_end = False
            node.point_to(None, end_node.nid)

        for node in right_fa.get_end_states():
            node.is_end = False
            node.point_to(None, end_node.nid)

        node_dict = {}
        node_dict[start_node.nid] = start_node
        node_dict[end_node.nid] = end_node
        node_dict.update(left_fa.nodes)
        node_dict.update(right_fa.nodes)

        return fa.FA(node_dict)


class MulExpr(RegularExpr):
    """
    Implement AB in Regex

    MulExpr(A, B) -> A*B
    """

    _left: RegularExpr
    _right: RegularExpr

    def __init__(self, left: RegularExpr, right: RegularExpr) -> None:
        super().__init__()
        self._left = left
        self._right = right

    def to_fa(self) -> fa.FA:
        start_node = fa.FANode(is_start=True, label='Mul_S')
        end_node = fa.FANode(is_end=True, label='Mul_E')
        mid_start_node = fa.FANode(label='Mul_M')

        left_fa = self._left.to_fa()
        right_fa = self._right.to_fa()

        # start node point to left_fa start
        for node in left_fa.get_start_states():
            node.is_start = False
            start_node.point_to(None, node.nid)

        # left end point to mid
        for node in left_fa.get_end_states():
            node.is_end = False
            node.point_to(None, mid_start_node.nid)

        # mid point to right start
        for node in right_fa.get_start_states():
            node.is_start = False
            mid_start_node.point_to(None, node.nid)

        # right point to end
        for node in right_fa.get_end_states():
            node.is_end = False
            node.point_to(None, end_node.nid)

        node_dict = {}
        node_dict[start_node.nid] = start_node
        node_dict[mid_start_node.nid] = mid_start_node
        node_dict[end_node.nid] = end_node

        node_dict.update(left_fa.nodes)
        node_dict.update(right_fa.nodes)

        return fa.FA(node_dict)


class WildCardExpr(RegularExpr):
    """
    Implement `*` in RegExp.

    WildCardExpr(A) -> A*
    """

    _left: RegularExpr

    def __init__(self, left: RegularExpr) -> None:
        super().__init__()
        self._left = left

    def to_fa(self) -> fa.FA:
        start_node = fa.FANode(is_start=True, label='WC_S')
        matched_node = fa.FANode(label='WC_M')
        end_node = fa.FANode(is_end=True, label='WC_E')

        left_fa = self._left.to_fa()

        # point start to end
        start_node.point_to(None, end_node.nid)

        # point matched to start
        matched_node.point_to(None, start_node.nid)

        # point matched to end
        matched_node.point_to(None, end_node.nid)

        # point start to left start
        for node in left_fa.get_start_states():
            node.is_start = False
            start_node.point_to(None, node.nid)

        # point left end to match
        for node in left_fa.get_end_states():
            node.is_end = False
            node.point_to(None, matched_node.nid)

        node_dict = {}
        node_dict[start_node.nid] = start_node
        node_dict[matched_node.nid] = matched_node
        node_dict[end_node.nid] = end_node
        node_dict.update(left_fa.nodes)

        return fa.FA(node_dict)
