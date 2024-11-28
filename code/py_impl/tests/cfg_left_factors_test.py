from loguru import logger
from cfg import CFGSystem, Terminal, NonTerminal, Production, Derivation
from cfg import LL1CFGSystem, LL1CFGSystemError, SelectSetConflictError
from pprint import pformat

# Define NonTerminals
X = NonTerminal("X")
Y = NonTerminal("Y")
Z = NonTerminal("Z")

# Define Terminals
a = Terminal("a")
b = Terminal("b")
c = Terminal("c")
d = Terminal("d")
end = Terminal("$")

# Define productions with shared left factors
# X -> aY | aZ | b
# Y -> c
# Z -> d
productions_ll1_after_extraction = [
    Production(source=X, target=Derivation([a, Y])),  # X → a Y
    Production(source=X, target=Derivation([a, Z])),  # X → a Z
    Production(source=X, target=Derivation([b])),  # X → b
    Production(source=Y, target=Derivation([c])),  # Y → c
    Production(source=Z, target=Derivation([d])),  # Z → d
]


# Define NonTerminals
from cfg import CFGSystem, Terminal, NonTerminal, Production, Derivation

# Define NonTerminals
S = NonTerminal("S")
X = NonTerminal("X")
A = NonTerminal("A")
B = NonTerminal("B")
C = NonTerminal("C")

# Define Terminals
add = Terminal("+")


T = NonTerminal("T")

# Define Productions after Left Factoring
productions_not_ll1_after_extraction = [
    Production(source=S, target=Derivation([a, X])),  # S → a X
    Production(source=S, target=Derivation([b, A])),  # S → b A
    Production(source=X, target=Derivation([A])),  # X → A
    Production(source=X, target=Derivation([B])),  # X → B
    Production(source=A, target=Derivation([c])),  # A → c
    Production(source=A, target=Derivation([])),  # A → ε
    Production(source=B, target=Derivation([d])),  # B → d
    Production(source=B, target=Derivation(None)),  # B → ε
]


test_production_list = [
    Production(source=S, target=Derivation([T])),
    Production(source=S, target=Derivation([T, add, A])),
    Production(source=S, target=Derivation([T, add, B])),
    Production(source=S, target=Derivation([T, add, B, add, C])),
    Production(source=S, target=Derivation([d, X])),
    Production(source=X, target=Derivation([a])),
    Production(source=A, target=Derivation([a])),
    Production(source=B, target=Derivation([b])),
    Production(source=C, target=Derivation([c])),
    Production(source=T, target=Derivation([d])),
]


# Test cases definition end.
# --------------------------------------------------------------


def test_left_factor_extraction():
    logger.info("Forst test case:")
    ll1_cfg = LL1CFGSystem(
        production_list=productions_ll1_after_extraction,
        entry=X,
        allow_conflict=True,
    )
    new_ll1_cfg = ll1_cfg.extract_left_factors()
    logger.info("Productions:\n" + pformat(new_ll1_cfg.production_dict))
    logger.info("New Productions:\n" + pformat(new_ll1_cfg.production_dict))
    logger.info("First sets:\n" + pformat(new_ll1_cfg.first_sets))
    logger.info("Follow sets:\n" + pformat(new_ll1_cfg.follow_sets))
    logger.info("Select sets:\n" + pformat(new_ll1_cfg.select_sets))
    logger.success(f"New CFG is_ll_1()={new_ll1_cfg.is_ll_1()}")

    logger.success("-------------------------------------------------")
    logger.info("Second test case:")

    not_ll1_cfg = LL1CFGSystem(
        production_list=productions_not_ll1_after_extraction,
        entry=S,
        allow_conflict=True,
    )
    logger.info("Productions:\n" + pformat(not_ll1_cfg.production_dict))
    new_not_ll1_cfg = not_ll1_cfg.extract_left_factors()
    logger.info("New Productions:\n" + pformat(new_not_ll1_cfg.production_dict))
    logger.info("First sets:\n" + pformat(new_not_ll1_cfg.first_sets))
    logger.info("Follow sets:\n" + pformat(new_not_ll1_cfg.follow_sets))
    logger.info("Select sets:\n" + pformat(new_not_ll1_cfg.select_sets))
    logger.success(f"New CFG is_ll_1()={new_not_ll1_cfg.is_ll_1()}")

    logger.success("-------------------------------------------------")
    logger.info("Third test case:")

    test_cfg = LL1CFGSystem(
        production_list=test_production_list, entry=S, allow_conflict=True
    )
    test_cfg = test_cfg.extract_left_factors(render=True)
    # test_cfg = test_cfg.extract_left_factors(render=True)


if __name__ == "__main__":
    test_left_factor_extraction()
