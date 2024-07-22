# from typing import NewType, Union
from loguru import logger
import graphviz as gv
from copy import copy

from .utils import get_node_id

# Notice that FANodeID and FAChar must be hashable type.
# Since the hash method is used when checking if two nodes have identical transition moves. That's to check if two
# pointers collection has the same hash value.
type FANodeID = int | str


class FANode[LabelType, FAChar]:
    nid: FANodeID
    is_start: bool
    is_end: bool
    pointers: list[tuple[FAChar, FANodeID]]
    label: LabelType | None  # label of this node

    def __init__(self, is_start=False, is_end=False, nid=None, label: LabelType | None = None) -> None:
        if nid is None:
            nid = get_node_id()

        self.nid = nid
        self.is_start = is_start
        self.is_end = is_end
        self.pointers = []
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
        repr_str = f'<FANode id:{self.nid} Start:{self.is_start} Fin:{self.is_end}>\n'
        for p in self.pointers:
            repr_str += f'<Pointer input:{p[0]} nextId:{p[1]}/>\n'
        repr_str += '</FANode>'

        return repr_str

    def try_move(self, next_input: FAChar) -> set[FANodeID] | None:
        """
        Return a list of FANodeID if we successfully find the next node to move on. Otherwise, return `None`.
        """
        move_candidate: set[FANodeID[LabelType]] = set()  # id list of the movable node next.

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
        char_list: list[FAChar] = []

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

    def point_to(self, char: FAChar, node_id: FANodeID) -> bool:
        """
        Add a pointer to this Node if not exists.

        Returns `False` if already exists that pointer, else return `True`.
        """
        # construct new pointer
        pointer_tuple: tuple[FAChar, FANodeID] = (char, node_id)

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
        pointers_set = set(self.pointers)  # convert pointers list to set. This will ignore order & remove duplicated
        hashval = hash(tuple(pointers_set))
        if consider_is_end:
            hashval = hash(tuple([hashval, self.is_end]))
        return hashval


