"""Craft/edit diffed files.
"""

import re
from textwrap import dedent
from typing import cast

from modifiers import Constant, ListOf, MakeListOf, Regex, TextModifier
from utils import increment_name


class DiffList(TextModifier):
    """One chain of diffed files.
    Be careful that the first one needs be anchored,
    and the others are located wrt to it.
    """

    _sep = r"\Diff"

    def __init__(self, input: str):
        files = input.split(self._sep)
        self.head = Constant(files.pop(0))
        self.files = [Diff(f) for f in files]

    def render(self) -> str:
        return self._sep.join(m.render() for m in [self.head] + self.files)

    def append(self, **kwargs) -> "Diff":
        # Default connect to previous one and use the same name +1.
        # Start default names with to "F".
        # But the first one needs an explicit position.
        kwargs.setdefault("mod", "0")
        kwargs.setdefault("anchor", "north east")
        if not "pos" in kwargs:
            prevname = cast(str, self.files[-1].name)
            kwargs["pos"] = r"$({}.south east) + (0, -\FileSpacing)$".format(prevname)
        if not "name" in kwargs:
            prevname = cast(str, self.files[-1].name if self.files else "D")
            kwargs["name"] = increment_name(prevname)
        diff = Diff.new(**kwargs)
        self.files.append(diff)
        return diff

    def clear(self):
        self.files.clear()


class Diff(Regex):
    """One diffed file"""

    def __init__(self, input: str):
        super().__init__(
            input,
            r"\[(.*?)\]" * 3 + r"{(.*?)}.*?" * 2 + r"{\s*(.*)\n?\s*}\s*",
            "mod anchor name pos filename lines",
            lines=DiffLines,
        )

    @staticmethod
    def new(**kwargs) -> "Diff":
        """Create a new line with given parameters (minus leading separator)."""
        model = "[{mod}][{anchor}][{name}]{{{pos}}}{{{filename}}}{{\n}}\n"
        return Diff(model.format(**kwargs))

    def set_text(self, input: str):
        """Construct the lines list from raw text.
        Escaping for tex.
        """
        input = input.replace("_", r"\_")
        input = input.replace("#", r"\#")
        for line in dedent(input).strip().split("\n"):
            cast(ListOf, self.lines).append(mod=0, text=line)


class DiffLine(Regex):
    """One diff line."""

    _short = True

    def __init__(self, input: str):
        super().__init__(
            input,
            r"\s*(.*?)/{(.*)}\s*",
            "mod text",
        )

    @staticmethod
    def new(**kwargs) -> "DiffLine":
        model = "    {mod}/{{{text}}}"
        return DiffLine(model.format(**kwargs))


DiffLines = MakeListOf(DiffLine, tail=True)
