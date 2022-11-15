"""Modifiers concerned with individual slides and their very concrete content.
"""

from diffs import DiffList
from filetree import FileTree
from modifiers import Regex, TextModifier, render_function, MakeListOf, Constant
from repo import Repo


class Step(TextModifier):
    """Special abstract parent of slide bodies,
    whose individual slides inherit of.
    """

    pass


ListOfChunks = MakeListOf(Constant, sep="\n\n", head=True, tail=True)


class Clients(Step, ListOfChunks):
    """Good example of simple slide to animate simply with various chunks."""

    pass


class Pizzas(Step):
    """The slide with repo / project folder / file content."""

    def __init__(self, input: str):
        chunks = input.split("\n\n")
        it = iter(chunks)
        next(it)  # Ignore leading_whitespace
        self.filetree = FileTree(next(it))
        self.diffs = DiffList(next(it))
        self.repo = Repo(next(it))
        try:
            self.command = Command(next(it))
        except StopIteration:
            self.command = Command("")
        try:
            while some := next(it):
                assert not some
        except StopIteration:
            pass

    @render_function
    def render(self) -> str:
        return (
            "\n\n"
            + "\n\n".join(
                m.render() if isinstance(m, TextModifier) else m
                for m in (
                    self.filetree,
                    self.diffs,
                    self.repo,
                    self.command,
                )
            )
            + "\n"
        )


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
