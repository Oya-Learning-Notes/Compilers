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
