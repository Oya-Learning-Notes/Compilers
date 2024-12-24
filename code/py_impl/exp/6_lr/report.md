# LR(0) Parse 实验

## 实验目的

## 实验结果

本次实验，我们采用了书上的例子，对字符串 `bccd#` 进行 LR(0) 分析。分析结果的文本输出如下，其中：

- 由于本次实验是最后一次实验，故本次实验综合了以往各个实验的实验成果，尽量包含整个课程的多个环节，包括：
  - 正规式转 DFA
  - 词法分析
  - 文法表示
  - LR 分析器

下方的输出中，也包含了对于给定字符串 `bccd#` 的完整 LR(0)分析过程。

```
Tokens:
TokenPair(token_type='b', content='b')
TokenPair(token_type='c', content='c')
TokenPair(token_type='c', content='c')
TokenPair(token_type='d', content='d')
TokenPair(token_type='$', content='$')

Used pieces:
{$, S, B, E, A, a, S', b, d, c}
------------
Used Non Terminal:
{S, B, E, A, S'}
First Set:
First($) = {$}
First(S) = {a, b}
First(E) = {a, b}
First(B) = {d, c}
First(d) = {d}
Follow Set
Follow(S') = {None}
Follow($) = {None}
Follow(S) = {$}
Follow(E) = {$}
Follow(A) = {$}
Follow(a) = {d, c}
Follow(B) = {$}
Follow(b) = {d, c}
Follow(c) = {d, c}
Follow(d) = {$}
----------
Production Dict
S' -> {S' -> S$}
S -> {S -> E}
E -> {E -> aA, E -> bB}
A -> {A -> d, A -> cA}
B -> {B -> cB, B -> d}
---------------

2024-12-24 19:50:09.815 | DEBUG    | parser.lr.parser_lr:parse:95 - Stack: []
2024-12-24 19:50:09.816 | DEBUG    | parser.lr.parser_lr:parse:105 - Shift b into stack
2024-12-24 19:50:09.817 | DEBUG    | parser.lr.parser_lr:parse:95 - Stack: [b]
2024-12-24 19:50:09.818 | DEBUG    | parser.lr.parser_lr:parse:105 - Shift c into stack
2024-12-24 19:50:09.819 | DEBUG    | parser.lr.parser_lr:parse:95 - Stack: [b, c]
2024-12-24 19:50:09.820 | DEBUG    | parser.lr.parser_lr:parse:105 - Shift c into stack
2024-12-24 19:50:09.820 | DEBUG    | parser.lr.parser_lr:parse:95 - Stack: [b, c, c]
2024-12-24 19:50:09.821 | DEBUG    | parser.lr.parser_lr:parse:105 - Shift d into stack
2024-12-24 19:50:09.822 | DEBUG    | parser.lr.parser_lr:parse:95 - Stack: [b, c, c, d]
2024-12-24 19:50:09.823 | DEBUG    | parser.lr.parser_lr:parse:101 - Reduction using prod: B -> d
2024-12-24 19:50:09.824 | DEBUG    | parser.lr.parser_lr:parse:95 - Stack: [b, c, c, B]
2024-12-24 19:50:09.825 | DEBUG    | parser.lr.parser_lr:parse:101 - Reduction using prod: B -> cB
2024-12-24 19:50:09.826 | DEBUG    | parser.lr.parser_lr:parse:95 - Stack: [b, c, B]
2024-12-24 19:50:09.826 | DEBUG    | parser.lr.parser_lr:parse:101 - Reduction using prod: B -> cB
2024-12-24 19:50:09.827 | DEBUG    | parser.lr.parser_lr:parse:95 - Stack: [b, B]
2024-12-24 19:50:09.828 | DEBUG    | parser.lr.parser_lr:parse:101 - Reduction using prod: E -> bB
2024-12-24 19:50:09.829 | DEBUG    | parser.lr.parser_lr:parse:95 - Stack: [E]
2024-12-24 19:50:09.830 | DEBUG    | parser.lr.parser_lr:parse:101 - Reduction using prod: S -> E
2024-12-24 19:50:09.831 | DEBUG    | parser.lr.parser_lr:parse:95 - Stack: [S]
2024-12-24 19:50:09.832 | DEBUG    | parser.lr.parser_lr:parse:105 - Shift $ into stack
2024-12-24 19:50:09.833 | DEBUG    | parser.lr.parser_lr:parse:95 - Stack: [S, $]
2024-12-24 19:50:09.834 | DEBUG    | parser.lr.parser_lr:parse:101 - Reduction using prod: S' -> S$
```

分析完成后，其构造的语法树结果如下图所示:

![Parse Tree](./assets/parse_tree.png)

## 实验代码

