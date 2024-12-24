import parser
from cfg import *
import reg_exp as reg
import lexical_analyzer as la
from pprint import pprint


def main():
    program_str = "bccd$"

    # Lexical Analyzer Part

    reg_b = reg.CharExpr("b")
    reg_c = reg.CharExpr("c")
    reg_d = reg.CharExpr("d")
    reg_eof = reg.CharExpr("$")

    lexical_analyzer = la.LexicalAnalyzer(
        token_definitions=[
            la.TokenDefinition("b", reg_b),
            la.TokenDefinition("c", reg_c),
            la.TokenDefinition("d", reg_d),
            la.TokenDefinition("$", reg_eof),
        ],
        use_dfa=True,
    )

    program_token_list = lexical_analyzer.parse(program_str)
    program_token_list = [t for t in program_token_list if t.token_type != "white"]

    print("Tokens:")
    for i in program_token_list:
        print(i)

    # CFG Part
    terminal_a = Terminal(name="a")
    terminal_b = Terminal(name="b")
    terminal_c = Terminal(name="c")
    terminal_d = Terminal(name="d")
    terminal_eof = Terminal(name="$")

    S_pi = NonTerminal("S'")
    S = NonTerminal(name="S")
    E = NonTerminal(name="E")
    A = NonTerminal(name="A")
    B = NonTerminal(name="B")

    cfg_sys = CFGSystem(
        entry=S_pi,
        production_list=[
            Production(source=S_pi, target=Derivation([S, terminal_eof])),
            Production(source=S, target=Derivation([E])),
            Production(source=E, target=Derivation([terminal_a, A])),
            Production(source=E, target=Derivation([terminal_b, B])),
            Production(source=A, target=Derivation([terminal_c, A])),
            Production(source=A, target=Derivation([terminal_d])),
            Production(source=B, target=Derivation([terminal_d])),
            Production(source=B, target=Derivation([terminal_c, B])),
        ],
    )

    print("Used pieces:")
    pprint(cfg_sys.used_pieces)
    print("------------")

    print("Used Non Terminal:")
    pprint(set([i for i in cfg_sys.used_pieces if isinstance(i, NonTerminal)]))

    print("First Set:")
    for k, v in cfg_sys.first_sets.items():
        print(f"First({k}) = {v}")
    print("----------")

    print("Follow Set")
    for k, v in cfg_sys.follow_sets.items():
        print(f"Follow({k}) = {v}")
    print("----------")

    print("Production Dict")
    for k, v in cfg_sys.production_dict.items():
        print(f"{k} -> {v}")
    print("---------------")

    # create parser
    lr_parser = parser.lr.LRParserBase(
        cfg_sys=cfg_sys, epsilon_terminal=Terminal(name="[e]")
    )

    # show graph of that automaton
    gv_ins = lr_parser.stack_automaton.to_graphviz()
    gv_ins.render(directory="./output", view=True)

    parse_tree = lr_parser.parse(program_token_list)

    if parse_tree is not None:
        parse_tree.to_graphviz().render(directory="./output", view=True)


if __name__ == "__main__":
    main()
