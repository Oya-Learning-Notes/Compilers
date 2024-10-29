import sys
from loguru import logger
from os import environ

from cfg.grammar_type import (
    run_example_cases,
    ChomskyGrammarSystem,
    ChomskyProduction,
    Piece,
    NonTerminal,
    Terminal,
    HIERARCHY_TEXT,
)

# suppress default logger
logger.remove()

# custom logger format
# simplified for this program
fmt = (
    # "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    # "<cyan>{name}</cyan>:"
    # "<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# add custom logger
logger.add(sys.stderr, format=fmt, level="DEBUG")

# set up file logger.
logger.add("./chomsky_type.log", format=fmt, level="DEBUG")


def run_test():
    # run test cases
    run_example_cases()

    # success
    logger.success("All cases executed")


def chomsky_grammar_input() -> ChomskyGrammarSystem:
    """
    Prompt user to input a chomsky grammar from command line
    """
    productions: list[ChomskyProduction] = []
    used_pieces: dict[str, Piece] = {}

    while True:
        production_str = input(
            "Input a production (E.g.: ABC->aBc) (Input 0 or empty line to finish. Enter q to quit): \n"
        )

        if production_str == 'q':
            raise KeyboardInterrupt()

        production_str = production_str.replace(",", "").replace("\\e", "")

        # input end
        if production_str == "" or production_str == "0":
            break

        # convert production str to production
        try:
            productions.append(
                convert_string_to_production(production_str, used_pieces)
            )
        except Exception as e:
            logger.error(f"Invalid production string: {production_str}")
            logger.error(e)
            logger.error("Please input again")
            continue

    # get entry production
    entry: NonTerminal | None = None
    while True:
        entry_str = input("Input the start symbol: \n")
        try:
            entry = used_pieces[entry_str]  # type: ignore
            assert isinstance(
                entry, NonTerminal
            ), "Input symbol is not a non-terminal(Vn)"
            break
        except Exception as e:
            logger.error(f"Invalid start symbol: {entry_str}")
            logger.error(e)
            logger.error("Please input again")

    # construct grammar
    return ChomskyGrammarSystem(
        entry=entry, productions=productions, pieces=list(used_pieces.values())
    )


def convert_string_to_production(
    production_str: str,
    used_pieces: dict[str, Piece],
) -> ChomskyProduction:
    """
    Convert a production string to a ChomskyProduction,
    also update used_pieces in place.
    """
    # split production string
    left, right = production_str.split("->")
    left = left.strip()
    right = right.strip()

    def string_to_pieces(string: str) -> list[Piece]:
        pieces_for_str: list[Piece] = []

        # return empty list
        if string == "":
            return pieces_for_str

        nonlocal used_pieces

        for c in string:
            if c.isupper():
                used_pieces.setdefault(c, NonTerminal(c))
            else:
                used_pieces.setdefault(c, Terminal(c))

            pieces_for_str.append(used_pieces[c])

        return pieces_for_str

    return ChomskyProduction(string_to_pieces(left), string_to_pieces(right))


def main():
    run_test()

    logger.info("Pre-defined test finished, result as above. ")
    logger.info("Now you can input and test your own grammar. ")

    while True:
        try:
            grammar = chomsky_grammar_input()
        except KeyboardInterrupt:
            return 0
        except Exception as e:
            logger.error(e)
            logger.error("Failed to input a chomsky grammar, please try again. ")
            continue

        logger.info(f"Grammar:\n {grammar}")
        logger.success(
            f"Grammar Chomsky Hierarchy: {HIERARCHY_TEXT[grammar.chomsky_hierarchy]} ({grammar.chomsky_hierarchy})"
        )


if __name__ == "__main__":
    main()