本次实验实际上是我编写的整个实验项目的一部分，在条件允许的情况下，推荐通过 GitHub 仓库查看全部代码。



### 入口以及数据定义代码

`./lr_test.py`

```python
import parser
from cfg import *
import reg_exp as reg
import lexical_analyzer as la
from pprint import pprint


def main():
    program_str = "bccd$"

    # Lexical Analyzer Part

    reg_b = reg.CharExpr("b")
    reg_c = reg.CharExpr("c")
    reg_d = reg.CharExpr("d")
    reg_eof = reg.CharExpr("$")

    lexical_analyzer = la.LexicalAnalyzer(
        token_definitions=[
            la.TokenDefinition("b", reg_b),
            la.TokenDefinition("c", reg_c),
            la.TokenDefinition("d", reg_d),
            la.TokenDefinition("$", reg_eof),
        ],
        use_dfa=True,
    )

    program_token_list = lexical_analyzer.parse(program_str)
    program_token_list = [t for t in program_token_list if t.token_type != "white"]

    print("Tokens:")
    for i in program_token_list:
        print(i)

    # CFG Part
    terminal_a = Terminal(name="a")
    terminal_b = Terminal(name="b")
    terminal_c = Terminal(name="c")
    terminal_d = Terminal(name="d")
    terminal_eof = Terminal(name="$")

    S_pi = NonTerminal("S'")
    S = NonTerminal(name="S")
    E = NonTerminal(name="E")
    A = NonTerminal(name="A")
    B = NonTerminal(name="B")

    cfg_sys = CFGSystem(
        entry=S_pi,
        production_list=[
            Production(source=S_pi, target=Derivation([S, terminal_eof])),
            Production(source=S, target=Derivation([E])),
            Production(source=E, target=Derivation([terminal_a, A])),
            Production(source=E, target=Derivation([terminal_b, B])),
            Production(source=A, target=Derivation([terminal_c, A])),
            Production(source=A, target=Derivation([terminal_d])),
            Production(source=B, target=Derivation([terminal_d])),
            Production(source=B, target=Derivation([terminal_c, B])),
        ],
    )

    print("Used pieces:")
    pprint(cfg_sys.used_pieces)
    print("------------")

    print("Used Non Terminal:")
    pprint(set([i for i in cfg_sys.used_pieces if isinstance(i, NonTerminal)]))

    print("First Set:")
    for k, v in cfg_sys.first_sets.items():
        print(f"First({k}) = {v}")
    print("----------")

    print("Follow Set")
    for k, v in cfg_sys.follow_sets.items():
        print(f"Follow({k}) = {v}")
    print("----------")

    print("Production Dict")
    for k, v in cfg_sys.production_dict.items():
        print(f"{k} -> {v}")
    print("---------------")

    # create parser
    lr_parser = parser.lr.LRParserBase(
        cfg_sys=cfg_sys, epsilon_terminal=Terminal(name="[e]")
    )

    # show graph of that automaton
    gv_ins = lr_parser.stack_automaton.to_graphviz()
    gv_ins.render(directory="./output", view=True)

    parse_tree = lr_parser.parse(program_token_list)

    if parse_tree is not None:
        parse_tree.to_graphviz().render(directory="./output", view=True)


if __name__ == "__main__":
    main()
```

### 分析器核心代码

