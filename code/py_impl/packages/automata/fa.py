# from typing import NewType, Union
from loguru import logger
import graphviz as gv

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

    def __init__(self, is_start=False, is_end=False, nid=None, label=None) -> None:
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

    def hash_of_pointers(self) -> int:
        """
        Return logical hash values of a group of pointers.

        Notice:

        - This method will ignore the order of the pointers in the list.
        - This method will ignore the duplicated pointer.

        Nodes with same pointers hash value should be able to merge when minimizing DFA.
        """
        pointers_set = set(self.pointers)  # convert pointers list to set. This will ignore order & remove duplicated
        return hash(pointers_set)


class FA[LabelType, CharType]:
    type FANodeType = FANode[LabelType, CharType]

    nodes: dict[FANodeID, FANode[LabelType, CharType]]
    _current_states: set[FANode[LabelType, CharType]]
    max_match: int

    def __init__(self, nodes_dict: dict[FANodeID, FANode] | list[FANode]) -> None:
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

    def to_graphviz(self) -> gv.Digraph:
        pass
        # create a new graphviz directed graph object.

    def is_dfa(self):
        """
        Check if this Automaton is Determined Finite Automaton
        """
        for node in self.nodes.values():
            if not node.is_dfa():
                return False
        return True

    def get_start_states(self, find_epsilons: bool = False) -> set[FANode[LabelType, CharType]]:
        if not find_epsilons:
            return set(n for (nid, n) in self.nodes.items() if n.is_start)
        return self.find_epsilons(set(n for (nid, n) in self.nodes.items() if n.is_start))

    def get_current_state(self):
        return self._current_states

    def get_end_states(self) -> set[FANode]:
        return self.find_epsilons(set(n for nid, n in self.nodes.items() if n.is_end))

    def init_state(self) -> 'FA':
        """
        Set the initial state of this FA.

        Return this FA itself.
        """
        self._current_states = self.get_start_states(find_epsilons=True)
        self.max_match = 0
        return self

    def find_epsilons(self, input_states: set[FANode[LabelType, CharType]]) -> set[FANode[LabelType, CharType]]:
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
            epsilon_nodes = self.convert_id_list_to_node_list(
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

    def move_next(self, next_input: str) -> bool:
        """
        Try to move this FA to next states with given input

        Return `True` if this is a valid move, else return `False`.
        """
        next_state = self._move_next(prev_states=self._current_states, next_input=next_input)
        if next_state is None:
            return False

        # valid move, update state
        self.max_match += 1
        self._current_states = next_state
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
            new_states.update(self.convert_id_list_to_node_list(new_id))

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

    def convert_id_list_to_node_list(self, id_set: set[FANodeID]):
        """
        Convert a list of nid to the FANode object

        Notice: This method will deduplicated the nid before converting
        """
        return [self.nodes[nid] for nid in id_set]

    def to_dfa(self, new_fa: bool = True) -> 'FA[LabelType,CharType]':
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
            return FA(nodes_dict=nodes_dict_for_fa_init)
        else:
            self.nodes = nodes_dict_for_fa_init
            return self

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
