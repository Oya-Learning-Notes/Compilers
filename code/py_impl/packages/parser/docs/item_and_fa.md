Lots of LR Parser will use Stack Automaton and Items. So the `parser` module could implement the base functionality
of those two part.

# Items

Both SLR, CLR and LALR uses Items.

SLR use LR(0) Items, LALR and CLR use LR(1) Items. The only difference between these two is that if it has
a `lookahead`.

In this case we could actually simply implement LR(1) Items, and set `lookahead` to `None` when using it with SLR
algorithm. Or in another word, SLR only using the `core` of the LR(1) Items.