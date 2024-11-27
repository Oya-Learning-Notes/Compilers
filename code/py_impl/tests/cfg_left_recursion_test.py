from loguru import logger
from cfg import CFGSystem, Terminal, NonTerminal, Production, Derivation
from cfg import LL1CFGSystem, LL1CFGSystemError, SelectSetConflictError
from pprint import pformat

# Define NonTerminals
S = NonTerminal("S")
S_PI = NonTerminal("S'")
A = NonTerminal("A")
B = NonTerminal("B")

# Define Terminals
a = Terminal("a")
b = Terminal("b")
c = Terminal("c")
end = Terminal("$")

# Define productions with left recursion

# S' -> S
# S -> Sa | b | AB
# A -> Ab | c
# B -> Bc | a
productions_direct_left_recursive = [
    Production(source=S_PI, target=Derivation([S, end])),
    Production(source=S, target=Derivation([S, a])),  # S → S a
    Production(source=S, target=Derivation([b])),  # S → b
    Production(source=S, target=Derivation([A, B])),  # S → AB
    Production(source=A, target=Derivation([A, b])),  # A → A b
    Production(source=A, target=Derivation([c])),  # A → c
    Production(source=B, target=Derivation([B, c])),  # B → B c
    Production(source=B, target=Derivation([a])),  # B → a
]

# S -> Ab
# A -> Bc
# B ->a | Sa
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

# A -> Bc
# B -> a | Sa
# S -> Ab
# S -> Bc
# S -> ac | Sac

cfg_direct_left_recursive = CFGSystem(
    entry=S_PI, production_list=productions_direct_left_recursive
)

cfg_indirect_left_recursive = CFGSystem(
    entry=S, production_list=productions_indirect_left_recursive
)

# Test cases definition end.
# --------------------------------------------------------------


def test_direct_left_recursion():
    try:
        cfg_1_ll1 = LL1CFGSystem(
            entry=cfg_direct_left_recursive.entry,
            production_list=cfg_direct_left_recursive.production_list,
        )
    except LL1CFGSystemError as e:
        logger.error(e)
        pass

    try:
        cfg_2_ll1 = LL1CFGSystem(
            entry=cfg_indirect_left_recursive.entry,
            production_list=cfg_indirect_left_recursive.production_list,
        )
    except LL1CFGSystemError as e:
        logger.error(e)
        pass

    # --------------------------------------------------------------

    cfg_1 = cfg_direct_left_recursive.eliminate_left_recursive()
    logger.info("\n" + pformat(cfg_1.production_dict))
    logger.info("first set:\n" + pformat(cfg_1.first_sets))
    logger.info("follow set:\n" + pformat(cfg_1.follow_sets))
    try:
        cfg_1_ll1 = LL1CFGSystem(
            entry=cfg_1.entry, production_list=cfg_1.production_list
        )
        logger.info("select set\n" + pformat(cfg_1_ll1.select_sets))
    except SelectSetConflictError as e:
        logger.error(e)
        pass

    # --------------------------------------------------------------

    cfg_2 = cfg_indirect_left_recursive.eliminate_left_recursive()
    logger.info("\n" + pformat(cfg_2.production_dict))
    logger.info("first set:\n" + pformat(cfg_2.first_sets))
    logger.info("follow set:\n" + pformat(cfg_2.follow_sets))
    try:
        cfg_2_ll1 = LL1CFGSystem(
            entry=cfg_2.entry,
            production_list=cfg_2.production_list,
            allow_conflict=True,
        )
        logger.info("select set\n" + pformat(cfg_2_ll1.select_sets))

    except SelectSetConflictError as e:
        logger.error(e)
        pass


if __name__ == "__main__":
    test_direct_left_recursion()
