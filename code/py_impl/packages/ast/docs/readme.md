AST will become a core module for the frontend compiler processing, since lots of functionalities are rely on the AST strucutrue and the Visitor of the AST.

# Parse Tree To AST

There are lots of difference between Parse Tree and AST.

|          | Parse Tree                                                  | AST                                                                                                 |
| -------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| NodeType | ParseTreeNode. Will bind to a NonTerminal or Terminal type. | Should be an ASTNode. Have its own set of node types.                                               |
| Pointers | Unnamed children. Distinguished by index.                   | Should be named children. Also different types of ASTNode should have different children sturcture. |

The **ASTNode should be able to**:

- Store type info of this ASTNode. (Visitor will decide what functions should be executed upon this node by recognizing the node type)
- Be able to get it's children. (Will be used when visiting the AST)
- Be able to store some attributes. (Some visitor may need to use the attributes of an ASTNode)

When implementing the ASTNode class, we could consider using `dict` in Python to store the info of children node and the attribute of this node.

## Converting Rules

For each non-terminal(or somethings terminal) nodes, we need to provide a rules that defines how this node should be converted into the AST.

There are several info that could be used to generate a new ASTNode.

- Info of current node.
  - Type of the ParseTreeNode
  - Content of the ParseTreeNode (Usually used if this node is Terminal and contains literal info)
- Info of children nodes.

We need the info of the children nodes because the ASTNode may need to points to these nodes.

## Ruleset For Generating AST

The **ruleset should actually be bound to a Production.** This means, for each Production, there should be a corresponding Converting Ruleset. *(This may require modify the parser module to add the corresponding Production info into the ParseTreeNode)*

Ruleset function should concur with certain format as described below:

```python
# A ruleset function should satisfy:
# 
# Receiving two params:
# - A ParseTreeNode represents current node to be processed.
# - A gen_ast_node function used to generate the corresponding ASTNode for children if needed.
# 
# Return:
# - The generated ASTNode instance.
type RulesetFunc = Callable[[ParseTreeNode, Callable], ASTNode]
```

For example, the Production `Expr -> int;Expr` could have belowing ruleset:

```python
def converting_rules_for_prod(node: ParseTreeNode, gen_ast_node: Callable):
    return ASTNode(
        node_type: 'expr',
        content: {
            'expr_list': [gen_ast_node(node.pointers[0])] + gen_ast_node(node.pointers[2])
        }
    )

rule_for_prod: RulesetFunc = converting_rules_for_prod
```

> Previously, I had considered that we could first calculate all ASTNode of the children before calling `gen_ast_node()` of the parent node. However it turns out that this is unnecessary and sometimes could lead to logical error: for example, some redundant ParseTreeNode actually should not be converted to ASTNode.
> 
> So the implementation above **gives the power to the parent node, and let parent node decide what children should be converted into ASTNode**. This is achieved by providing a `Callable` object to the ruleset function which is used to convert ParseTreeNode to ASTNode.

The util func `gen_ast_node` then should be able to generate the ASTNode correctly based on the node info including the corresponding Production info of the node.

```python
def gen_ast_node(node: ParseTreeNode) -> ASTNode:
    # get corresponding ruleset of the receiving node.
    ruleset_func: Callable = get_rule_set_by_production(node.corresponding_production)
    # call the retrieve ruleset function with the node as param.
    return ruleset_func(node, gen_ast_node)
```

-----

We need to gather all ruleset of different production together. **One of the simple way is to use a `dict[Production, RulesetFunc]`**. This also ensure that one Production chould have at most one corresponding converting rules.

```python
ruleset_dict = {
    prod1: ruleset_func1,
    ...
}
```

-----

In this case, when all rules are well defined, we just need to trigger the the `gen_ast_node(root_node)`, in which `root_node` should be the root node of the ParseTree instance.

# Visitor Design

We may need to use a general Visitor class to handle the task of traverse through the AST.

## Rules For Visitors

We may need to perform different operations when traverse through different types of ASTNode. To achieve this, we should allow user providing a RuleSet to the Visitor instance.

Visitor Ruleset should contains the action for all types of node. Then for a single node, the Ruleset should consists of several callbacks like:

- `before_visit_children(current_node)`
- `after_visit_children(current_node)`

The first will be executed before traversing down to the children node, and the second one will be executed after all declared children has been traversed.

