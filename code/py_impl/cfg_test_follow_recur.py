from cfg import *


def main():
    terminal_int = Terminal(name='int')
    terminal_add = Terminal(name='+')
    terminal_mul = Terminal(name='*')
    terminal_eof = Terminal(name='$')
    terminal_a = Terminal(name='a')
    terminal_b = Terminal(name='b')
    terminal_c = Terminal(name='c')
    terminal_d = Terminal(name='d')

    non_terminal_a = NonTerminal(name='A')
    non_terminal_b = NonTerminal(name='B')
    non_terminal_c = NonTerminal(name='C')
    non_terminal_d = NonTerminal(name='D')

    cfg_sys = CFGSystem(production_list=[
        # A -> BC | a
        # C -> DA | c
        Production(source=non_terminal_a, target=Derivation(pieces=[terminal_a])),
        Production(source=non_terminal_a, target=Derivation(pieces=None)),
        Production(source=non_terminal_b, target=Derivation(pieces=[terminal_b])),
        Production(source=non_terminal_c, target=Derivation(pieces=[terminal_c])),
        Production(source=non_terminal_d, target=Derivation(pieces=[terminal_d])),

        Production(source=non_terminal_a, target=Derivation(pieces=[non_terminal_b, non_terminal_c])),
        Production(source=non_terminal_c, target=Derivation(pieces=[non_terminal_d, non_terminal_a])),
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
