from loguru import logger
from cfg import CFGSystem, Terminal, NonTerminal, Production, Derivation
from pprint import pformat

# Define NonTerminals
S = NonTerminal("S")
A = NonTerminal("A")
B = NonTerminal("B")

# Define Terminals
a = Terminal("a")
b = Terminal("b")
c = Terminal("c")

# Define productions with left recursion
productions_direct_left_recursive = [
    Production(source=S, target=Derivation([S, a])),  # S → S a
    Production(source=S, target=Derivation([b])),  # S → b
    Production(source=A, target=Derivation([A, b])),  # A → A b
    Production(source=A, target=Derivation([c])),  # A → c
    Production(source=B, target=Derivation([B, c])),  # B → B c
    Production(source=B, target=Derivation([a])),  # B → a
]

productions_indirect_left_recursive = [
    Production(source=S, target=Derivation([A, b])),  # S → A b
    Production(source=A, target=Derivation([B, c])),  # A → B c
    Production(source=B, target=Derivation([a])),  # B → a
    Production(
        source=B, target=Derivation([S, a])
    ),  # B → S a (indirect left recursion starts here)
]

# A -> Bc
# S -> Ab
# S -> Bcb
# B -> a | Sa
# B -> a | Bcba

cfg_direct_left_recursive = CFGSystem(
    entry=S, production_list=productions_direct_left_recursive
)

cfg_indirect_left_recursive = CFGSystem(
    entry=S, production_list=productions_indirect_left_recursive
)

# Test cases definition end.
# --------------------------------------------------------------


def test_direct_left_recursion():
    cfg_1 = cfg_direct_left_recursive.eliminate_left_recursive()
    logger.info("\n" + pformat(cfg_1.production_dict))

    cfg_2 = cfg_indirect_left_recursive.eliminate_left_recursive()
    logger.info("\n" + pformat(cfg_2.production_dict))


if __name__ == "__main__":
    test_direct_left_recursion()
