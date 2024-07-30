- [Node In Parse Tree](#node-in-parse-tree)
  - [About ParseTreeNode and pointers](#about-parsetreenode-and-pointers)
  - [Epsilon Node](#epsilon-node)
  - [Corresponding Production Info](#corresponding-production-info)
- [Design of ParseTree](#design-of-parsetree)
  - [For Top-down Algorithms](#for-top-down-algorithms)
  - [For Bottom-up Algorithms](#for-bottom-up-algorithms)


# Node In Parse Tree

## About ParseTreeNode and pointers

When designing the usage of `ParseTree` and `ParseTreeNode`, the `ParseTreeNode` object are designed to reused and
linked by reference of Node instance itself.

This is different from the thought when designing Finite Automata, where we use `nid` _(A string or a number that
unique across different nodes)_ . Actually I was regret that I didn't use direct instance ref at that time for `fa`
module.

## Epsilon Node

When initializing a ParseTree, it's required to provide an $\varepsilon$ terminal.

This is because we use `None` to represent $\varepsilon$ in this packages, however when a node is derived into $\varepsilon$, we need to actually link it to a Epsilon node, otherwise this node will be left in the leaves as non-terminal.

Once a $\varepsilon$ terminal has been pass to parse tree, the parse tree will use such terminal to generate **Epsilon Node** everytime it's used.

We could not directly cache the *Epsilon Node*, since different node that has been derived to $\varepsilon$ should actually link to it's own child *Epsilon Node*.

## Corresponding Production Info

For each node, we may store the corresponding Production info that related to this node. Checkout this example:

![image](https://github.com/user-attachments/assets/5a55a6b6-6f45-4676-864a-0fe98a90604f)

The **corresponding Production should represents the relationship of this node and its children nodes**.

-----

**Usage Of Corresponding Production**

The Corresponding Production info is **useful when we trying to use a Rule-Based system to convert Parse Tree to Abstract Syntax Tree**. We could specify the rules for every single Production that how to convert ParseTreeNode to ASTNode which has this kinds of Production.

# Design of ParseTree

The ParseTree class should be designed to serve several different Parsing Algorithm for example `LL(1)`, `SLR`,
`CLR` etc.

There is two basic types of those Algorithm: Top-down and Bottom-up.

To support these two types of algorithm simultaneously, we define two fields in this class:

- `entries`
- `leaves`

They are both a `list[ParseTreeNode]` object. `entries` stores the current top nodes, and `leaves` tracks the leaves
nodes.

## For Top-down Algorithms

When using ParseTable in Top-down algorithms, we generally first initialize the `entries` to be the Entry NonTerminal,
For example the `S` node, so does `leaves` _(because at this time the leaves of the tree is also the Entry
NonTerminal)._

Then when Parser going on and want to do Derivation on some leave nodes. (Usually is the left-most NonTerminal in
`leaves`), we directly update the pointer of the nodes that we want to derive, let it point to the new derived nodes.
Then remove this node from `leaves`, add new nodes to `leaves` to replace this node.

For example we want to do `1 -> 2, 3`, then we found `1` in `leaves`, point `1` to `2, 3`, then replace `1` in
`leaves` with `2, 3`.

When all things finished and parse success, the `leaves` nodes should all be `Terminal` and should match the
sequence of input list of `TokenPairs`.

## For Bottom-up Algorithms

At the beginning, initialize both `entries` and `leaves` to list of `Terminal` matched the input list of `TokenPairs`

When doing Reduction on some nodes, we first found these nodes in `entries`, create a new node that point to these
node, then replace these nodes in `entries` with the newly created nodes.

For example, if we want reduction like `node1 <- node2, node3, node4`, We first create new node `node1`, point it to
the three
nodes, then replace `node2, node3, node4` in `entries` with `node1`.

When finished, `entries` should become a list of single Node that matches the Entry NonTerminal type.

