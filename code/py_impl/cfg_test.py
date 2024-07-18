from cfg import *


def main():
    terminal_int = Terminal(name='int')
    terminal_add = Terminal(name='+')
    terminal_mul = Terminal(name='*')
    terminal_eof = Terminal(name='$')
    terminal_left_para = Terminal(name='(')
    terminal_right_para = Terminal(name=')')
    non_terminal_s = NonTerminal(name='S')
    non_terminal_e = NonTerminal(name='E')
    non_terminal_t = NonTerminal(name='T')

    cfg_sys = CFGSystem(production_list=[
        # S = E EOF
        Production(source=non_terminal_s, target=Derivation(pieces=[non_terminal_e, terminal_eof])),
        # E = T + E
        Production(source=non_terminal_e, target=Derivation(pieces=[non_terminal_t, terminal_add, non_terminal_e])),
        # E = T
        Production(source=non_terminal_e, target=Derivation(pieces=[non_terminal_t])),
        # T = (E)
        Production(source=non_terminal_t,
                   target=Derivation(pieces=[terminal_left_para, non_terminal_e, terminal_right_para])),
        # T = int * T
        Production(source=non_terminal_t, target=Derivation(pieces=[terminal_int, terminal_mul, non_terminal_t])),
        # T = int
        Production(source=non_terminal_t, target=Derivation(pieces=[terminal_int])),
    ])

    print('Used pieces:\n', cfg_sys.used_pieces)
    print('Used Non Terminal:\n', set([i for i in cfg_sys.used_pieces if isinstance(i, NonTerminal)]))

    for k, v in cfg_sys.first_sets.items():
        print(f'First({k}) = {v}')

    for k, v in cfg_sys.follow_sets.items():
        print(f'Follow({k}) = {v}')

    for k, v in cfg_sys.production_dict.items():
        print(f'{k} -> {v}')


if __name__ == '__main__':
    main()
