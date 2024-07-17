from dataclasses import dataclass


@dataclass
class Piece:
    name: str


class Terminal(Piece):
    pass


class NonTerminal(Piece):
    pass


class Production:
    source: NonTerminal
    target: list[Piece] | None
