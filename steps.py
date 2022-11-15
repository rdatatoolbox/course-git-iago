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
    """Optionally a git command to position, but maybe nothing instead."""

    def __init__(self, input: str):
        if input.strip():
            super().__init__(
                input,
                r"\s*\\Command\[(.*?)\]{(.*?)}{(.*?)}",
                "anchor loc text",
            )
            self._rendered = True
        else:
            self._rendered = False

    @staticmethod
    def new(*args) -> "Command":
        model = (r"  \Command[{}]" + "{{{}}}" * 2).format(*args)
        res = Command(model)
        res._rendered = True
        return res
