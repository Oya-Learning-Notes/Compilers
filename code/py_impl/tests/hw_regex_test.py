import reg_exp
from reg_exp import CharExpr, MulListExpr, AddExpr, WildCardExpr, AddListExpr
from automata.visualize import FADiGraph

a_re = CharExpr("a")
b_re = CharExpr("b")
c_re = CharExpr("c")

abc_re = reg_exp.MulListExpr([a_re, b_re, c_re])

bandc_re = AddExpr(b_re, c_re)

bandc_wildcard_re = WildCardExpr(bandc_re)

b_or_c_wildcard_a_re = MulListExpr([bandc_wildcard_re, a_re])

b_wildcard_re = WildCardExpr(b_re)

b_wildcard_c_re = MulListExpr([b_wildcard_re, c_re])

final_re = AddListExpr([abc_re, b_or_c_wildcard_a_re, b_wildcard_c_re])
final_fa = final_re.to_fa()

original_fa = final_fa.__deepcopy__()
original_graph = FADiGraph(name="1 - Original Regex", fa=original_fa).render(
    format="png"
)

final_dfa = original_fa.to_dfa().__deepcopy__()
dfa_graph = FADiGraph(name="2 - Determined FA", fa=final_dfa).render(format="png")

min_dfa = final_dfa.minimize()

graph = FADiGraph(name="3 - Minimized Regex", fa=min_dfa)
graph.render(format="png")
