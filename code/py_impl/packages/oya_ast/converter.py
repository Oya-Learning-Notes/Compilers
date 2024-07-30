from typing import Callable

from cfg import Terminal, NonTerminal, Piece, Production
from parser import ParseTree, ParseTreeNode

type GenAstNodeFuncType = Callable[[ParseTreeNode], ASTNode]
type RulesetFuncType = Callable[[ParseTreeNode, GenAstNodeFuncType], ASTNode]
type ASTNodeTypeReprType = str

__all__ = [
    'ASTNode',
    'ASTConverterRuleset',
]


class ASTNode:
    # a string represent the type of this oya_ast node. E.g.: "if_else", "string"
    node_type: ASTNodeTypeReprType
    # dict to store content of this node. Usually used when this node is a leaf.
    content: dict[str, object]
    # grammar attributes stored in this node.
    attributes: dict[str, object]
    # pointers to children of this node.
    pointers: dict[str, 'ASTNode']

    def __init__(self, node_type: ASTNodeTypeReprType):
        self.node_type = node_type
        self.content = {}
        self.attributes = {}
        self.pointers = {}


class ASTConverterRuleset:
    _ruleset_dict: dict[Production, RulesetFuncType]

    def __init__(self):
        self._ruleset_dict = {}

    def add_rules(self, rule_dict: dict[Production, RulesetFuncType]):
        self._ruleset_dict.update(rule_dict)

    def find_rule(self, node: ParseTreeNode):
        # todo
        # Update parser module, add corresponding production info into ParseTreeNode.
        related_production: Production = node.production
        try:
            rule_for_this_node = self._ruleset_dict[related_production]
        except KeyError:
            raise RuleUndefinedError(prod=related_production, node=node)


class RuleUndefinedError(Exception):
    """
    Raise when trying to get the corresponding rule for a Production that has no defined rule.
    """

    def __init__(self, prod: Production, node: ParseTreeNode | None = None):
        # production info
        err_msg = f'Could not find rule for Production {prod}. '
        # add relevant node info
        if node is not None:
            err_msg += f'The node {node} is corresponding to this Production.'

        super().__init__(err_msg)