```python
from copy import copy
from dataclasses import dataclass
from loguru import logger

from cfg import *
from automata import FA, FANode
from automata.visualize import FADiGraph
from lexical_analyzer import TokenPair

from ..items import *
from ..parse_tree import *
from .stack_automata import *
from .. import errors as general_err

__all__ = ["LRParserBase"]


class LRParserBase:
    """
    Base class for all LR parsers.

    Rewrites:

    To create new LR Parser, we need to re-write the following methods:

    - ``_generate_automaton()`` Rewrite to generate the proper Stack Automaton for the LR Parser.
    - ``_get_lookahead()`` Rewrite if you want to decide how to convert a token to its corresponding lookahead instance.
    - ``_is_lookahead_match()`` Determine how to judge whether current lookahead match the requirement of the Item.

    Fields:
    - ``_parser_type`` The string that represents the type of the parser. E.g.: SLR, CLR, ...
    """

    cfg_sys: CFGSystem

    _parser_type: str = "Base LR"

    _token_list: list[TokenPair]

    # working stack of this parser
    _stack: list[ParserStackItem]

    # list of unexamined token of the parser
    _unexamined: list[TokenPair]

    # parse tree object for the parser.
    _parse_tree: ParseTree

    # a terminal that used to represent the epsilon derivation in parse tree.
    _epsilon_terminal: Terminal | None

    # store the stack automaton for this parser
    stack_automaton: StackAutomaton

    def __init__(
        self,
        cfg_sys: CFGSystem,
        epsilon_terminal: Terminal | None = None,
    ):
        self.cfg_sys = cfg_sys
        self._epsilon_terminal = epsilon_terminal
        self._generate_automaton()

    def init_state(self, token_list: list[TokenPair]) -> "LRParserBase":
        """
        Prepare the parser, make it ready to parse the input list of token.
        """
        # shadow copy the received token list.
        self._token_list = token_list[:]
        self._unexamined = token_list[:]
        # initialize the stack
        self._stack = []

        # initialize parse tree
        parse_tree_nodes: list[ParseTreeNode] = []
        # convert all tokens in token_list into ParseTreeNode.
        for token in self._token_list:
            parse_tree_nodes.append(
                ParseTreeNode(node_type=token.to_terminal(), node_content=token)
            )
        # init parse tree.
        self._parse_tree = ParseTree(
            parse_tree_nodes,
            epsilon_terminal=self._epsilon_terminal,
        )

        return self

    def parse(self, token_list: list[TokenPair]) -> ParseTree | None:
        # initial parser state
        self.init_state(token_list)

        # parse until parse tree valid or all token used
        while not self._parse_tree.is_valid_for_bottom_up():
            logger.debug(f"Stack: {self._stack}")

            # check if we should perform reduction
            reduce_prod = self._should_reduce()
            # perform reduction if should
            if reduce_prod is not None:
                logger.debug(f"Reduction using prod: {reduce_prod}")
                self.perform_reduction(reduce_prod)
            # else, perform shift
            else:
                logger.debug(f"Shift {self._get_lookahead()} into stack")
                self.perform_shift()

        # error detection part
        if len(self._unexamined) > 0:
            general_err.ParseErrorBase(
                f"Parse Tree has been fully reduced with unexamined tokens {token_list}"
            )

        if self._parse_tree.is_valid():
            general_err.ParseErrorBase(
                "Could not successfully reduced into a valid parse tree with all tokens already used"
            )

        # all good, return parse tree
        return self._parse_tree

    def _get_lookahead(self) -> Terminal | None:
        """
        Return the lookahead terminal type of current state.

        Return None if no lookahead found.
        """
        if len(self._unexamined) == 0:
            return None

        return Terminal(name=self._unexamined[0].token_type)

    def _is_lookahead_match(self, item: Item) -> bool:
        """
        Check if input item could match current lookahead of this parser.
        """
        # In convention of this package, lookahead set is None represents that no limitation on lookahead.
        # So here always return True.
        if item.lookahead_set is None or (None in item.lookahead_set):
            return True

        # get current lookahead
        lookahead_terminal = self._get_lookahead()
        # return compare result
        return lookahead_terminal in item.lookahead_set

    def _should_reduce(self) -> Production | None:
        """
        Check if the parser should perform reduction at current state of affairs.

        Rets:

        - ``Production`` Returns Production which should be used for Reduction if should reduce.
        - ``None`` If should NOT reduce at this time.
        """
        # if stack is empty, impossible to reduce
        if len(self._stack) == 0:
            return None

        # get current valid items
        valid_items = self._stack[-1].get_valid_items()

        # no valid items
        if len(valid_items) == 0:
            return None

        # check all items in current states, if they matched the current lookahead?
        matched_items: set[Item] = set()
        for item in valid_items:

            # only all matched items could be used for reduction action.
            if not (item.core.all_matched()):
                continue

            # if lookahead matched, add to matched_item list.
            if self._is_lookahead_match(item):
                matched_items.add(item)

        matched_count = len(matched_items)

        # if no item match, should not reduce
        if matched_count == 0:
            return None

        # there should be at most one matched item
        if matched_count > 1:
            raise ReduceReduceConflict(
                conflict_item=matched_items, parser_type=self._parser_type
            )

        # retrieve the only matched item
        single_match_item: Item = None
        for i in matched_items:
            single_match_item = i

        assert single_match_item is not None
        return single_match_item.core.production

    def perform_reduction(self, production: Production) -> None:
        """
        Perform Reduction operation on the Stack with the instruction of given Production.
        """

        # retrieve info
        source = production.source
        target_pieces = production.target.pieces

        # determine reduce size.
        # Here reduce size means the count of the stack element that is going to be reduced.
        reduce_size: int = -1
        if target_pieces is None:
            reduce_size = 0
        else:
            reduce_size = len(target_pieces)

        # check if current Reduction could actually be performed.
        # that is: check if the top part of the stack matches the target pieces of this production.
        stack_top = self._stack[-reduce_size:]
        stack_top_pieces = [i.piece for i in stack_top]
        # raise error if pieces not match
        # if target pieces is None, means target is epsilon, no need to check
        if (target_pieces is not None) and (not (stack_top_pieces == target_pieces)):
            raise InvalidReductionError(
                production_target=target_pieces, stack_top=stack_top_pieces
            )

        # reduction could be successfully performed.

        # remove previous pieces
        if reduce_size > 0:
            self._stack = self._stack[:-reduce_size]

        # update parse tree
        self._parse_tree.reduce_node(
            start_index=len(self._stack), reduce_size=reduce_size, new_piece=source
        )

        # generate item for new pieces
        # if the stack is not empty after removing target pieces, means we could start matching at the state of top of
        # the stack.
        start_states: set[FANode] | None = None
        if len(self._stack) > 0:
            start_states = self._stack[-1].fa_state
        new_stack_item_list = self.stack_automaton.match_stack(
            stack=[source], start_states=start_states
        )

        # special judge when source if entry. (since stack automaton could not match the true entry)
        if source == self.cfg_sys.entry:
            self._stack.append(ParserStackItem(piece=source, fa_state=set()))
            return

        # raise error if the stack could not be matched using the Stack Automaton after reduction.
        if new_stack_item_list is None:
            raise ReductionStateError()

        # add new item list to stack
        # here new stack item list should always have only one element. This is because the source part of a Production
        # should always be a single NonTerminal.
        assert len(new_stack_item_list) == 1
        self._stack.append(new_stack_item_list[0])

    def perform_shift(self):
        # raise error if it could not shift
        if len(self._unexamined) == 0:
            raise RuntimeError(
                "Could not perform Shift operation for this parser, since no more tokens in unexamined list."
            )

        # get first token in unexamined
        token_terminal_to_be_shift = self._unexamined.pop(0).to_terminal()

        # go through the fa
        start_state: set[FANode] | None = None
        if len(self._stack) > 0:
            start_state = self._stack[-1].fa_state
        parser_item_list = self.stack_automaton.match_stack(
            stack=[token_terminal_to_be_shift], start_states=start_state
        )

        # raise error if shift breaks viable prefixes
        if parser_item_list is None:
            raise ShiftStateError()

        assert len(parser_item_list) == 1
        new_parser_item = parser_item_list[0]

        # add new item to stack
        self._stack.append(new_parser_item)

    def _generate_automaton(self):
        """
        Generate Stack Automaton for this parser.

        Notice:

        Make sure self.cfg_sys has been input successfully.

        Override:

        Should be overridden by subclasses to generate proper Stack Automaton for different LR Parser.
        """
        self.stack_automaton = StackAutomaton(self.cfg_sys)


class CLRParser(LRParserBase):
    """
    ## About Entry of CLR Parser:

    The entry of CLRParser should be in pattern of S' -> S $

    Specifically, the pattern should have a Derivation with two pieces, The first is the true entry, the second is the
    terminal that represent the end of parsing.

    Also in CLR(1) Items, lookahead is None represent reduce with no limitation. This will only be used in the entry
    of the augmented grammar. S' -> S$, this item should have the None as the lookahead.
    """

    pass


class ReduceReduceConflict(Exception):
    """
    Raise when more than one reduce operation could be performed at the same time.
    """

    def __init__(self, conflict_item: set[Item], parser_type: str | None = None):
        """
        Params:

        - conflict_item A set of the conflict item.
        - parser_type String represents the type of the parser. E.g.: CLR, LR(1), ...
        """
        parser_type_str = ""
        if parser_type is not None:
            parser_type_str += f" with type {parser_type}"

        error_msg = f"Reduce-Reduce error occurred in parser{parser_type_str}. Set of conflict items: {conflict_item}"


class InvalidReductionError(general_err.ParseErrorBase):
    """
    Raise when LR Parser is intend to perform a Reduction with instruction of a Production. However the target pieces
    of this production doesn't match the stack top of the parser state.
    """

    def __init__(self, production_target: list[Piece], stack_top: list[Piece]):
        super().__init__(
            f"A Reduction by Production with target pieces {production_target} could not been performed, "
            f"since the top part of parser Stack {stack_top} does not match such pieces."
        )


class ReductionStateError(general_err.ParseErrorBase):
    """
    Raise when a reduction is performed, but the new stack is not a viable perfixes.
    """

    def __init__(self):
        super().__init__(
            "A Production has been successfully performed, but the new Stack is not a viable prefix after reducing."
        )


class ShiftStateError(general_err.ParseErrorBase):
    """
    Raise when Stack is not viable prefixes anymore after a shift operation.
    """

    def __init__(self):
        super().__init__(
            "Stack is not viable prefixes anymore after a Shift operation."
        )

```
