from collections.abc import Sequence

from automata import FA, FANode


def create_fa_node_from_lines(lines: Sequence[str]) -> FA:
    nodes_dict: dict[str, FANode[str, str]] = {}

    return FA(nodes_dict=nodes_dict)


def main():
    pass


if __name__ == "__main__":
    pass
