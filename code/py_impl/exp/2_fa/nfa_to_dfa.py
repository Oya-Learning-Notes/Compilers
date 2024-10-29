from collections.abc import Sequence
import re

from loguru import logger

from automata import FA, FANode

# Regex pattern to parse state transition strings in format: "state1 -> state2:condition"
# Groups: from_state (source state), to_state (destination state), condition (optional transition condition)
string_state_format_regex = re.compile(
    r"(?P<from_state>[a-zA-Z0-9_]+)\s*->\s*(?P<to_state>[a-zA-Z0-9_]+)(:(?P<condition>[a-zA-Z0-9,\\]+)){0,1}"
)


class AutomataStringParseError:
    pass


def create_fa_node_from_lines(lines: Sequence[str]):

    # dict to store the node created during the process
    nodes_dict: dict[str, FANode[str, str]] = {}

    # iterate every line
    for l in lines:

        l = l.strip()

        # skip empty line
        if l == "":
            continue

        # try match from the start
        match = string_state_format_regex.match(l)
        if match is None:
            raise RuntimeError(f"Invalid state format: {l}")

        from_state = match.group("from_state")
        to_state = match.group("to_state")
        condition = match.group("condition")

        if from_state not in nodes_dict:
            nodes_dict[from_state] = FANode[str, str](nid=from_state, label=from_state)

        if to_state not in nodes_dict:
            nodes_dict[to_state] = FANode[str, str](nid=to_state, label=to_state)

        nodes_dict[from_state].add_pointer(condition, to_state)

    return FA(nodes_dict=nodes_dict)


def main():
    pass


if __name__ == "__main__":
    pass