class FA[LabelType, CharType]:
    # store nodes in this automaton
    # pattern: nodes[<node_id>] = node_instance
    nodes: dict[FANodeID, FANode[LabelType, CharType]]
    _current_states: set[FANode[LabelType, CharType]]
    _max_match: int
    max_match: int

    def __init__(self, nodes_dict: dict[FANodeID, FANode] | list[FANode]) -> None:
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
        repr_str = '<FA>\n'
        for node in self.nodes.values():
            repr_str += str(node)
            repr_str += '\n'

        repr_str += '</FA>'
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

    def get_start_states(self, find_epsilons: bool = False) -> set[FANode[LabelType, CharType]]:
        """
        Get a set of start states of this automaton.

        Params:

        - ``find_epsilons`` If `true`, will return the epsilon state set of the start states.
        """
        if not find_epsilons:
            return set(n for (nid, n) in self.nodes.items() if n.is_start)
        return self.find_epsilons(set(n for (nid, n) in self.nodes.items() if n.is_start))

    def get_current_state(self) -> set[FANode[LabelType, CharType]]:
        return self._current_states

    def get_end_states(self) -> set[FANode[LabelType, CharType]]:
        return self.find_epsilons(set(n for nid, n in self.nodes.items() if n.is_end))

    def init_state(self) -> 'FA[LabelType, CharType]':
        """
        Set the initial state of this FA.

        Return this FA itself.
        """
        self._current_states = self.get_start_states(find_epsilons=True)
        self._max_match = 0
        self.max_match = 0
        return self

    def find_epsilons(self, input_states: set[FANode[LabelType, CharType]]) -> set[FANode[LabelType, CharType]]:
        """
        Find the epsilon closure of the input_states
        """
        # iterate all nodes to find epsilon moves
        it_nodes = input_states
        while True:
            found_epsilons: set[FANodeID] = set()

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
            epsilon_nodes = self.convert_id_set_to_node_set(
                found_epsilons
            )

            # we still need to check if there is any epsilon moves in the newly found nodes
            it_nodes = epsilon_nodes

            before_count: int = len(input_states)
            # also the found node should be added to new states
            input_states.update(epsilon_nodes)

            # if final states count not increase, break
            after_count: int = len(input_states)
            if after_count == before_count:
                break

        return input_states

    @staticmethod
    def get_all_possible_input_on_state(state: set[FANode[LabelType, CharType]]) -> set[CharType]:
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
        Try to move this FA to next states with given input

        Return `True` if this is a valid move, else return `False`.
        """
        next_state = self._move_next(prev_states=self._current_states, next_input=next_input)
        if next_state is None:
            return False

        # valid move, update state
        self._max_match += 1
        self._current_states = next_state
        if self.is_accepted():
            self.max_match = self._max_match
        return True

    def _move_next(
            self,
            prev_states: set[FANode[LabelType, CharType]],
            next_input: CharType) -> set[FANode[LabelType, CharType]] | None:
        """
        Try to find the next states with given previous state in this FA.

        Params:

        - `input` Should be a single character.

        Return set of the new states if move valid, else return None
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
        return new_states

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
        """
        for state in self._current_states:
            if state.is_end:
                return True

        return False

    def convert_id_set_to_node_set(self, id_set: set[FANodeID]):
        """
        Convert a list of nid to the FANode object

        Notice: This method will deduplicated the nid before converting
        """
        return [self.nodes[nid] for nid in id_set]

    def to_dfa(self, new_fa: bool = True, minimize: bool = True) -> 'FA[LabelType,CharType]':
        """
        Try to convert current FA to DFA.

        Params:

        - `new_fa` If true, return a newly created FA instance instead of mutating this instance.
        """
        # store sets of states for DFA, init it with start state
        # key should be the set of states, value should be the FANode object for the corresponding DFA states
        dfa_states_dict: dict[tuple[FANode[LabelType, CharType], ...], FANode[LabelType, CharType]] = {}

        # record if a dfa state has been visited
        visited_dict: dict[FANode, bool] = {}

        # create start state node
        start_state = self.get_start_states(find_epsilons=True)
        start_state_node = self._create_set_state(start_state)
        start_state_node.is_start = True
        # add to dfa_states_dict
        dfa_states_dict[tuple(start_state)] = start_state_node

        # process list
        process_list: list[set[FANode[LabelType, CharType]]] = [start_state]

        # deal with process list until it's empty
        while len(process_list) > 0:
            # deal with last element in proc list
            prev_state = process_list.pop()

            # if prev_state in states dict, retrieve it, else create it
            prev_state_node = dfa_states_dict.get(tuple(prev_state))
            if prev_state_node is None:
                prev_state_node = self._create_set_state(prev_state)
                dfa_states_dict[tuple(prev_state)] = prev_state_node

            # if the retrieved state already in dfa_states_dict, skip
            if visited_dict.get(prev_state_node):
                continue
            visited_dict[prev_state_node] = True

            # find all possible input
            all_possible_input = self.get_all_possible_input_on_state(prev_state)

            for input_char in all_possible_input:
                # for each input, get the next state
                next_state = self._move_next(prev_state, input_char)

                # if next_state node exists then retrieve it, else create new one
                next_state_node = dfa_states_dict.get(tuple(next_state))
                if next_state_node is None:
                    next_state_node = self._create_set_state(next_state)
                    dfa_states_dict[tuple(next_state)] = next_state_node

                # add pointers for prev state
                prev_state_node.point_to(input_char, next_state_node.nid)

                # add discovered new states to process list
                process_list.append(next_state)

        # create nodes dict for fa init
        nodes_dict_for_fa_init: dict[FANodeID, FANode] = {}
        for dict_item in dfa_states_dict.items():
            node = dict_item[1]
            nodes_dict_for_fa_init[node.nid] = node

        if new_fa:
            new_fa = FA(nodes_dict=nodes_dict_for_fa_init)
            if minimize:
                new_fa.minimize(new_fa=False)
            return new_fa
        else:
            self.nodes = nodes_dict_for_fa_init
            if minimize:
                self.minimize(new_fa=False)
            return self

    def minimize(self, check_dfa: bool = False, new_fa: bool = False) -> 'FA[LabelType, CharType]':
        """
        Try to minimize this FA.

        Params:

        - `check_dfa` If true, check if this FA is DFA before perform minimize
        - `new_fa` If true, return a newly created FA

        Notice that only DFA could be simplified.
        """

        if check_dfa and (not self.is_dfa()):
            raise RuntimeError('Only Determined Finite Automaton should be minimized, you are trying to minimize a NFA')

        if new_fa:
            return copy(self).minimize(new_fa=False)

        # store the node with certain transition hash
        transition_hash_dict: dict[int, set[FANode]] = {}

        # group nodes with same transition hash
        for node in self.nodes.values():
            transition_hash = node.hash_of_pointers(consider_is_end=True)
            nodes_set_for_this_hash = transition_hash_dict.setdefault(transition_hash, set())
            nodes_set_for_this_hash.add(node)

        # merge those with same hash
        for nodes_set_with_same_hash in transition_hash_dict.values():
            self.merge_nodes(nodes_set_with_same_hash)

        # remove unref node
        self.remove_unref_node()
        return self

    def merge_nodes(self, nodes_set: set[FANode]) -> None:
        if len(nodes_set) < 2:
            return

        # generate standard node
        std_node = None
        for i in nodes_set:
            std_node = i
            if i.is_end:
                std_node.is_end = True
            if i.is_start:
                std_node.is_start = True

        for node in self.nodes.values():
            # set standard node
            if std_node is None:
                std_node = node

            # replace all pointers that point to nodes in this set to std node
            pointer_to_be_replaced: list[tuple[CharType, FANodeID]] = []
            for pointer in node.pointers:
                # get the node that this pointer points to
                point_to_nid = pointer[1]
                point_to_node = self.nodes[point_to_nid]

                # if matched, add to replace
                if point_to_node in nodes_set:
                    pointer_to_be_replaced.append(pointer)

            # replace pointer to std node (add new pointer points to std_node, remove old pointer)
            for p in pointer_to_be_replaced:
                node.pointers.append(tuple[CharType, FANodeID]([p[0], std_node.nid]))
                node.pointers.remove(p)

    def remove_unref_node(self) -> None:
        """
        Remove node from this FA if no pointers points to it.
        """
        ref_set: set[FANodeID] = set()

        ref_set.update([st.nid for st in self.get_start_states(find_epsilons=True)])

        for node in self.nodes.values():
            for pointer in node.pointers:
                ref_set.add(pointer[1])

        # get refed set
        ref_node_set = self.convert_id_set_to_node_set(ref_set)

        # convert set to dict
        ref_dict: dict[FANodeID, FANode] = dict()
        for n in ref_node_set:
            ref_dict[n.nid] = n

        self.nodes = ref_dict

    @staticmethod
    def _create_set_state(state_set: set[FANode[LabelType, CharType]]) -> FANode[list[LabelType], CharType]:
        """
        Create a new state from a set of states. Usually used when converting NFA to DFA
        """
        # check if it's end state
        is_end_state: bool = False
        for st in state_set:
            if st.is_end:
                is_end_state = True
                break

        # cat nid of old nodes as the new nid
        new_nid: str = ','.join(str(st.nid) for st in state_set)
        new_nid = '{' + new_nid + '}'
        new_label = [st.label for st in state_set]

        # create new node
        new_state_node = FANode(
            nid=new_nid,
            is_end=is_end_state,
            label=new_label,
        )

        return new_state_node
