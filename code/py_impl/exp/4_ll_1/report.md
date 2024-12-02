# LL(1) 文法判别实验报告

本次实验主要完成的工作有:

- First Set, Follow Set, Select Set 的生成。
- LL(1)文法的判断
- 消除左递归
- 提取左公因子

在实现着四个主要功能的代码实现部分，我个人特别着重分配时间的部分是 **提取左公因子** 的部分。其余部分的代码实现，基本上可以认为是对于教材中提到的算法进行实现。

## 提取左公因子

进一步来说，对于左公因子的提取的算法思想和实现，我**单独编写了一份文档**。参见附件：“提取左公因子”。

## LL(1) 文法的判断

总体的思想上来说，我们只需要考虑对于每一组拥有同样左部的产生式来说，其是否存在冲突。

假设我们已经计算出某一组产生式的 Select Set 的情况下，一种快速的确认其是否存在重复元素的方式如下：

- 对于每一个产生式，计算其 Select Set 中的元素，然后计算这一组产生式每个 Select Set 的元素个数的总和。
- 将这一组所有产生式的 Select Set 执行并集操作。计算其元素个数。

如果后者小于前者，那么我们便可以认定，这些集合中存在重复的元素。

> 注：这种做法消耗的计算资源相对一一比较来说更少，但于此同时，并不能具体的给出是那两个 Select Set 发生了冲突。对于需要知道冲突具体情况的场景，可以采用一一比较的方法。

## First Set 和 Follow Set 的计算

总体上，这两者的计算均采用教材中提供的迭代法进行求解，故对于算法的理论方面，此处不过多赘述。
具体实现在上下文无关文法的基类 `CFGSystem` 中给出：

> 下方提供的两个函数，都提供了较好的步骤封装和抽象，同时提供了必要的注释和文档。
> 您可以借助代码中的注释来帮助理解这两个方法的工作原理。

需要注意的是，通过 Python 对书本中的 First Set 和 Follow Set 算法进行实现时，需要注意为各个数据类提供合适的 `__hash__()` 和 `__eq__()` 方法，以确保我们自己定义的数据类可以配合诸如 `set`, `frozenset` 等容器一同工作。

### First Set Calculation

```python
class CFGSystem
    ...
    def generate_first_set_iteratively(self) -> None:
        """
        Generate first set of all used pieces using iterative method.
        """

        current_first_sets_state: dict[Piece, set[Terminal | None]] = defaultdict(set)
        """
        Store current state of first sets info.

        This state will mutated with the iteration going forward,
        and at the time that iteration will not make any update
        on the state, the algorithm finished.
        """
        # for more info about default dict, checkout:
        # https://docs.python.org/3/library/collections.html#collections.defaultdict

        def calc_first_set_based_on_curr_state() -> bool:
            nonlocal current_first_sets_state

            mutated: bool = False

            for piece in self.used_pieces:

                piece_fisrt_set = current_first_sets_state[piece]
                """Current first set state of currently processing piece"""

                prev_first_set_size = len(piece_fisrt_set)

                # if piece is terminal, return set with only itself inside.
                if isinstance(piece, Terminal):
                    piece_fisrt_set.add(piece)
                    if len(piece_fisrt_set) > prev_first_set_size:
                        mutated = True
                    continue

                # if it's non-terminal, first of all, get all possible derivation

                piece = cast("NonTerminal", piece)  # type narrowed to non-terminal

                # record that if this non-terminal could deduce to epsilon
                contains_epsilon: bool = False

                # all possible derivation sequence that use this non-terminal as LHS
                derivations_set: set[Derivation] = self.get_all_derivation(piece)

                # deal with each RHS with current NonTerminal as source
                # update first set state in plcae
                for derivation in derivations_set:

                    # if this non-terminal could be derived to epsilon, then first set contains epsilon
                    if derivation.pieces is None:
                        contains_epsilon = True
                        continue

                    # loop through each part of the derivation
                    all_contains_epsilon_until_now: bool = True
                    for cur_piece_in_derivation in derivation.pieces:

                        # here means some symbol before this piece is non-epsilonable
                        # not need to continue in this case, this symbol will not affect first set
                        if not all_contains_epsilon_until_now:
                            break

                        # use current first set state
                        cur_piece_first_set = current_first_sets_state[
                            cur_piece_in_derivation
                        ]

                        # if all first set of the parts before contains epsilon
                        # then first set of this part should be added to first set of the source
                        piece_fisrt_set.update(cur_piece_first_set)

                        if not (None in cur_piece_first_set):
                            all_contains_epsilon_until_now = False

                    if all_contains_epsilon_until_now:
                        contains_epsilon = True

                # add epsilon into the set if needed
                if contains_epsilon:
                    piece_fisrt_set.add(None)
                else:
                    try:
                        piece_fisrt_set.remove(None)
                    except KeyError:
                        pass

                # check if first set size changed
                if len(piece_fisrt_set) > prev_first_set_size:
                    mutated = True

            return mutated

        # if the state mutated, calc_first_set_based_on_curr_state will return True
        # which will cause loop continue, until nothing changed anymore.
        while calc_first_set_based_on_curr_state():
            pass

        # adopt the final state as the result of first sets
        self.first_sets = current_first_sets_state

```

