__all__ = [
    "BaseError",
]


class BaseError(Exception):
    """
    General error that used in the whole CC(Compiler's Compiler) packages series.

    Usage:

    The best practice is to create a new sub base-error class for each sub packages
    in this system.

    For example, if there is a package called `automata`, then you may want to create
    a subclass call `AutomataBaseError`, which will allow user to distinguish errors
    threw from different sub packages of this system.

    SubClasses:

    It's recommended to only override `__init__()` method when creating your own
    subclasses, following is an example:

        class UnprocessableEpsilonRule(ChomskyGrammarError):
            def __init__(
                self,
                name="unprocessable_epsilon_rule",
                message="This epsilon rule could not be handled by current program",
                production: "ChomskyProduction | None" = None,
            ):
                if production is not None:
                    message += f" (Production: {production})"
                super().__init__(name, message)
    """

    name: str
    message: str

    def __init__(self, name: str, message: str):
        self.name = name
        self.message = message
        super().__init__(message)

    def __repr__(self):
        return f"{self.message} ({self.name})"

    def __str__(self) -> str:
        return repr(self)
