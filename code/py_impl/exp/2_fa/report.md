
# NFA Determinization

本次实验的主要内容是对于不确定有限自动机的自动化。我们主要通过状态转移和求 $\varepsilon-Closure$ 来确定一个NFA所对应的DFA。 *（注：这种做法并不保证求出来的DFA是最简的。我们在完成确定化后，仍然需要对得到的DFA进行化简操作，但这一部份并不属于本次实验的内容）* 

## 基本算法

我们在理论基础上，采用书中给出的状态集合和求空闭包的方法。在具体实现上，我们实现了一个 `Automata` 类，并编写了算法所用到的相关函数，最终组合调用实现了确定化算法。下方将会进行详细解释。

### 定义节点数据结构

`FANode` 类用于定义 `Automata` 中使用的节点，简要结构如下：

```python
class FANode[LabelType, FAChar]:
    nid: FANodeID  # should be unique across the whole app lifecycle across all created nodes.
    is_start: bool
    is_end: bool
    pointers: list[tuple[FAChar, FANodeID]]
    label: LabelType | None  # label of this node
```

记录的信息包括：

- 该节点的类型（开始节点/结束节点）
- 该节点的标识符（唯一）和名称
- 该节点可能的状态转移条件 `pointers`

`pointers` 的储存结构如下：

```python
[
	('x', node_id_1),
	('y', node_id_2),
	...
]
```

此外，节点类 `FANode` 中还包含各种有关的成员函数，这里因篇幅原因略去。

### Find Epsilons

`FA.find_epsilons(input_state: set[FANode])` 函数，用于寻找某一个状态集合的 $\varepsilon-Closure$.

由类型标志可知，该函数接收一个节点集合作为参数（下称：传入集合）。满足下列条件的节点将会被返回：

- 所有在传入集合中的节点
- 可以由某个在传入集合中节点经过任意次 $\varepsilon$ 转移到达的节点。

根据如上定义，不难知道对于一个 `input_state: set[FANode]`，`output_state = FA.find_epsilons(input_state)` 是一**个大小不小于原集合**的新集合。

### Get All Possible Input

`FA.get_all_possible_input_on_state(states_set)` 用于求出对于某个状态集合，其所有可能的合法非空输入。

对于一个状态集合 $I$, 某一个字符 $x$ 属于 $I$ 的合法非空输入，当且仅当：
- $I$ 作为自动机的当前状态集合时，可以接收这个字符 $x$ 并转移到一组新的状态 $I’$
- $x \neq \varepsilon$

这个函数将会被用于搜索一个NFA所有可能**从开始状态集合出发，触及到的状态集合**，进而将这些集合定义为新的DFA中的状态。

### Move Next

`FA._move_next(states_set, char)` 接收一个状态集合以及一个字符。这个方法会将	`states_set` 考虑为当前自动机的状态，并返回这个状态接收到字符 `char` 之后，将会转移到到新状态。

这里值得注意的是，该方法**首先寻找某一个状态集合收到某个字符后，将会直接转移到的新状态，然后，进一步对得到的状态求空闭包**。

且如果对于输入字符，没有任意一个符合条件的新状态，该函数会直接返回 `None`

___

不难注意到，该方法不仅可以用于求NFA的闭包，同时也恰恰时NFA运行时的状态转移逻辑，故被命名为 `move_next()`

### To DFA

通过使用上面提到的各个函数，我们得以编写一个总的 NFA to DFA 函数，其大致工作逻辑如下：

1. 确定该自动机的开始状态，并加入待探索队列。
2. 取出待探索队列首位的状态集合，对其做以下处理：
	1. 如果当前状态集合已经在DFA状态中，跳过。否则，将该状态集合加入新的DFA状态。
	2. 搜索从当前状态集合开始，通过该状态集合所有有效非空字符，可以转移到的各种新状态集合。所有搜索到的集合，都加入待探索队列。

本质上，这种算法实现可以理解为从开始状态集合  $I_0$ 开始，通过BFS搜索，逐一尝试不同合法字符输入时的转移情况，从而发现新的状态。

