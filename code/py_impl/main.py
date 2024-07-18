# import sys
# sys.path.insert(0, "./packages")

from reg_exp import CharExpr, MulExpr, AddExpr, WildCardExpr
import automata as fa
import lexical_analyzer as la

single_zero_reg = CharExpr('0')
single_one_reg = CharExpr('1')
binary_expr = MulExpr(
    CharExpr('b'),
    WildCardExpr(
        AddExpr(single_one_reg, single_zero_reg)
    )
)
add_expr = CharExpr('+')
whitespace_expr = AddExpr(CharExpr(' '), CharExpr('\n'))
whitespaces_expr = MulExpr(whitespace_expr, WildCardExpr(whitespace_expr))

binary_graph = fa.visualize.FADiGraph().from_fa(binary_expr.to_fa())
binary_graph.get_graph().render(directory='output', view=True)

analyzer = la.LexicalAnalyzer(token_definitions=[
    la.TokenDefinition(token_type='binary', regular_expr=binary_expr),
    la.TokenDefinition(token_type='add', regular_expr=add_expr),
    la.TokenDefinition(token_type='white', regular_expr=whitespaces_expr),
])

pairs = analyzer.parse("""
b1001110 + b1001b1111111 + b00000000
""")

for p in pairs:
    if p.token_type == 'white':
        continue
    print(p)
