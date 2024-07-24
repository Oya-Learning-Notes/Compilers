import parser
from cfg import *
import reg_exp as reg
import lexical_analyzer as la
from pprint import pprint


def main():
    program_str = '5*((1+2)*3)$'
    # 1+3+2$
    # | int + int + int eof
    # int | + int + int eof
    # int U | + int + int eof
    # T | + int + int eof
    # T + | int + int eof
    # T + int | + int eof
    # T + int U | ..
    # T + T | + int eof

    # Lexical Analyzer Part

    reg_single_dec_number = reg.CharListExpr('0123456789')

    reg_int = reg.MulExpr(
        reg_single_dec_number,
        reg.WildCardExpr(reg_single_dec_number),
    )
    reg_add = reg.CharExpr('+')
    reg_left_para = reg.CharExpr('(')
    reg_right_para = reg.CharExpr(')')
    reg_mul = reg.CharExpr('*')
    reg_white = reg.CharListExpr('\n ')
    reg_whites = reg.MulExpr(
        reg_white,
        reg.WildCardExpr(reg_white),
    )
    reg_eof = reg.CharExpr('$')

    lexical_analyzer = la.LexicalAnalyzer(
        token_definitions=[
            la.TokenDefinition('int', reg_int),
            la.TokenDefinition('+', reg_add),
            la.TokenDefinition('*', reg_mul),
            la.TokenDefinition('white', reg_whites),
            la.TokenDefinition('(', reg_left_para),
            la.TokenDefinition(')', reg_right_para),
            la.TokenDefinition('$', reg_eof),

        ],
        use_dfa=True
    )

    program_token_list = lexical_analyzer.parse(program_str)
    program_token_list = [t for t in program_token_list if t.token_type != 'white']

    print('Tokens:')
    for i in program_token_list:
        print(i)

    # CFG Part

    terminal_int = Terminal(name='int')
    terminal_add = Terminal(name='+')
    terminal_mul = Terminal(name='*')
    terminal_eof = Terminal(name='$')
    terminal_left_para = Terminal(name='(')
    terminal_right_para = Terminal(name=')')
    non_terminal_s = NonTerminal(name='S')
    non_terminal_e = NonTerminal(name='E')
    non_terminal_f = NonTerminal(name='F')
    non_terminal_t = NonTerminal(name='T')
    non_terminal_u = NonTerminal(name='U')

    non_terminal_s_pi = NonTerminal(name='S\'')
    non_terminal_c = NonTerminal(name='C')
    terminal_c = Terminal(name='c')
    terminal_d = Terminal(name='d')

    cfg_sys_without_left_factoring = CFGSystem(
        production_list=[
            # S -> E$
            Production(source=non_terminal_s, target=Derivation(pieces=[non_terminal_e, terminal_eof])),
            # E -> T + E
            Production(source=non_terminal_e, target=Derivation(pieces=[non_terminal_t, terminal_add, non_terminal_e])),
            # E -> T
            Production(source=non_terminal_e, target=Derivation(pieces=[non_terminal_t])),
            # T -> (E)
            Production(source=non_terminal_t,
                       target=Derivation(pieces=[terminal_left_para, non_terminal_e, terminal_right_para])),
            # T -> int
            Production(source=non_terminal_t, target=Derivation(pieces=[terminal_int])),
            # T -> T * T
            Production(source=non_terminal_t, target=Derivation(pieces=[non_terminal_t, terminal_mul, non_terminal_t]))
        ],
        entry=non_terminal_s
    )

    cfg_sys = CFGSystem(production_list=[
        # E = T | T + E
        # T = (E) | int | int * T

        # S = E EOF
        Production(source=non_terminal_s, target=Derivation(pieces=[non_terminal_e, terminal_eof])),
        # E = T F
        Production(source=non_terminal_e, target=Derivation(pieces=[non_terminal_t, non_terminal_f])),
        # F = epsilon
        Production(source=non_terminal_f, target=Derivation(pieces=None)),
        # F = + E
        Production(source=non_terminal_f, target=Derivation(pieces=[terminal_add, non_terminal_e])),
        # # F = *T
        # Production(source=non_terminal_f, target=Derivation(pieces=[terminal_mul, non_terminal_t])),
        # T = (E)
        Production(source=non_terminal_t,
                   target=Derivation(pieces=[terminal_left_para, non_terminal_e, terminal_right_para])),
        # T = int U
        Production(source=non_terminal_t, target=Derivation(pieces=[terminal_int, non_terminal_u])),
        # U = epsilon
        Production(source=non_terminal_u, target=Derivation(pieces=None)),
        # U = * T
        Production(source=non_terminal_u, target=Derivation(pieces=[terminal_mul, non_terminal_t])), ],
        entry=non_terminal_s)

    cfg_sys_on_dragon_book = CFGSystem(
        production_list=[
            Production(source=non_terminal_s_pi, target=Derivation(pieces=[non_terminal_s, terminal_eof])),
            Production(source=non_terminal_s, target=Derivation(pieces=[non_terminal_c, non_terminal_c])),
            Production(source=non_terminal_c, target=Derivation(pieces=[terminal_c, non_terminal_c])),
            Production(source=non_terminal_c, target=Derivation(pieces=[terminal_d]))
        ],
        entry=non_terminal_s_pi
    )

    cfg_production_could_cause_reduce_reduce_conflict = CFGSystem(
        production_list=[
            Production(source=non_terminal_s_pi, target=Derivation(pieces=[non_terminal_s, terminal_eof])),
            Production(source=non_terminal_s, target=Derivation(pieces=[non_terminal_c, non_terminal_c])),
            Production(source=non_terminal_c, target=Derivation(pieces=[non_terminal_c, non_terminal_c])),
            Production(source=non_terminal_c, target=Derivation(pieces=[terminal_d]))
        ],
        entry=non_terminal_s_pi
    )

    print('Used pieces:')
    pprint(cfg_sys.used_pieces)
    print('------------')

    print('Used Non Terminal:')
    pprint(set([i for i in cfg_sys.used_pieces if isinstance(i, NonTerminal)]))

    print('First Set:')
    for k, v in cfg_sys.first_sets.items():
        print(f'First({k}) = {v}')
    print('----------')

    print('Follow Set')
    for k, v in cfg_sys.follow_sets.items():
        print(f'Follow({k}) = {v}')
    print('----------')

    print('Production Dict')
    for k, v in cfg_sys.production_dict.items():
        print(f'{k} -> {v}')
    print('---------------')

    # try generating default stack automaton
    stack_automaton = parser.lr.StackAutomaton(cfg_sys_without_left_factoring)

    # show graph of that automaton
    gv_ins = stack_automaton.to_graphviz()
    gv_ins.render(directory='./output', view=True)

    # create parser
    lr_parser = parser.lr.LRParserBase(
        cfg_sys=cfg_sys_without_left_factoring,
        epsilon_terminal=Terminal(name='[e]')
    )

    parse_tree = lr_parser.parse(program_token_list)

    parse_tree.to_graphviz().render(directory='./output', view=True)


if __name__ == '__main__':
    main()
