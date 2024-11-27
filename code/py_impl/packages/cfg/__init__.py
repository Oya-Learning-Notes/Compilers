# Contains CFGSystem that is used to deal with Context-free grammar.
from .type import *

# A seperated implementation of Chomsky Grammar system. Mainly
# (or actually only) used for checking the type of chomsky grammar.]
#
# Here "type" actually means the Chomsky Hierarhy of a grammar.
# Checkout https://en.wikipedia.org/wiki/Chomsky_hierarchy for more info.
from .grammar_type import *
