"""Modifiers concerned with individual slides and their very concrete content.
"""

from diffs import DiffList
from repo import Repo
from filetree import FileTree
from modifiers import TextModifier, Regex


class Step(TextModifier):
    """Special abstract parent of slide bodies,
    whose individual slides inherit of.
    """

    pass


class Introduction(Step):
    """Empty slide for now."""

    def __init__(self, input: str):
        assert not input.strip()

    def render(self) -> str:
        return "\n\n"


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
            + "\n\n"
        )


class Command(Regex):
    """Optionally a git command to position, but maybe nothing instead."""

    def __init__(self, input: str):
        if input.strip():
            super().__init__(
                input,
                r"\s*\\Command\[(.*?)\]{(.*?)}{(.*?)}",
                "anchor loc cmd",
            )
            self._visible = True
        else:
            self._visible = False

    @staticmethod
    def new(*args) -> "Command":
        model = (r"  \Command[{}]" + "{{{}}}" * 2).format(*args)
        res = Command(model)
        res._visible = True
        return res

    def render(self) -> str:
        if not self._visible:
            return ""
        return super().render()
