from typing import NewType, Union
from loguru import logger
import graphviz as gv

from .utils import get_node_id

type FANodeID = int | str
type FAChar = str | None


class FANode[LabelType]:
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

    def __repr__(self) -> str:
        str = f'<FANode id:{self.nid} Start:{self.is_start} Fin:{self.is_end}>\n'
        for p in self.pointers:
            str += f'<Pointer input:{p[0]} nextId:{p[1]}/>\n'
        str += '</FANode>'

        return str

    def try_move(self, next_input: FAChar) -> list[FANodeID] | None:
        """
        Return a list of FANodeID if we successfully find the next node to move on. Otherwise, return `None`.
        """
        move_candidate: list[FANodeID] = []  # id list of the movable node next.

        # loop through all pointers to check which node could we move next.
        for pointer in self.pointers:
            if pointer[0] == next_input:
                move_candidate.append(pointer[1])

        if len(move_candidate) == 0:
            return None

        return move_candidate

    def is_dfa(self) -> bool:
        """
        If this node could be a DFA node.
        """
        char_list: list[FAChar] = []
        for char, node_id in self.pointers:
            char_list.append(char)

        char_set = set(char_list)

        if len(char_set) < len(char_list):
            return False

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


class FA[LabelType]:
    nodes: dict[FANodeID, FANode[LabelType]]
    _current_states: list[FANode]
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

    def get_start_states(self, find_epsilons: bool = False) -> list[FANode]:
        if not find_epsilons:
            return [n for (nid, n) in self.nodes.items() if n.is_start]
        return self.find_epsilons([n for (nid, n) in self.nodes.items() if n.is_start])

    def get_end_states(self) -> list[FANode]:
        return self.find_epsilons([n for nid, n in self.nodes.items() if n.is_end])

    def init_state(self) -> 'FA':
        """
        Set the initial state of this FA.

        Return this FA itself.
        """
        self._current_states = self.get_start_states(find_epsilons=True)
        self.max_match = 0
        return self

    def find_epsilons(self, input_states: list[FANode]) -> list[FANode]:
        # iterate all nodes to find epsilon moves
        it_nodes = input_states
        while True:
            found_epsilons: list[FANodeID] = []

            # all directly linked epsilon nodes with it_nodes
            for new_st in it_nodes:
                new_id = new_st.try_move(None)
                if new_id is None:
                    continue
                found_epsilons.extend(new_id)

            # break if not found any epsilon nodes
            if len(found_epsilons) == 0:
                break

            # convert id to nodes instance
            epsilon_nodes: list[FANode] = self.convert_id_list_to_node_list(
                found_epsilons
            )

            # we still need to check if there is any epsilon moves in the newly found nodes
            it_nodes = epsilon_nodes

            before_count: int = len(input_states)
            # also the found node should be added to new states
            input_states.extend(epsilon_nodes)

            # if final states count not increase, break
            after_count: int = len(input_states)
            if after_count == before_count:
                break

        return input_states

    def move_next(self, next_input: FAChar) -> bool:
        """
        Try to mutate the state of this FA on the input.

        Params:

        - `input` Should be a single character.

        Returns true if the move is valid
        """

        # no active state, FA stucked.
        if len(self._current_states) == 0:
            return False

        # init a list to store new state
        new_states: list[FANode] = []

        # find new states on input
        for cur_state in self._current_states:
            new_id = cur_state.try_move(next_input)
            if new_id is None:
                continue
            new_states.extend(self.convert_id_list_to_node_list(new_id))

        # if no new states, failed to move
        if len(new_states) == 0:
            self._current_states = []
            return False

        # find epsilon states of new states
        epsilon_nodes = self.find_epsilons(new_states)

        # also the found node should be added to new states
        new_states.extend(epsilon_nodes)

        # update state and return True
        self._current_states = new_states
        self.max_match += 1
        return True

    def move_next_str(self, input_sequence: list[FAChar]) -> bool:
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

    def test_str(self, input_str: list[FAChar]) -> bool:
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

    def convert_id_list_to_node_list(self, id_list: list[FANodeID]):
        return [self.nodes[nid] for nid in set(id_list)]
