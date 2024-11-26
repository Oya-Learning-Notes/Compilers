# DFA Minimization

## 算法基础

对于 DFA 的化简，我们需要考虑以下的情况：

- **Unreachable States:** 不可到达的状态。
- **Dead States:** 死状态（无效状态）。
- **Non-distinguishable States:** 不可区分的状态（等价状态）。

### 不可到达的状态 & 无效状态

对于这两个问题，我们可以采取类似的处理思想，**通过迭代的方式** 逐个移除不符合条件的节点。

- **不可到达的状态：** 迭代移除所有 **入度为零** 的节点，直到无法再移除任何一个节点。
- **无效状态：** 迭代移除所有 **不是终态且出度为零** 的节点，直到无法再移除任何一个节点。

上述提供的方法中，对于无效状态的处理实际上**只是一个快速的近似方法，并不具有绝对的正确性**。考虑这样一个例子：

```
a->b:1
a->c:2
c->d:2
d->c:2
```

#### 无效状态检测的一个可能改进

![An DFA Example](https://github.com/user-attachments/assets/09a27674-0006-443c-8c95-b848a9e016d6)

注意到，如果使用上述的无效节点检查方法，我们将无法正确检测并移除 `C`, `D` 这两个无效节点。因为这两个节点虽然都无法到达终态，但它们构成了循环依赖，故上述算法无法检出。

一个更好的办法是，我们先求出原 DFA 的反向 DFA
（反向 DFA 在这里指的是对原 DFA 的所有转移进行取反，如 a->b:x 变成 b->a:x），
然后再删除所有在反向 DFA 中是不可到达的节点。（即所有从可接受节点出发，反向转移无法触及的节点）

### 等价状态

对于 DFA 的确定化，总体上，我们采用书中 "创建初始集合，并不断划分" 的方法。

其中最关键的部份，就是**确定对于某一个状态集合，是否需要拆分，如果需要，如何拆分**的问题。对于这一部份，我们采取以下策略：

1. **检查集合中每个节点可接受的转移字符集合**，若有不同，进行划分。
   迭代执行，直到任意集合中，**所有节点可接受的转义字符集合相同**。
2. 检查**集合中每个节点的出边（向其他节点转移的边）**，
   对于某一个相同的输入字符，如果转移到的状态集合不同，则进行划分。迭代执行直到所有状态集合不发生变化。

> 等价状态合并的过程，基本可以看做是对于书中算法的实现。

## 代码实现

### 数据输入 & 数据定义

关于数据定义，本次实验和上一次实验（NFA 确定化）采用了完全相同的输入模式以及数据结构。具体参见上一次的实验报告，这里不重复说明。

### 代码组织

总体而言，我们为 `FA` 类提供了成员方法 `minimize()`，该方法会返回一个新的 `DFA`，且返回的 DFA 为原来 DFA 的最小化版本。

此外，我们单独拆分了各种函数：

- `divide_nodes_by_acceptable_charset()` 根据节点接受字符集进行划分
- `divide_nodes_by_transition_target_set_idx()` 根据节点状态转移情况不同进行划分
- `_remove_unref_node()` 移除不可到达节点
- `_remove_unused_node()` 移除无效节点
- ...

### 完整代码

本次实验的完整代码可以在 GitHub 上进行查阅：

- [dfa_minimize.py 入口文件](https://github.com/Oya-Learning-Notes/Compilers/tree/main/code/py_impl/exp/3_minimize/dfa_minimize.py)
- [fa.py FA 类定义文件](https://github.com/Oya-Learning-Notes/Compilers/tree/main/code/py_impl/packages/automata/fa.py)

同时，我们会在文件末尾附上这些文件的文本内容，方便查阅。

---

附件：

# dfa_minimize.py

```python
from collections.abc import Sequence, Iterable
from typing import Literal, cast, Any
from dataclasses import replace
import re

from loguru import logger

from automata import FA, FANode, get_node_id
from automata.visualize import FADiGraph, AutomataStandardStyle

# Regex pattern to parse state transition strings in format: "state1 -> state2:condition"
# Groups: from_state (source state), to_state (destination state), condition (optional transition condition)
string_state_format_regex = re.compile(
    r"(?P<from_state>[a-zA-Z0-9_]+)\s*->\s*(?P<to_state>[a-zA-Z0-9_]+)(:(?P<condition>[a-zA-Z0-9,\\]+)){0,1}"
)


class BaseError(Exception):

    def __init__(self, name: str, message: str, *args: object) -> None:
        self.name = name
        self.message = message
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.message}({self.name})"

    def __str__(self) -> str:
        return repr(self)


class AutomataStringParseError(BaseError):
    def __init__(
        self,
        name: str = "unparsable_string",
        message: str = "Could not parse input automata definition string. ",
        line: str | None = None,
        *args: object,
    ) -> None:
        if line is not None:
            message += f"Line: {line} "
        super().__init__(name, message, *args)


def create_fa_node_from_lines(lines: Sequence[str]):

    # dict to store the node created during the process
    nodes_dict: dict[str, FANode[str, str]] = {}

    def get_node_by_id(node_id: str) -> FANode[str, str]:
        """
        Return a node by node_id

        If node with the id is already exists, directly return the previous instance,
        else create a new node.
        """
        nonlocal nodes_dict
        if node_id not in nodes_dict.keys():
            nodes_dict[node_id] = FANode(nid=str(get_node_id()), label=node_id)
        return nodes_dict[node_id]

    def extract_transition_list(condition: str | None) -> list[str]:
        """
        Extract a list of transition chars from condition string.
        """
        if condition is None:
            return []

        # condition could be a comma seperated string
        # a,b,c
        # which should be splited to [a,b,c]
        conditions = [c.strip() for c in condition.split(",")]

        return conditions

    def process_one_line(line: str) -> None:
        """
        Process with one single line of input

        The input should have format a->b[:t]
        """
        line = line.strip()

        # skip empty line
        if line == "":
            return

        # if it's a type-declare line
        if line.startswith("start:") or line.startswith("end:"):
            _info_list = line.split(
                ":", 1
            )  # split the string with ":", only split one time.
            node_type = cast("Literal['start', 'end']", _info_list[0])
            node_id = _info_list[1].strip()

            if node_type == "start":
                get_node_by_id(node_id).is_start = True
            elif node_type == "end":
                get_node_by_id(node_id).is_end = True

            return

        # try match from the start
        match = string_state_format_regex.match(l)
        if match is None:
            raise AutomataStringParseError(
                message="Failed to retrive info from the input line.", line=line
            )

        # take out group info from regex match
        from_state = match.group("from_state")
        to_state = match.group("to_state")
        condition = match.group("condition")

        # determine transitions
        transition_list = extract_transition_list(condition)

        if to_state == "6":
            pass

        from_state_node = get_node_by_id(from_state)
        to_state_node = get_node_by_id(to_state)

        if len(transition_list) == 0:
            # no transition, add epsilon transition
            from_state_node.point_to(char=None, node_id=to_state_node.nid)
        else:
            # has transitions, add all
            for t in transition_list:
                from_state_node.point_to(char=t, node_id=to_state_node.nid)

    # iterate every line
    for l in lines:
        process_one_line(l)

    # notice in the node_dict of this function, we use user-defined labels as the
    # key of the dict, which is not necessarily the actual nid of that node.
    # The nid of the nodes are actually assigned automatically using get_node_id()
    # So here we could not directly use the node_dict, instead, we use a corrected
    # version
    node_dict_with_correct_nid = dict()
    for i in nodes_dict.values():
        node_dict_with_correct_nid[i.nid] = i

    return FA(nodes_dict=node_dict_with_correct_nid)


_test_case = """
start:1
end:8
1->2
2->2:b
2->3:c
3->8
1->4
4->9:a
9->10:b
10->5:c
5->8
1->6
6->6:b,c
6->7:a
7->8
""".split(
    "\n"
)


def main():
    fa = create_fa_node_from_lines(_test_case)

    def get_node_label(nid: str, node: FANode):
        label_repr = ""
        label = node.label

        def get_repr_from_label(label) -> str:
            """
            Deal with str, int, Iterable
            """

            if isinstance(label, str):
                return label

            if isinstance(label, Iterable):
                repr_str = "{"
                for i in label:

                    addition = f"{get_repr_from_label(i)},"
                    if len(addition) > 5:
                        addition += "\n"
                    else:
                        addition += " "

                    repr_str += addition
                repr_str = repr_str[:-2] + "}"
                return repr_str

            return str(label)

        return get_repr_from_label(label)

    graph = FADiGraph(
        name="Original FA",
        fa=fa,
        style=replace(AutomataStandardStyle, get_node_label=get_node_label),
    )
    graph.render()

    dfa = fa.to_dfa(new_fa=True)

    dfa_graph = FADiGraph(
        name="Determinized FA",
        fa=dfa,
        style=replace(AutomataStandardStyle, get_node_label=get_node_label),
    )
    dfa_graph.render()

    dfa = dfa.__deepcopy__()

    dfa_graph = FADiGraph(
        name="Determinized FA Copy",
        fa=dfa,
        style=replace(AutomataStandardStyle, get_node_label=get_node_label),
    )
    dfa_graph.render()

    min_dfa = dfa.minimize()

    min_dfa_graph = FADiGraph(
        name="Minimized DFA",
        fa=min_dfa,
        style=replace(AutomataStandardStyle, get_node_label=get_node_label),
    )
    min_dfa_graph.render()


if __name__ == "__main__":
    main()
```

# fa.py

```python
from typing import TypeAlias, Set, Collection, Any
from loguru import logger
import graphviz as gv
from copy import copy, deepcopy

from .utils import get_node_id

# # Notice that FANodeID and FAChar must be hashable type.
# # Since the hash method is used when checking if two nodes have identical transition moves. That's to check if two
# # pointers collection has the same hash value.
# type str = str


class FANode[LabelType, FAChar]:

    def __init__(
        self,
        is_start=False,
        is_end=False,
        nid: str | None = None,
        label: LabelType | None = None,
        pointers: list[tuple[FAChar | None, str]] | None = None,
    ) -> None:
        if nid is None:
            nid = str(get_node_id())

        if pointers is None:
            pointers = []

        self.nid = nid
        self.is_start = is_start
        self.is_end = is_end
        self.pointers = pointers
        self.label = label

    def __copy__(self):
        return FANode(
            is_start=self.is_start,
            is_end=self.is_end,
            nid=str(get_node_id()),
            label=self.label,
            pointers=self.pointers,
        )

    def __deepcopy__(self, *args, **kwargs):
        """
        Deepcopy a node with new nid and label and empty pointer
        """
        nid = str(get_node_id())
        return FANode[str, str](
            is_start=self.is_start,
            is_end=self.is_end,
            nid=nid,
            label=nid,
        )

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __hash__(self) -> int:
        return hash(self.nid)

    def has_same_pointers(self, other):
        """
        Check if this two states have same transition moves.

        This method usually be used when minimizing DFA.
        """
        return self.hash_of_pointers() == other.hash_of_pointers()

    def __repr__(self) -> str:
        repr_str = f"<FANode id:{self.nid} Start:{self.is_start} Fin:{self.is_end}>\n"
        for p in self.pointers:
            repr_str += f"<Pointer input:{p[0]} nextId:{p[1]}/>\n"
        repr_str += "</FANode>"

        return repr_str

    def try_move(self, next_input: FAChar | None) -> set[str] | None:
        """
        Return a set of FANodeID if we successfully find the next node to move on. Otherwise, return `None`.
        """
        move_candidate: set[str] = set()  # id list of the movable node next.

        # loop through all pointers to check which node could we move next.
        for pointer in self.pointers:
            if pointer[0] == next_input:
                move_candidate.add(pointer[1])

        if len(move_candidate) == 0:
            return None

        return move_candidate

    def is_dfa(self) -> bool:
        """
        If this node could be a DFA node.
        """
        char_list: list[FAChar | None] = []

        # first, to get pointers set, that means no pointers are identical
        deduplicated_pointers = set(self.pointers)

        # get char list
        for char, node_id in deduplicated_pointers:
            char_list.append(char)

        # get char set (deduplicated version of char list)
        char_set = set(char_list)

        # if charset smaller than char list, means there is duplicated char
        # which means, the identical input with a char may led to two different moves
        #
        # If this occurred, this node could not be the state inside a DFA, return False
        if len(char_set) < len(char_list):
            return False

        # DFA do NOT allow epsilon moves.
        if None in char_set:
            return False

        return True

    def point_to(self, char: FAChar | None, node_id: str) -> bool:
        """
        Add a pointer to this Node if not exists. Use `None` to represent epsilon move.

        Returns `False` if already exists that pointer, else return `True`.
        """
        # construct new pointer
        pointer_tuple: tuple[FAChar | None, str] = (char, node_id)

        # return False if exists
        if pointer_tuple in self.pointers:
            return False

        # Add to pointers list
        self.pointers.append(pointer_tuple)
        return True

    def get_acceptable_charset(self) -> frozenset[FAChar | None]:
        """
        Return a frozenset of acceptable transition char of this node
        """
        charset: set[FAChar | None] = set()
        for char, nid in self.pointers:
            charset.add(char)

        return frozenset(charset)

    def hash_of_acceptable_charset(self) -> int:
        """
        Return the hash value of the set of acceptable transaction char.

        This method is usually used by the DFA minimize process.
        """
        charset = self.get_acceptable_charset()
        return hash(charset)

    def hash_of_pointers(self, consider_is_end: bool = False) -> int:
        """
        Return logical hash values of a group of pointers.

        Params:

        - consider_is_end: If `True`, node with different is_end value will have different hash

        Notice:

        - This method will ignore the order of the pointers in the list.
        - This method will ignore the duplicated pointer.

        Nodes with same pointers hash value should be able to merge when minimizing DFA.
        """
        pointers_set = set(
            self.pointers
        )  # convert pointers list to set. This will ignore order & remove duplicated
        hashval = hash(frozenset(pointers_set))
        if consider_is_end:
            hashval = hash(frozenset([hashval, self.is_end]))
        return hashval


class FA[LabelType, CharType]:

    def __init__(
        self,
        nodes_dict: (
            dict[str, FANode[LabelType, CharType]] | list[FANode[LabelType, CharType]]
        ),
    ) -> None:
        self._max_match = 0
        self.max_match = 0

        # convert list to dict if needed
        if isinstance(nodes_dict, list):
            new_dict = {}
            for node in nodes_dict:
                new_dict[node.nid] = node
            nodes_dict = new_dict

        # store nodes in this automaton
        # pattern: nodes[<node_id>] = node_instance
        self.nodes: dict[str, FANode[LabelType, CharType]] = nodes_dict

        # store current set of active states.
        # empty set should represent this machine has stuck.
        _current_states: frozenset[FANode[LabelType, CharType]]

        self.init_state()

    def __repr__(self) -> str:
        repr_str = "<FA>\n"
        for node in self.nodes.values():
            repr_str += str(node)
            repr_str += "\n"

        repr_str += "</FA>"
        return repr_str

    def __copy__(self):
        """
        Make a shadow copy of this Automaton
        """
        return FA(nodes_dict=self.nodes)

    def __deepcopy__(self, **kwargs) -> "FA[str, CharType]":
        # create new nodes
        old_to_new_nodes: dict[FANode[LabelType, CharType], FANode[str, CharType]] = (
            dict()
        )
        old_nid_to_new_nid: dict[str, str] = dict()

        # create new nodes using deepcopy
        label_count = 0
        for nid, n in self.nodes.items():
            label_count += 1
            new_n = n.__deepcopy__()
            new_n.label = str(label_count)
            old_to_new_nodes[n] = new_n  # type: ignore
            old_nid_to_new_nid[nid] = new_n.nid

        # add the pointers
        for old_n, new_n in old_to_new_nodes.items():
            for char, nid in old_n.pointers:
                new_n.point_to(char=char, node_id=old_nid_to_new_nid[nid])

        # construct new nodes dict
        new_nodes = dict()
        for new_n in old_to_new_nodes.values():
            new_nodes[new_n.nid] = new_n

        return FA(nodes_dict=new_nodes)

    def is_dfa(self) -> bool:
        """
        Check if this Automaton is Determined Finite Automaton
        """
        for node in self.nodes.values():
            if not node.is_dfa():
                return False
        return True

    def get_start_states(
        self, find_epsilons: bool = False
    ) -> frozenset[FANode[LabelType, CharType]]:
        """
        Get a set of start states of this automaton.

        Params:

        - ``find_epsilons`` If `true`, will return the epsilon state set of the start states.
        """
        if not find_epsilons:
            return frozenset(n for (nid, n) in self.nodes.items() if n.is_start)
        return self.find_epsilons(
            set(n for (nid, n) in self.nodes.items() if n.is_start)
        )

    def get_current_state(self) -> frozenset[FANode[LabelType, CharType]]:
        """
        Return a copy of the set including the current state of this FA.
        """
        return copy(self._current_states)

    def set_current_state(self, states: frozenset[FANode[LabelType, CharType]]) -> None:
        if len(states) == 0:
            raise RuntimeError(
                "Could not set current state to an empty set, which representing FA stuck."
            )
        self._current_states = states

    def get_end_states(self) -> frozenset[FANode[LabelType, CharType]]:
        return self.find_epsilons(set(n for nid, n in self.nodes.items() if n.is_end))

    def init_state(self) -> "FA[LabelType, CharType]":
        """
        Set the initial state of this FA.

        Return this FA itself.
        """
        self._current_states = self.get_start_states(find_epsilons=True)
        self._max_match = 0
        self.max_match = 0
        return self

    def find_epsilons(
        self, input_states: Set[FANode[LabelType, CharType]]
    ) -> frozenset[FANode[LabelType, CharType]]:
        """
        Find the epsilon closure of the input_states
        """
        _input_states = set(input_states)
        # iterate all nodes to find epsilon moves
        it_nodes = _input_states
        while True:
            found_epsilons: set[str] = set()

            # all directly linked epsilon nodes with it_nodes
            for new_st in it_nodes:
                new_id = new_st.try_move(None)
                if new_id is None:
                    continue
                found_epsilons.update(new_id)

            # break if not found any epsilon nodes
            if len(found_epsilons) == 0:
                break

            # convert id to nodes instance
            epsilon_nodes = self._convert_id_set_to_node_set(found_epsilons)

            # we still need to check if there is any epsilon moves in the newly found nodes
            it_nodes = epsilon_nodes

            before_count: int = len(_input_states)
            # also the found node should be added to new states
            _input_states.update(epsilon_nodes)

            # if final states count not increase, break
            after_count: int = len(_input_states)
            if after_count == before_count:
                break

        return frozenset(_input_states)

    @staticmethod
    def get_all_possible_input_on_state(
        state: frozenset[FANode[LabelType, CharType]]
    ) -> set[CharType]:
        """
        Get all possible input CharType set on certain state.

        Notice epsilon move is ignored.
        """
        all_possible_input: set[CharType] = set()

        for node in state:
            for pointer in node.pointers:
                if pointer[0] is None:
                    continue
                all_possible_input.add(pointer[0])

        return all_possible_input

    def move_next(self, next_input: CharType) -> bool:
        """
        Try to move this FA to next states with given input, update current state.

        Return `True` if this is a valid move, else return `False`.
        """
        next_state = self._move_next(
            prev_states=self._current_states, next_input=next_input
        )

        # if move failed, update state to empty set, return False.
        if next_state is None:
            self._current_states = frozenset()
            return False

        # valid move, update state
        self._max_match += 1
        self._current_states = next_state

        # if current state is accepted, update max_match
        if self.is_accepted():
            self.max_match = self._max_match

        return True

    def _move_next(
        self, prev_states: frozenset[FANode[LabelType, CharType]], next_input: CharType
    ) -> frozenset[FANode[LabelType, CharType]] | None:
        """
        Try to find the next states with given previous state in this FA.

        Params:

        - `input` Should be a single character.

        Return set of the new states if move valid, else return None.

        Notice:

        This method should NOT has any side effect to the current FA.
        """

        # no active state, FA stuck.
        if len(prev_states) == 0:
            return None

        # init a list to store new state
        new_states: set[FANode[LabelType, CharType]] = set()

        # find new states on input
        for cur_state in prev_states:
            new_id = cur_state.try_move(next_input)
            if new_id is None:
                continue
            new_states.update(self._convert_id_set_to_node_set(new_id))

        # if no new states, failed to move
        if len(new_states) == 0:
            return None

        # find epsilon states of new states
        epsilon_nodes = self.find_epsilons(new_states)

        # also the found node should be added to new states
        new_states.update(epsilon_nodes)

        # update state and return True
        return frozenset(new_states)

    def move_next_str(self, input_sequence: list[CharType]) -> bool:
        """
        Input a consecutive string into FA

        Param:

        - `next_input` A string, could more than on char.

        Return:

        - Return `true` if accepted, else return `false`.
        """

        for char in input_sequence:
            valid_move = self.move_next(char)
            if not valid_move:
                return False

        return self.is_accepted()

    def test_str(self, input_str: list[CharType]) -> bool:
        """
        Test if a string could be match by this FA.

        Similar to `move_next_str()`, but this method will set initial state before test.
        """
        return self.init_state().move_next_str(input_str)

    def is_accepted(self):
        """
        Check if FA currently in an Accept state.

        If one of the current state is the end state, this automaton is accepted in this state. Else is not.
        """
        for state in self._current_states:
            if state.is_end:
                return True

        return False

    def _convert_id_set_to_node_set(self, id_set: set[str]):
        """
        Convert a list of nid to the FANode object

        Notice: This method will deduplicated the nid before converting
        """
        return [self.nodes[nid] for nid in id_set]

    def to_dfa(
        self, new_fa: bool = True, minimize: bool = True
    ) -> "FA[frozenset[LabelType],CharType]":
        """
        Try to convert current FA to DFA.

        Params:

        - `new_fa` If true, return a newly created FA instance instead of mutating this instance.
        """
        # store sets of states for DFA, init it with start state
        # key should be the set of states, value should be the FANode object for the corresponding DFA states
        dfa_states_dict: dict[
            tuple[FANode[LabelType, CharType], ...], FANode[list[LabelType], CharType]
        ] = {}

        discovered_states_set: set[frozenset[FANode[LabelType, CharType]]] = set()
        states_sets_points_to: list[
            tuple[
                frozenset[FANode[LabelType, CharType]],
                frozenset[FANode[LabelType, CharType]],
                CharType,
            ]
        ] = []
        """
        list of pointers, from a states set to another states set
        """

        # record if a dfa state has been visited
        visited_dict: dict[FANode, bool] = {}

        # get start state node
        start_states_set = frozenset(self.get_start_states(find_epsilons=True))

        # process list
        process_list: list[frozenset[FANode[LabelType, CharType]]] = [start_states_set]

        # deal with process list until it's empty
        while len(process_list) > 0:
            # deal with last element in proc list
            curr_states_set = process_list.pop()

            # discovered, continue
            if curr_states_set in discovered_states_set:
                continue

            # add to discovered
            discovered_states_set.add(frozenset(curr_states_set))

            # if prev_state in states dict, retrieve it, else create it
            # prev_state_node = dfa_states_dict.get(tuple(curr_states_set))
            # if prev_state_node is None:
            #     prev_state_node = self._create_set_state(curr_states_set)
            #     dfa_states_dict[tuple(curr_states_set)] = prev_state_node

            # if the retrieved state already in dfa_states_dict, skip
            # if visited_dict.get(prev_state_node):
            #     continue
            # visited_dict[prev_state_node] = True

            # find all possible input
            all_possible_input = self.get_all_possible_input_on_state(curr_states_set)

            for input_char in all_possible_input:
                # for each input, get the next state
                next_states_set_on_curr_char = self._move_next(
                    curr_states_set, input_char
                )
                assert (
                    next_states_set_on_curr_char is not None
                )  # this must not be None, since input_char should be valid.

                # add pointers for prev state
                states_sets_points_to.append(
                    (
                        frozenset(curr_states_set),
                        frozenset(next_states_set_on_curr_char),
                        input_char,
                    )
                )

                # add discovered new states to process list
                process_list.append(frozenset(next_states_set_on_curr_char))

        nodes_dict_for_dfa: dict[str, FANode[frozenset[LabelType], CharType]] = {}
        states_set_to_node_map: dict[
            frozenset[FANode[LabelType, CharType]],
            FANode[frozenset[LabelType], CharType],
        ] = {}

        # create dfa nodes
        for st in discovered_states_set:
            dfa_node = self._create_set_state(st)
            nodes_dict_for_dfa[dfa_node.nid] = dfa_node
            states_set_to_node_map[frozenset(st)] = dfa_node

            if st == start_states_set:
                dfa_node.is_start = True

        # create pointers
        for start_st, end_st, input_char in states_sets_points_to:
            start_node = states_set_to_node_map[start_st]
            end_node = states_set_to_node_map[end_st]
            start_node.point_to(char=input_char, node_id=end_node.nid)

        return FA(nodes_dict=nodes_dict_for_dfa)

    def minimize_for_parser(
        self,
        check_dfa: bool = False,
        new_fa: bool = False,
        skip_if_pointers_empty: bool = False,
    ) -> "FA[LabelType, CharType]":
        """
        Try to minimize this FA.

        Params:

        - `check_dfa` If true, check if this FA is DFA before perform minimize
        - `new_fa` If true, return a newly created FA

        Notice that only DFA could be simplified.
        """

        if check_dfa and (not self.is_dfa()):
            raise RuntimeError(
                "Only Determined Finite Automaton should be minimized, you are trying to minimize a NFA"
            )

        if new_fa:
            return copy(self).minimize_for_parser(new_fa=False)

        # store the node with certain transition hash
        transition_hash_dict: dict[int, set[FANode]] = {}

        # group nodes with same transition hash
        for node in self.nodes.values():
            transition_hash = node.hash_of_pointers(consider_is_end=True)
            nodes_set_for_this_hash = transition_hash_dict.setdefault(
                transition_hash, set()
            )
            nodes_set_for_this_hash.add(node)

        # merge those with same hash
        for nodes_set_with_same_hash in transition_hash_dict.values():
            self.merge_nodes(nodes_set_with_same_hash, skip_if_pointers_empty)

        # remove unref node
        self._remove_unref_node()
        return self

    def minimize(self) -> "FA[frozenset[LabelType], CharType]":
        """
        Try to minimize current automata. Requires this automata to be a DFA first.
        """
        if not self.is_dfa():
            raise RuntimeError(
                "Only Determined Finite Automaton should be minimized, you are trying to minimize a NFA"
            )

        # sets that stores set of nodes that we assume it's equivalent
        # this set will changes during iteration, and will represents the
        # final result once iteration finished
        equivalent_nodes_set: list[set[FANode[LabelType, CharType]]] = []

        def find_set_index_a_node_links_to(
            node: FANode[LabelType, CharType]
        ) -> int | None:
            nonlocal equivalent_nodes_set

            # try to find the index of the sets that this node lies in
            for i in range(len(equivalent_nodes_set)):
                node_set = equivalent_nodes_set[i]
                if node in node_set:
                    return i

            # could not found
            return None

        # two temp set to store two init sets
        _normal_nodes_set: set[FANode[LabelType, CharType]] = set()
        _accept_nodes_set: set[FANode[LabelType, CharType]] = set()

        # calculate two init sets
        for n in self.nodes.values():
            if n.is_end:
                _accept_nodes_set.add(n)
            else:
                _normal_nodes_set.add(n)

        # index two init sets
        equivalent_nodes_set.extend([_normal_nodes_set, _accept_nodes_set])

        def divide_nodes_by_acceptable_charset(nodes_set: set[FANode[LabelType, CharType]]):
            charset_hash_dict: dict[int, set[FANode[LabelType, CharType]]] = dict()

            for n in nodes_set:
                hash_val = hash(n.hash_of_acceptable_charset())
                charset_hash_dict.setdefault(hash_val, set()).add(n)

            return charset_hash_dict

        def divide_nodes_by_transition_target_set_idx(
            nodes_set: set[FANode[LabelType, CharType]], char: CharType | None
        ):
            if char is None:
                raise RuntimeError("DFA should not have epsilon moves.")
            nonlocal equivalent_nodes_set

            target_set_idx_dict: dict[int, set[FANode[LabelType, CharType]]] = dict()

            for n in nodes_set:
                # get what node this node points to, when input is char
                target_node_nid = None
                for pointer in n.pointers:
                    if pointer[0] == char:
                        target_node_nid = pointer[1]
                if target_node_nid is None:
                    raise RuntimeError("Could not find target node")

                set_idx = find_set_index_a_node_links_to(self.nodes[target_node_nid])
                assert set_idx is not None
                target_set_idx_dict.setdefault(set_idx, set()).add(n)

            return target_set_idx_dict

        def add_new_sets_from_dict_values(
            data: dict[Any, set[FANode[LabelType, CharType]]]
        ):
            nonlocal equivalent_nodes_set
            logger.debug("Splitting")
            for nodes_set in data.values():
                for n in nodes_set:
                    logger.debug(n.nid)
                logger.debug("----------")
                equivalent_nodes_set.append(nodes_set)

        def try_divide_first_neq_set() -> bool:
            """Try to find and divided the first set that contains inequivalent nodes
            inside equivalent_nodes_set.

            Return `true` if found inequivalent set, else return no
            """
            nonlocal equivalent_nodes_set  # bind to outer variable

            # index_nodes_mapping: dict[int, set[FANode[LabelType, CharType]]] = (
            #     dict()
            # )  # tmp variable

            # iterate all sets in the list
            neq_set_idx: int | None = None
            for set_idx in range(len(equivalent_nodes_set)):
                nodes_set = equivalent_nodes_set[set_idx]

                pointers_map = divide_nodes_by_acceptable_charset(nodes_set=nodes_set)
                if len(pointers_map) > 1:
                    logger.debug("Pointers of these node not equal!")
                    neq_set_idx = set_idx
                    add_new_sets_from_dict_values(pointers_map)
                    break

                chars = self.get_all_possible_input_on_state(frozenset(nodes_set))
                for char in chars:
                    transition_map = divide_nodes_by_transition_target_set_idx(
                        char=char, nodes_set=nodes_set
                    )

                    if len(transition_map) > 1:
                        logger.debug(f"Transition on {char} of these node not equal!")
                        neq_set_idx = set_idx
                        add_new_sets_from_dict_values(transition_map)
                        break

            # remove old set
            if neq_set_idx is not None:
                equivalent_nodes_set.pop(neq_set_idx)
                return True

            return False

        # iterate
        while try_divide_first_neq_set() == True:
            pass

        nodes_dict_for_minimized_dfa: dict[
            str, FANode[frozenset[LabelType], CharType]
        ] = dict()

        sets_idx_to_new_nodes_mapping: dict[
            int, FANode[frozenset[LabelType], CharType]
        ] = dict()

        # at this point, the nodes in the same set will be equivalent
        # merge nodes in the final sets
        for idx in range(len(equivalent_nodes_set)):
            nodes_set = equivalent_nodes_set[idx]
            new_state = self._create_set_state(frozenset(nodes_set))
            nodes_dict_for_minimized_dfa[new_state.nid] = new_state
            sets_idx_to_new_nodes_mapping[idx] = new_state

        # contruct pointers (transitions) of the new DFA
        for from_set_idx in range(len(equivalent_nodes_set)):
            nodes_set = equivalent_nodes_set[from_set_idx]

            from_minimized_node = sets_idx_to_new_nodes_mapping[from_set_idx]

            # retrive one node from this set
            some_node = None
            for n in nodes_set:
                some_node = n
                break
            if some_node is None:
                raise RuntimeError("A minimized set has no node which is impossible")

            # implement transition based on some_node
            for char, point_to_nid in some_node.pointers:
                # get point_to_node based on nid
                target_node = self.nodes[point_to_nid]
                # get the set that target node in
                target_set_idx = find_set_index_a_node_links_to(target_node)
                assert target_set_idx is not None
                # get the minimized node that this set represents
                target_minimized_node = sets_idx_to_new_nodes_mapping[target_set_idx]
                from_minimized_node.point_to(char, target_minimized_node.nid)

        new_fa = FA(nodes_dict=nodes_dict_for_minimized_dfa)

        new_fa._remove_unused_node()

        return new_fa

    def _remove_unref_node(self) -> None:
        """
        Remove node from this FA if no pointers points to it.
        """
        ref_set: set[str] = set()

        ref_set.update([st.nid for st in self.get_start_states(find_epsilons=True)])

        for node in self.nodes.values():
            for pointer in node.pointers:
                ref_set.add(pointer[1])

        # get refed set
        ref_node_set = self._convert_id_set_to_node_set(ref_set)

        # convert set to dict
        ref_dict: dict[str, FANode] = dict()
        for n in ref_node_set:
            ref_dict[n.nid] = n

        self.nodes = ref_dict

    def _remove_nodes_and_all_relavant_pointers(
        self, node: FANode[LabelType, CharType]
    ):
        for n in self.nodes.values():
            new_pointers: list[tuple[CharType | None, str]] = []
            for p in n.pointers:
                if p[1] == node.nid:
                    continue
                new_pointers.append(p)

            n.pointers = new_pointers

        self.nodes.pop(node.nid)

    def _remove_unused_node(self) -> None:
        """
        Remove node from this FA if this node could not reach accept state"""

        mutated: bool = True
        while mutated:
            mutated = False
            unreached_node = None

            for node in self.nodes.values():
                if node.is_end:
                    continue

                if len(node.pointers) == 0:
                    unreached_node = node
                    mutated = True
                    break

            if unreached_node is not None:
                logger.debug(f"Removing unused: {unreached_node.label}")
                self._remove_nodes_and_all_relavant_pointers(unreached_node)

    # def minimize_1(
    #     self,
    #     check_dfa: bool = False,
    #     new_fa: bool = False,
    #     skip_if_pointers_empty: bool = False,
    # ) -> "FA[LabelType, CharType]":
    #     """
    #     Try to minimize this FA.

    #     Params:

    #     - `check_dfa` If true, check if this FA is DFA before perform minimize
    #     - `new_fa` If true, return a newly created FA

    #     Notice that only DFA could be simplified.
    #     """

    #     if check_dfa and (not self.is_dfa()):
    #         raise RuntimeError(
    #             "Only Determined Finite Automaton should be minimized, you are trying to minimize a NFA"
    #         )

    #     if new_fa:
    #         return copy(self).minimize_for_parser(new_fa=False)

    #     # store the node with certain transition hash
    #     transition_hash_dict: dict[int, set[FANode]] = {}

    #     # group nodes with same transition hash
    #     for node in self.nodes.values():
    #         transition_hash = node.hash_of_pointers(consider_is_end=True)
    #         nodes_set_for_this_hash = transition_hash_dict.setdefault(
    #             transition_hash, set()
    #         )
    #         nodes_set_for_this_hash.add(node)

    #     # merge those with same hash
    #     for nodes_set_with_same_hash in transition_hash_dict.values():
    #         self.merge_nodes(nodes_set_with_same_hash, skip_if_pointers_empty)

    #     # remove unref node
    #     self.remove_unref_node()
    #     return self

    def merge_nodes(
        self, nodes_set: set[FANode], skip_if_pointers_empty: bool = False
    ) -> None:
        if len(nodes_set) < 2:
            return

        # known issue: the nid of the nodes not been merged.

        # generate standard node
        std_node = FANode[list[LabelType], CharType](label=[])

        for i in nodes_set:
            if i.is_end:
                std_node.is_end = True
            if i.is_start:
                std_node.is_start = True
            std_node.pointers = i.pointers
            # add label
            try:
                assert std_node.label is not None
                std_node.label.extend(i.label)  # type: ignore
            except Exception:
                raise RuntimeError(
                    "Could not deal with DFA Node label when merging nodes."
                )

        # skip if needed
        if skip_if_pointers_empty and (
            (std_node.pointers is None) or (len(std_node.pointers) == 0)
        ):
            return

        # add std_node to this fa
        self.nodes[std_node.nid] = std_node  # type: ignore

        for node in self.nodes.values():
            # replace all pointers that point to nodes in this set to std node
            pointer_to_be_replaced: list[tuple[CharType | None, str]] = []
            for pointer in node.pointers:
                # get the node that this pointer points to
                point_to_nid = pointer[1]
                point_to_node = self.nodes[point_to_nid]

                # if matched, add to replace
                if point_to_node in nodes_set:
                    pointer_to_be_replaced.append(pointer)

            # replace pointer to std node (add new pointer points to std_node, remove old pointer)
            for p in pointer_to_be_replaced:
                node.pointers.append(tuple[CharType, str]([p[0], std_node.nid]))  # type: ignore
                node.pointers.remove(p)

    @staticmethod
    def _create_set_state(
        state_set: frozenset[FANode[LabelType, CharType]]
    ) -> FANode[frozenset[LabelType], CharType]:
        """
        Create a new state from a set of states. Usually used when converting NFA to DFA
        """
        # check if it's start state
        # is_start_state: bool = False
        # for st in state_set:
        #     if st.is_start:
        #         is_start_state = True
        #         break

        # check if it's end state
        is_end_state: bool = False
        for st in state_set:
            if st.is_end:
                is_end_state = True
                break

        nid_set: set[str] = set(n.nid for n in state_set)
        new_nid = str(nid_set)

        new_label = frozenset([st.label for st in state_set if st.label is not None])

        # create new node
        new_state_node = FANode[frozenset[LabelType], CharType](
            nid=new_nid,
            is_end=is_end_state,
            label=new_label,
        )

        return new_state_node
```
