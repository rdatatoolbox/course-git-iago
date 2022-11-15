"""Modifiers concerned with individual slides and their very concrete content.
"""

from modifiers import Regex, TextModifier


class Step(TextModifier):
    """Special abstract parent of slide bodies,
    whose individual slides inherit of.
    Useful a meta-list of children so we can dynamically pick the right type
    by matching document information with their type name.
    """

    pass


class Command(Regex):
    """Common git command to position, but maybe nothing instead."""

    def __init__(self, input: str):
        super().__init__(
            input.strip(),
            r"\\Command\[(.*?)\]{(.*?)}{(.*?)}",
            "anchor loc text",
        )

    @staticmethod
    def new(*args) -> "Command":
        model = (r"\Command[{}]" + "{{{}}}" * 2).format(*args)
        return Command(model)


class HighlightSquare(Regex):
    """Make a node glow a little bit."""

    def __init__(self, input: str):
        super().__init__(
            input.strip(),
            r"\\HighlightSquare\[(.*?)\]{(.*?)}{(.*?)}",
            "padding lower upper",
        )

    @staticmethod
    def new(lower, upper, padding=5) -> "HighlightSquare":
        model = (r"\HighlightSquare[{2}]{{{0}}}{{{1}}}").format(lower, upper, padding)
        return HighlightSquare(model)

class HighlightShade(Regex):
    """Make a node glow a little bit."""

    def __init__(self, input: str):
        super().__init__(
            input.strip(),
            r"\\HighlightShade\[(.*?)\]{(.*?)}",
            "padding node",
        )

    @staticmethod
    def new(node, padding=5) -> "HighlightShade":
        model = (r"\HighlightShade[{1}]{{{0}}}").format(node, padding)
        return HighlightShade(model)