![image](https://github.com/user-attachments/assets/da25ade1-0696-46d9-9332-496dcd5d4b1c)


## 实现细节与要点

### 开始和可接受状态的标记

对于开始节点，我们采用特判标记法。有且仅有一个节点，也就是最开始的初始状态集合转换而得的节点，会被标记为 DFA 的开始节点。

对于结束节点，只要该状态集合中任意一个状态是 NFA 的可接受状态，则该状态集合转换得来的 DFA 状态也是一个可接受状态。

### 自动机数据的录入

我们通过多行的字符串，对自动机的初始数据进行录入。格式如下：

```
start:[start_state_id]
end:[end_state_id]
st1->st2:condition
...
```

- 对于开始状态和接受状态，我们通过以 `start:` 或者 `end:` 开始的行来定义。
- 对于状态转移，我们通过 `a->b:c` 来定义，其中 `c` 是转移所需的输入字符条件。
	- 对于多个转移条件，可以快捷的用逗号隔开：`a->b:x,y,z`
	- 如果需要定义空转移，可以忽略转移条件，详见下方例子。

> 注：值得一提的是，在从单行字符串提取各部分信息的过程中，我使用了 Python 提供的正则表达式工具（RegExp `re`）这一工具。具体使用到的正则表达式如下：`r"(?P<from_state>[a-zA-Z0-9_]+)\s*->\s*(?P<to_state>[a-zA-Z0-9_]+)(:(?P<condition>[a-zA-Z0-9,\\]+)){0,1}"`
> 
> 关于这个正则表达式的具体说明，参见附件 "正则表达式信息提取"

让我们看一个例子，如下的多行输入：

```
start:1
end:3
end:4
1->1:a,b
1->2:a
1->3:b
1->4
2->4:a
3->4:b
4->4:a,b
```

将会产生如下图所示的 NFA：

![NFA Definition Example](https://github.com/user-attachments/assets/fbff5335-b316-4c42-8033-472a7481681b)


注意到 `1->4` 是一个 $\varepsilon$ 转移路径，因为我们没有定义转移条件。同时，可接受状态的数量不受限制，我们可以定义多个结束状态。

此外，上述的 NFA 经过本程序化简之后，会得到下图的 DFA。

![Determinized Automata](https://github.com/user-attachments/assets/d796506c-a743-4c9a-a16c-b018ce4476c3)



### 状态集合的添加与维护

在程序内维护一组状态集合时，需要注意的点之一就是对于集合唯一性的确认。在储存集合时，我们需要保证数据结构具有以下特性：

- 节点唯一：集合内的所有节点不得重复。
- 集合同一性：如果两个集合内的所有节点都相同，两个集合也必须是相同的关系。

如果不满足上述条件，可能导致某些相同的状态（比如包含的节点相同，但是顺序不同）被重新认定为不同的状态。具体到程序实现上来说，我们就不宜继续采用常见的顺序储存结构，如 `List`，而应该选择其他更合适的数据结构。

在本程序中，我们**主要通过 `frozenset` 来储存状态集合**。

### 自动机的可视化

在可视化方面，我们基于 Graphviz 这一开源项目进行实现。总体而言，我们只需要根据一定的规则，将 NFA 或者 DFA 转换成 GraphViz 中的 Directed Graph （有向图）即可。

于此同时，我们还定义了自己的一套风格化标准，用于指定转换后，GraphViz 输出图案的各种风格设置，比如 开始状态的形状，可接受状态的形状等等。简要代码如下：

```python
@dataclass
class FADiGraphStyle[LabelType, CharType]:
    """
    A util data class used to defined the styles of the generated graphviz
    when using FADiGraph.

    # Refs:

    - [Node Shapes In GraphViz](https://graphviz.org/doc/info/shapes.html)
    """

    epsilon_edge_style: str = EPSILON_EDGE_STYLE
    start_node_shape: NodeShapeLiteral = START_NODE_SHAPE
    end_node_shape: NodeShapeLiteral = END_NODE_SHAPE
    start_and_end_node_shape: NodeShapeLiteral = START_AND_END_NODE_SHAPE
    normal_node_shape: NodeShapeLiteral = NORMAL_NODE_SHAPE
    create_start_pointers: bool = True
    """
    Create a arrow pointers to the start state.
    """

    get_node_label: Callable[[str, FANode[LabelType, CharType]], str] | None = None
    """
    Callback Pattern:
    
    - Parameter: (node_id, node_instance)
    - Returns: str
    """

    get_edge_label: Callable[[tuple[CharType | None, str]], str] | None = None
    """
    Callback Pattern:
    
    - Parameters: (pointers)
    - Returns: str
    """
```

在可视化过程中，我们可以传入不同的 `FADiGraphStyle` 实例，实现各种不同的风格，或者可以直接使用我们预定义好的自动机风格实例常量： `AutomataStandardStyle`

此外，注意到我们还可以提供一个函数，用于决定每一个自动机状态，应该以什么名称被显示在最终的图表上（默认根据 `node.label`，也就是节点的 `label` 成员的值，自动决定该节点的名称）。

## 程序代码实现

### 程序演示

我们可以通过修改 `nfa_to_dfa.py` 中的 `_test_case` 变量，来修改程序执行的样例。下面我们将通过一个样例展示本程序的运行过程和结果。

```python
# Test cases
_test_case = """
start:1
end:4
end:3
1->1:a,b
1->2:a
1->3:b
2->4:a
3->4:b
4->4:a,b
""".split(
    "\n"
)
```

上方测试样例所生成的 NFA：

![Original NFA](https://github.com/user-attachments/assets/c0dce1d1-557a-43cd-9cb3-8a25d5fde9af)

上方 NFA 转换而来的 DFA：

![Determinized DFA](https://github.com/user-attachments/assets/7d31b218-286f-4f36-8339-24878323af17)


### 完整代码

如果您想阅读本程序的代码，可以直接在 GitHub 上进行查阅：

- [本程序入口代码 nfa_to_dfa.py](https://github.com/Oya-Learning-Notes/Compilers/blob/main/code/py_impl/exp/2_fa/nfa_to_dfa.py)
- [本程序核心类代码 automata.fa.py](https://github.com/Oya-Learning-Notes/Compilers/blob/main/code/py_impl/packages/automata/fa.py)
- [Automata Graphviz可视化封装 automata.visualize.py](https://github.com/Oya-Learning-Notes/Compilers/blob/main/code/py_impl/packages/automata/visualize.py)

> 访问 GitHub 可能需要特殊的网络环境，故本实验报告将在最后附上上述文件的代码以供查阅。

### 在本地运行

本程序实际上是基于我正在尝试编写的一系列编译原理相关程序的Package之上的程序，故如果想要在本地运行此程序，您可能需要完整克隆 [这个项目](https://github.com/Oya-Learning-Notes/Compilers/tree/main/code/py_impl)，并根据 [本项目的安装文档](https://github.com/Oya-Learning-Notes/Compilers/blob/main/code/py_impl/doc/install.md) 正确的配置环境。

当完成上述步骤后，您便可以通过下方指令运行本程序：

```shell
cd ./exp/2_fa
python nfa_to_dfa.py
```

当然，您也可以根据上方提到的，修改 `_test_case` 变量的值，来测试不同的样例。

-----

附件：


# 正则表达式信息提取


```regex
r"(?P<from_state>[a-zA-Z0-9_]+)\s*->\s*(?P<to_state>[a-zA-Z0-9_]+)(:(?P<condition>[a-zA-Z0-9,\\]+)){0,1}"
```

#### Breakdown of the Pattern

1. **`(?P<from_state>[a-zA-Z0-9_]+)`**  
   - **Explanation**: This part captures the `from_state`, or the initial state in the transition.
   - **Pattern Details**: 
     - `(?P<from_state> ...)` defines a named capture group called `from_state`.
     - `[a-zA-Z0-9_]+` matches one or more alphanumeric characters or underscores (`_`), allowing variable names or identifiers.

2. **`\s*->\s*`**  
   - **Explanation**: This part matches the arrow (`->`) between the states, which represents the transition.
   - **Pattern Details**:
     - `\s*` matches any whitespace (spaces, tabs, etc.) zero or more times, allowing flexible spacing around the arrow.
     - `->` matches the literal arrow characters.

3. **`(?P<to_state>[a-zA-Z0-9_]+)`**  
   - **Explanation**: This part captures the `to_state`, or the destination state in the transition.
   - **Pattern Details**:
     - `(?P<to_state> ...)` defines a named capture group called `to_state`.
     - `[a-zA-Z0-9_]+` matches one or more alphanumeric characters or underscores.

4. **`(: (?P<condition>[a-zA-Z0-9,\\]+)) {0,1}`**  
   - **Explanation**: This part optionally captures a condition associated with the transition.
   - **Pattern Details**:
     - `(: ...) {0,1}` matches the entire group `(: ...)`, zero or one time, making it optional.
     - `:` matches the literal colon character.
     - `(?P<condition> ...)` defines a named capture group called `condition`.
     - `[a-zA-Z0-9,\\]+` matches one or more alphanumeric characters, commas, or backslashes (`\`). This allows for multiple conditions separated by commas or with escaped characters.

#### Summary
This regex is used to parse a transition syntax such as `stateA -> stateB:condition1,condition2`. It captures:
- **`from_state`**: The starting state of the transition.
- **`to_state`**: The destination state of the transition.
- **`condition`** (optional): Additional conditions that may apply to the transition, which can include multiple conditions separated by commas.

#### Examples

1. **Example 1**: `"idle -> running:condition1"`
   - **Captures**:
     - `from_state`: `idle`
     - `to_state`: `running`
     - `condition`: `condition1`

2. **Example 2**: `"idle -> paused"`
   - **Captures**:
     - `from_state`: `idle`
     - `to_state`: `paused`
     - `condition`: Not captured (optional)

3. **Example 3**: `"stateA -> stateB:conditionA,conditionB"`
   - **Captures**:
     - `from_state`: `stateA`
     - `to_state`: `stateB`
     - `condition`: `conditionA,conditionB`

# nfa_to_dfa.py

```python
from collections.abc import Sequence
from typing import Literal, cast
from dataclasses import replace
import re

from loguru import logger

from automata import FA, FANode
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
        if node_id not in nodes_dict:
            nodes_dict[node_id] = FANode(nid=node_id, label=node_id)
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

    return FA(nodes_dict=nodes_dict)


_test_case = """
start:1
end:4
end:3
1->1:a,b
1->2:a
1->3:b
2->4:a
3->4:b
4->4:a,b
""".split(
    "\n"
)


def main():
    fa = create_fa_node_from_lines(_test_case)

    def get_node_label(nid: str, node: FA):
        return nid

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


if __name__ == "__main__":
    main()
```

# automata.fa.py


```python
from typing import TypeAlias, Set, Collection
from loguru import logger
import graphviz as gv
from copy import copy

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
        hashval = hash(tuple(pointers_set))
        if consider_is_end:
            hashval = hash(tuple([hashval, self.is_end]))
        return hashval


class FA[LabelType, CharType]:
    # store nodes in this automaton
    # pattern: nodes[<node_id>] = node_instance
    nodes: dict[str, FANode[LabelType, CharType]]

    # store current set of active states.
    # empty set should represent this machine has stuck.
    _current_states: frozenset[FANode[LabelType, CharType]]

    _max_match: int
    max_match: int

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

        self.nodes = nodes_dict
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
            epsilon_nodes = self.convert_id_set_to_node_set(found_epsilons)

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
            new_states.update(self.convert_id_set_to_node_set(new_id))

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

    def convert_id_set_to_node_set(self, id_set: set[str]):
        """
        Convert a list of nid to the FANode object

        Notice: This method will deduplicated the nid before converting
        """
        return [self.nodes[nid] for nid in id_set]

    def to_dfa(
        self, new_fa: bool = True, minimize: bool = True
    ) -> "FA[set[LabelType],CharType]":
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

        # def _get_states_by_set_of_nodes(states_set: set[FANode[LabelType, CharType]]):
        #     nonlocal discovered_states_set
        #     """
        #     Get a states set, create one if not exists
        #     """
        #     if states_set not in discovered_states_set:
        #         discovered_states_set.add(states_set)

        #     return states_set

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

        nodes_dict_for_nfa: dict[str, FANode[set[LabelType], CharType]] = {}
        states_set_to_node_map: dict[
            frozenset[FANode[LabelType, CharType]], FANode[set[LabelType], CharType]
        ] = {}

        # create dfa nodes
        for st in discovered_states_set:
            dfa_node = self._create_set_state(st)
            nodes_dict_for_nfa[dfa_node.nid] = dfa_node
            states_set_to_node_map[frozenset(st)] = dfa_node

            if st == start_states_set:
                dfa_node.is_start = True

        # create pointers
        for start_st, end_st, input_char in states_sets_points_to:
            start_node = states_set_to_node_map[start_st]
            end_node = states_set_to_node_map[end_st]
            start_node.point_to(char=input_char, node_id=end_node.nid)

        return FA(nodes_dict=nodes_dict_for_nfa)
        # # create nodes dict for fa init
        # nodes_dict_for_fa_init: dict[str, FANode[list[LabelType], CharType]] = {}

        # for dict_item in dfa_states_dict.items():
        #     node = dict_item[1]
        #     nodes_dict_for_fa_init[node.nid] = node

        # if new_fa:
        #     new_fa_ins = FA(nodes_dict=nodes_dict_for_fa_init)
        #     if minimize:
        #         new_fa_ins.minimize(new_fa=False)
        #     return new_fa_ins
        # else:
        #     self.nodes = nodes_dict_for_fa_init  # type:ignore
        #     if minimize:
        #         self.minimize(new_fa=False)
        #     return self  # type: ignore

    def minimize(
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
            return copy(self).minimize(new_fa=False)

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
        self.remove_unref_node()
        return self

    def minimize_1(
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
            return copy(self).minimize(new_fa=False)

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
        self.remove_unref_node()
        return self

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
            pointer_to_be_replaced: list[tuple[CharType, str]] = []
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

    def remove_unref_node(self) -> None:
        """
        Remove node from this FA if no pointers points to it.
        """
        ref_set: set[str] = set()

        ref_set.update([st.nid for st in self.get_start_states(find_epsilons=True)])

        for node in self.nodes.values():
            for pointer in node.pointers:
                ref_set.add(pointer[1])

        # get refed set
        ref_node_set = self.convert_id_set_to_node_set(ref_set)

        # convert set to dict
        ref_dict: dict[str, FANode] = dict()
        for n in ref_node_set:
            ref_dict[n.nid] = n

        self.nodes = ref_dict

    @staticmethod
    def _create_set_state(
        state_set: frozenset[FANode[LabelType, CharType]]
    ) -> FANode[set[LabelType], CharType]:
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

        new_label = set([st.label for st in state_set if st.label is not None])

        # create new node
        new_state_node = FANode[set[LabelType], CharType](
            nid=new_nid,
            is_end=is_end_state,
            label=new_label,
        )

        return new_state_node
```

# automata.visualize.py

```python
from typing import Callable, Any, Literal
from dataclasses import dataclass, replace
from functools import wraps, partialmethod
import graphviz as gv

from .fa import FA, FANode

__all__ = ["FADiGraph"]

NodeShapeLiteral = Literal[
    "box",
    "polygon",
    "ellipse",
    "oval",
    "circle",
    "point",
    "egg",
    "triangle",
    "plaintext",
    "plain",
    "diamond",
    "trapezium",
    "parallelogram",
    "house",
    "pentagon",
    "hexagon",
    "septagon",
    "octagon",
    "doublecircle",
    "doubleoctagon",
    "tripleoctagon",
    "invtriangle",
    "invtrapezium",
    "invhouse",
    "Mdiamond",
    "Msquare",
    "Mcircle",
    "rect",
    "rectangle",
    "square",
    "star",
    "none",
    "underline",
    "cylinder",
    "note",
    "tab",
    "folder",
    "box3d",
    "component",
]

EPSILON_EDGE_STYLE = "solid"

START_NODE_SHAPE: NodeShapeLiteral = "diamond"
END_NODE_SHAPE: NodeShapeLiteral = "doubleoctagon"
START_AND_END_NODE_SHAPE: NodeShapeLiteral = "tripleoctagon"
NORMAL_NODE_SHAPE: NodeShapeLiteral = "box"


from typing import Literal


@dataclass
class FADiGraphStyle[LabelType, CharType]:
    """
    A util data class used to defined the styles of the generated graphviz
    when using FADiGraph.

    # Refs:

    - [Node Shapes In GraphViz](https://graphviz.org/doc/info/shapes.html)
    """

    epsilon_edge_style: str = EPSILON_EDGE_STYLE
    start_node_shape: NodeShapeLiteral = START_NODE_SHAPE
    end_node_shape: NodeShapeLiteral = END_NODE_SHAPE
    start_and_end_node_shape: NodeShapeLiteral = START_AND_END_NODE_SHAPE
    normal_node_shape: NodeShapeLiteral = NORMAL_NODE_SHAPE
    create_start_pointers: bool = True
    """
    Create a arrow pointers to the start state.
    """

    get_node_label: Callable[[str, FANode[LabelType, CharType]], str] | None = None
    """
    Callback Pattern:
    
    - Parameter: (node_id, node_instance)
    - Returns: str
    """

    get_edge_label: Callable[[tuple[CharType | None, str]], str] | None = None
    """
    Callback Pattern:
    
    - Parameters: (pointers)
    - Returns: str
    """


AutomataStandardStyle = FADiGraphStyle[Any, Any](
    start_node_shape="circle",
    normal_node_shape="circle",
    end_node_shape="doublecircle",
    start_and_end_node_shape="doublecircle",
)


class FADiGraph[LabelType, CharType]:

    def __init__(
        self,
        fa: FA,
        name: str | None = None,
        style: FADiGraphStyle[LabelType, CharType] = AutomataStandardStyle,
        # get_node_label: Callable[[str, FANode[LabelType, CharType]], str] | None = None,
        # get_edge_label: Callable[[tuple[object, str]], str] | None = None,
    ):
        # init name
        self.name = name or "Automata Graph"

        # init styles
        style.get_node_label = style.get_node_label or self.get_node_label_default
        style.get_edge_label = style.get_edge_label or self.get_edge_label_default

        # store styles
        self.style = style

        # init fa
        self._graphviz_obj: gv.Digraph
        if fa is not None:
            self.from_fa(fa)

    @staticmethod
    def get_node_label_default(nid: str, node: FANode[LabelType, CharType]) -> str:
        """
        Default function used to generate the label of a node int .dot file.
        """
        ret_str = f"{nid}"
        if node.label is not None:
            ret_str += f" {node.label}"

        return ret_str

    @staticmethod
    def get_edge_label_default(edge_info: tuple[object, str]):
        ret_str = f" {edge_info[0]} "
        if edge_info[0] is None:
            ret_str = ""
        return ret_str

    def from_fa(self, fa: FA) -> "FADiGraph":
        """
        Generate a graphviz object from an fa.FA object.

        Raise RuntimeError if there is already an object.
        """

        # initialize object
        self._graphviz_obj = gv.Digraph(self.name)
        self._graphviz_obj.attr("graph", rankdir='LR')

        # add node to digraph
        for nid, node in fa.nodes.items():

            # determine node shape
            node_shape = None
            if node.is_start and node.is_end:
                node_shape = self.style.start_and_end_node_shape
            elif node.is_start:
                node_shape = self.style.start_node_shape

                # add arrow points to start node if configured
                if self.style.create_start_pointers:
                    # create invisible node
                    self._graphviz_obj.node(
                        f"start_pointers_{nid}", label="", shape="plaintext"
                    )
                    # add arrow from invisible node to the start node
                    self._graphviz_obj.edge(
                        f"start_pointers_{nid}",
                        nid,
                    )

            elif node.is_end:
                node_shape = self.style.end_node_shape
            else:
                node_shape = self.style.normal_node_shape

            assert self.style.get_node_label is not None
            self._graphviz_obj.node(
                str(nid), label=self.style.get_node_label(nid, node), shape=node_shape
            )

        # add edges
        for nid, node in fa.nodes.items():
            for next_input, next_node_id in node.pointers:
                edge_style = None
                if next_input is None:
                    edge_style = self.style.epsilon_edge_style

                assert self.style.get_edge_label is not None
                self._graphviz_obj.edge(
                    str(nid),
                    str(next_node_id),
                    label=self.style.get_edge_label((next_input, next_node_id)),
                    style=edge_style,
                )

        return self

    def get_graph(self) -> gv.Digraph:
        if self._graphviz_obj is None:
            raise RuntimeError(
                "FADiGraph.get_graph() called while self._graphviz_obj is None. Make sure you already call self.from_fa() before."
            )
        return self._graphviz_obj

    def render(self):
        self._graphviz_obj.render(
            filename=f"{self.name}",
            directory="./graphviz",
            view=True,
        )
```