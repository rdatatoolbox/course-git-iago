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
