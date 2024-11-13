import automata as fa
from typing import Iterable


class RegularExpr:
    """
    Base class for Regular Expressions.
    """

    # To write a sub-class, the main task is to rewrite __init__() and to_fa() method.
    #
    # - __init__() should take enough info for generating this Expression.
    # - to_fa() returns a fa.FA() instance, representing the Automata of this RegExp.
    #
    # Notice:
    # - It's recommend to only have one single Start and End node in the Automata generated.

    def to_fa(self) -> fa.FA:
        raise NotImplementedError()


class CharExpr(RegularExpr):
    _char: str

    def __init__(self, char: str) -> None:
        if len(char) != 1:
            raise ValueError("Char must be a single character")
        super().__init__()
        self._char = char

    def to_fa(self) -> fa.FA:
        start_node: fa.FANode = fa.FANode(is_start=True)
        end_node: fa.FANode = fa.FANode(is_end=True)
        start_node.point_to(self._char, end_node.nid)
        return fa.FA([start_node, end_node])


class AddListExpr(RegularExpr):
    def __init__(self, expr_list: list[RegularExpr]):
        self.expr_list = expr_list

    def to_fa(self):
        if len(self.expr_list) < 2:
            return self.expr_list[0].to_fa()

        new_expr = AddExpr(self.expr_list[0], self.expr_list[1])

        for idx in range(2, len(self.expr_list)):
            new_expr = AddExpr(new_expr, self.expr_list[idx])

        return new_expr.to_fa()


class AddExpr(RegularExpr):
    """
    Implement `+` in RegExp.

    AddExpr(A, B) -> A|B
    """

    _left: RegularExpr
    _right: RegularExpr

    def __init__(self, left: RegularExpr, right: RegularExpr) -> None:
        super().__init__()
        self._left = left
        self._right = right

    def to_fa(self) -> fa.FA:
        start_node: fa.FANode = fa.FANode(is_start=True, label="And_S")
        end_node: fa.FANode = fa.FANode(is_end=True, label="And_E")

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


class MulListExpr(RegularExpr):
    """
    Implement a chian multiple operation.

    [A,B,C] -> ABC
    """

    def __init__(self, expr_list: list[RegularExpr]):
        self.expr_list = expr_list
        self._new_expr: RegularExpr
        self._construct_new_expr()

    def to_fa(self):
        return self._new_expr.to_fa()

    def _construct_new_expr(self):
        if len(self.expr_list) < 2:
            return self.expr_list[0]

        new_expr = MulExpr(self.expr_list[0], self.expr_list[1])

        for idx in range(2, len(self.expr_list)):
            new_expr = MulExpr(new_expr, self.expr_list[idx])

        self._new_expr = new_expr


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
        start_node: fa.FANode = fa.FANode(is_start=True, label="Mul_S")
        end_node: fa.FANode = fa.FANode(is_end=True, label="Mul_E")
        mid_start_node: fa.FANode = fa.FANode(label="Mul_M")

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
        start_node: fa.FANode = fa.FANode(is_start=True, label="WC_S")
        matched_node: fa.FANode = fa.FANode(label="WC_M")
        end_node: fa.FANode = fa.FANode(is_end=True, label="WC_E")

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


class CharListExpr(RegularExpr):
    """
    Match a set of chars.

    CharListExpr('abc') -> a|b|c
    """

    def __init__(self, char_list: Iterable[str]):
        self._char_list: Iterable[str] = char_list

    def to_fa(self) -> fa.FA:
        start_node: fa.FANode = fa.FANode(is_start=True)
        end_node: fa.FANode = fa.FANode(is_end=True)
        for char in self._char_list:
            start_node.point_to(char, end_node.nid)

        return fa.FA({start_node.nid: start_node, end_node.nid: end_node})