### Follow Set Calculation

```python
    def generate_follow_set_iteratively(self) -> None:
        """
        Generate follow set of all used pieces using iterative method.
        Must call generate_first_set_iterative() before calling this method.

        Note that `None` in follow set indicates that
        this symbol is deductable/productable under any condition.

        In the following algorithm, we put `None` inside the follow set of start symbol,
        essentially means:
        - In LL parser, When faced with any production with start symbol as LHS, perform production.
          (Actually there should be only one production use start symbol as LHS, so there
          should NOT be a chance that program use start set or follow set to resolve conflict)
        - When faced with any reducable-string that reduced to the start symbol using Bottom-up parser,
          reduce with no limit.
          This indicates that there should be NO any production that has
          a reduce-reduce conflict with Production that use start symbol as left-hand side.
          (In augmented grammar, there should be only one grammar related to start symbol S')
          Or in another case,  such conflict doesn't matter. (For example, start symbol S could produce lot of
          different derivation which may cause reduce-reduce error, however they all reduced to
          start symbol, so conflict doesn't matter)
        """
        logger.debug("Start generating follow set iteratively...")
        current_follow_sets_state: dict[Piece, set[Terminal | None]] = defaultdict(set)

        # Start symbol's follow set includes end-of-input marker (None or "$")
        start_symbol = self.entry
        if start_symbol is not None:
            # None in follow set represent reducuction with no limit.
            current_follow_sets_state[start_symbol].add(None)

        def calc_follow_set_based_on_curr_state() -> bool:
            nonlocal current_follow_sets_state
            mutated: bool = False

            # iterate all productions
            for cur_prod in self.production_list:
                cur_prod_source = cur_prod.source

                # If RHS is epsilon, skip processing
                if cur_prod.target.pieces is None:
                    continue

                # Temporary follow set for lhs of currently processing production
                # used in later loop to update follow set of rhs
                cur_lhs_follow_set: set[Terminal | None] = current_follow_sets_state[
                    cur_prod_source
                ]

                # at this point, RHS must NOT be empty

                # For production A -> ab...xyz, add follow(A) to follow(z) unconditionally
                right_most_symbol_follow_set = current_follow_sets_state[
                    cur_prod.target.pieces[-1]
                ]
                prev_len = len(right_most_symbol_follow_set)

                right_most_symbol_follow_set.update(cur_lhs_follow_set)

                if len(right_most_symbol_follow_set) > prev_len:
                    mutated = True

                # bool flag used in following loop
                all_contains_epsilon_until_now: bool = True

                pieces_count = len(cur_prod.target.pieces)
                # loop through each part in derivation in reverse order
                for i in range(pieces_count - 1, -1, -1):

                    # extract some values for later ref

                    cur_piece = cur_prod.target.pieces[i]

                    cur_piece_follow_set = current_follow_sets_state[cur_piece]

                    # first set should be calculated already by calling generated_first_set_iteratively()
                    cur_piece_first_set = self.first_sets[cur_piece]

                    # store size of follow set of current piece before change
                    # used later to decided if state mutated
                    cur_piece_prev_len = len(cur_piece_follow_set)

                    # read next piece first set and follow set if exists
                    # (that is, if this is not the last piece, and for follow set, this is nonterminal)
                    # used later to update follow set of current piece
                    next_piece_first_set = None
                    next_piece_follow_set = None

                    if i != pieces_count - 1:
                        next_piece = cur_prod.target.pieces[i + 1]

                        # get first set
                        next_piece_first_set = self.first_sets[next_piece]
                        # get follow set if it's nonterminal
                        if isinstance(cur_prod.target.pieces[i + 1], NonTerminal):
                            next_piece_follow_set = current_follow_sets_state[
                                next_piece
                            ]

                    # if next symbol could produce epsilon, add follow(next) to follow(cur)
                    if (
                        next_piece_first_set is not None  # exists
                        and None in next_piece_first_set  # could produce epsilon
                    ):
                        if (
                            next_piece_follow_set is not None
                        ):  # follow set exists (is nonterminal)
                            cur_piece_follow_set.update(next_piece_follow_set)

                    # if not the last one, add the first set of the following piece
                    # to the follow set of current piece
                    if next_piece_first_set is not None:
                        cur_piece_follow_set.update(next_piece_first_set - {None})

                    # check if cur_piece is mutated
                    if len(cur_piece_follow_set) > cur_piece_prev_len:
                        mutated = True

            return mutated

        # Iterate until no mutation occurs
        while calc_follow_set_based_on_curr_state():
            pass

        # Adopt the final state as the result of follow sets
        self.follow_sets = current_follow_sets_state
```

注意到，函数注解中对于 Follow Set 中存在的 `None` 元素的意义做出了解释。

理论上， Follow Set 中不允许存在 $\varepsilon$，本程序中存在于 Follow Set 中的 `None` 并不代表空串，而更像是书中的 `#` 符号，用于标记语句结尾属于该符号的 Follow 集合。

---

> 注：这里注意到程序中还有两个 `calc_first_set()` 和 `calc_follow_set()` 方法。这两个方法并没有使用迭代算法，并且目前已经被弃用。
>
> 需要计算相关集合时，请确保使用上述提供了代码的两个迭代版本的类方法。
