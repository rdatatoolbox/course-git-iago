"""Craft/edit diffed files.
"""

from textwrap import dedent
from typing import cast

from modifiers import Constant, ListOf, MakeListOf, Regex, TextModifier, render_function
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

    @render_function
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

    def erase(self, file: "Diff"):
        """Remove from the chain, taking care of preserving the chain structure."""
        i = 0
        l = self.files
        assert l  # or it's erasing from empty list
        for i, f in enumerate(l):
            if f is file:
                break
        # When erasing not the last one, reconnect.
        if i == len(l) - 1:
            l.pop()
            return
        l.pop(i)
        l[i].pos = cast(str, file.pos)

    def clear(self):
        self.files.clear()


class Diff(Regex):
    """One diffed file."""

    lines: ListOf

    def __init__(self, input: str):
        super().__init__(
            input.strip(),
            r"\[(.*?)\]" * 3 + r"{(.*?)}.*?" * 2 + r"{(.*)}",
            "mod anchor name pos filename lines",
            lines=DiffLines,
        )

    @staticmethod
    def new(**kwargs) -> "Diff":
        """Create a new line with given parameters (minus leading separator)."""
        model = "[{mod}][{anchor}][{name}]{{{pos}}}{{{filename}}}{{}}"
        return Diff(model.format(**kwargs))

    @staticmethod
    def latex_escape(input: str) -> str:
        """Escape special characters for Latex input."""
        input = input.replace("_", r"\_")
        input = input.replace("#", r"\#")
        return input

    def append_text(self, input: str, mod="0"):
        r"""Construct the lines list from raw text.
        Escaping for tex.
        Input is stripped, unless it starts with \n\n in which case \n is kept.
        """
        lines = dedent(self.latex_escape(input)).strip().split("\n")
        if input.startswith("\n\n"):
            lines = [""] + lines
        for line in lines:
            self.lines.append(mod=mod, text=line)

    def set_mod(self, mod: str, start: int, end=None):
        """Modify the state of one or several lines."""
        if end is None:
            end = start
        if end == -1:
            end = len(self.lines.list)
        for line in self.lines.list[start:end]:
            line = cast(DiffLine, line)
            line.mod = mod

    def delete_lines(self, start: int, end=None):
        """Modify the state of one or several lines."""
        if end is None:
            end = start
        if end == -1:
            end = len(self.lines.list)
        self.lines.list = self.lines.list[:start] + self.lines.list[end + 1 :]


class DiffLine(Regex):
    """One diff line."""

    _short = True

    def __init__(self, input: str):
        super().__init__(
            input.strip(),
            r"(.*?)/{(.*)}",
            "mod text",
        )

    @staticmethod
    def new(**kwargs) -> "DiffLine":
        model = "{mod}/{{{text}}}"
        return DiffLine(model.format(**kwargs))


DiffLines = MakeListOf(DiffLine, sep=",\n", tail=True)
