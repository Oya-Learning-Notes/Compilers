"""
This module try to use a recursive descent method 
to deal with the same example CFG in the test.
"""

from loguru import logger

from parser.parse_tree import ParseTree, ParseTreeNode
from lexical_analyzer import TokenPair
import cfg
import lexical_analyzer as la
import reg_exp as reg


def recursive_parse(tokens, current_position, non_terminal):
    """Recursive descent parser based on the provided grammar."""

    # Base case for empty input (End of input)
    if current_position >= len(tokens):
        raise ValueError(f"Unexpected end of input while parsing {non_terminal}")

    token = tokens[current_position]

    # If the current symbol is a terminal, match it
    if isinstance(non_terminal, cfg.Terminal):
        if token.token_type == non_terminal.name:
            # Match terminal, move to next token
            node_content = TokenPair(token.token_type, token.content)
            node = ParseTreeNode(non_terminal, node_content)
            return node, current_position + 1
        else:
            raise ValueError(
                f"Expected {non_terminal.name}, but found {token.token_type} at position {current_position}"
            )

    # Recursive case for non-terminals:
    if non_terminal == cfg.NonTerminal("S"):
        # S -> E EOF
        node_e, pos = recursive_parse(tokens, current_position, cfg.NonTerminal("E"))
        if tokens[pos].token_type != "$":
            raise ValueError(f"Expected EOF, but found {tokens[pos].token_type}")
        node_eof = ParseTreeNode(cfg.Terminal("$"), TokenPair("$", "$"))
        node = ParseTreeNode(cfg.NonTerminal("S"), pointers=[node_e, node_eof])
        return node, pos + 1

    elif non_terminal == cfg.NonTerminal("E"):
        # E -> T F
        node_t, pos = recursive_parse(tokens, current_position, cfg.NonTerminal("T"))
        node_f, pos = recursive_parse(tokens, pos, cfg.NonTerminal("F"))
        node = ParseTreeNode(cfg.NonTerminal("E"), pointers=[node_t, node_f])
        return node, pos

    elif non_terminal == cfg.NonTerminal("F"):
        # F -> ε | + E
        if (
            current_position < len(tokens)
            and tokens[current_position].token_type == "+"
        ):
            # F -> + E
            node_add = ParseTreeNode(cfg.Terminal("+"), TokenPair("+", "+"))
            node_e, pos = recursive_parse(
                tokens, current_position + 1, cfg.NonTerminal("E")
            )
            node = ParseTreeNode(cfg.NonTerminal("F"), pointers=[node_add, node_e])
            return node, pos
        else:
            # F -> ε (epsilon, no children)
            node = ParseTreeNode(cfg.NonTerminal("F"))
            return node, current_position

    elif non_terminal == cfg.NonTerminal("T"):
        # T -> ( E ) | int U
        if tokens[current_position].token_type == "(":
            # T -> ( E )
            node_left_para = ParseTreeNode(cfg.Terminal("("), TokenPair("(", "("))
            node_e, pos = recursive_parse(
                tokens, current_position + 1, cfg.NonTerminal("E")
            )
            if tokens[pos].token_type != ")":
                raise ValueError(f"Expected ')', but found {tokens[pos].token_type}")
            node_right_para = ParseTreeNode(cfg.Terminal(")"), TokenPair(")", ")"))
            node = ParseTreeNode(
                cfg.NonTerminal("T"), pointers=[node_left_para, node_e, node_right_para]
            )
            return node, pos + 1
        elif tokens[current_position].token_type == "int":
            # T -> int U
            node_int = ParseTreeNode(cfg.Terminal("int"), TokenPair("int", "int"))
            node_u, pos = recursive_parse(
                tokens, current_position + 1, cfg.NonTerminal("U")
            )
            node = ParseTreeNode(cfg.NonTerminal("T"), pointers=[node_int, node_u])
            return node, pos
        else:
            raise ValueError(
                f"Expected '(' or 'int', but found {tokens[current_position].token_type} at position {current_position}"
            )

    elif non_terminal == cfg.NonTerminal("U"):
        # U -> ε | * T
        if (
            current_position < len(tokens)
            and tokens[current_position].token_type == "*"
        ):
            # U -> * T
            node_mul = ParseTreeNode(cfg.Terminal("*"), TokenPair("*", "*"))
            node_t, pos = recursive_parse(
                tokens, current_position + 1, cfg.NonTerminal("T")
            )
            node = ParseTreeNode(cfg.NonTerminal("U"), pointers=[node_mul, node_t])
            return node, pos
        else:
            # U -> ε (epsilon, no children)
            node = ParseTreeNode(cfg.NonTerminal("U"))
            return node, current_position

    else:
        raise ValueError(f"Unrecognized non-terminal: {non_terminal}")


def parse(program_str):

    # Lexical Analyzer Part
    reg_single_dec_number = reg.CharListExpr("0123456789")

    reg_int = reg.MulExpr(
        reg_single_dec_number,
        reg.WildCardExpr(reg_single_dec_number),
    )
    reg_add = reg.CharExpr("+")
    reg_left_para = reg.CharExpr("(")
    reg_right_para = reg.CharExpr(")")
    reg_mul = reg.CharExpr("*")
    reg_white = reg.CharListExpr("\n ")
    reg_whites = reg.MulExpr(
        reg_white,
        reg.WildCardExpr(reg_white),
    )
    reg_eof = reg.CharExpr("$")

    lexical_analyzer = la.LexicalAnalyzer(
        token_definitions=[
            la.TokenDefinition("int", reg_int),
            la.TokenDefinition("+", reg_add),
            la.TokenDefinition("*", reg_mul),
            la.TokenDefinition("white", reg_whites),
            la.TokenDefinition("(", reg_left_para),
            la.TokenDefinition(")", reg_right_para),
            la.TokenDefinition("$", reg_eof),
        ],
        use_dfa=True,
    )

    program_token_list = lexical_analyzer.parse(program_str)
    program_token_list = [t for t in program_token_list if t.token_type != "white"]

    try:
        parse_tree_node, _ = recursive_parse(
            program_token_list, 0, cfg.NonTerminal("S")
        )
        return ParseTree([parse_tree_node])
    except ValueError as e:
        logger.error(f"Parsing error: {e}")
        raise


# Example of using the recursive_parse function
program_str = "1+3+2$"
parse_tree = parse(program_str)
parse_tree.to_graphviz().render(
    filename="recursive_parse", directory="./graphviz", view=True
)
