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
