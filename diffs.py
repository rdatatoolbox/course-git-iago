"""Craft/edit diffed files.
"""

from textwrap import dedent
from typing import Iterable

from modifiers import (
    AnonymousPlaceHolder,
    ListBuilder,
    MakePlaceHolder,
    PlaceHolder,
    TextModifier,
    render_method,
)

DiffLineModifier, DiffLine = MakePlaceHolder("DiffLine", r"<mod>/{<text>}")
DiffLines = ListBuilder(DiffLine, ",\n", tail=True)


class DiffedFile(TextModifier):
    """One chain of diffed lines."""

    def __init__(self, input: str):
        """First line is an intensive coordinate supposed to locate the first Diff."""
        intro, lines = input.split("{\n", 1)
        self.intro = AnonymousPlaceHolder(
            r"\Diff[<mod>][<anchor>][<name>][<linespacing>]{<location>}{<filename>}",
            "parse",
            intro,
        )
        lines = lines.rsplit("}", 1)[0]
        self.lines = DiffLines.parse(lines)

    @staticmethod
    def new(**kwargs) -> "DiffedFile":
        """Create empty diffed file."""
        model = "\\Diff[{mod}][{anchor}][{name}][{linespacing}]{{{location}}}{{{filename}}}{{\n}}"
        return DiffedFile(model.format(**kwargs))

    @property
    def name(self):
        return self.intro.name

    def set_name(self, name: str) -> "DiffedFile":
        self.intro.name = name
        return self

    @property
    def mod(self):
        return self.intro.mod

    @mod.setter
    def mod(self, value):
        self.intro.mod = value

    @property
    def filename(self) -> str:
        return self.intro.filename

    def set_filename(self, filename: str, mod="0") -> "DiffedFile":
        self.intro.filename = filename
        self.intro.mod = mod
        return self

    @render_method
    def render(self) -> str:
        return self.intro.render() + "{\n" + self.lines.render() + "}\n"

    def clear(self) -> "DiffedFile":
        self.lines.clear()
        return self

    @staticmethod
    def latex_escape(input: str) -> str:
        """Escape special characters for LaTeX input."""
        input = input.replace("_", r"\_")
        input = input.replace("#", r"\#")
        return input

    def append_text(self, input: str, mod="0") -> "DiffedFile":
        r"""Construct the lines list from raw text.
        Input is stripped, unless it starts with \n\n in which case \n is kept.
        """
        lines = dedent(self.latex_escape(input)).strip().split("\n")
        if input.startswith("\n\n"):
            lines = [""] + lines
        for line in lines:
            self.lines.append(mod, line)
        return self

    def lines_range(self, start: int, end=None) -> Iterable[PlaceHolder]:  # DiffLine
        """Iterate on lines, counting from 1, end included, None for single, -1 for end."""
        yield from self.lines.list[start - 1 : end]

    def set_mod(self, mod: str, start: int, end=None) -> "DiffedFile":
        """Modify the state of one or several lines.
        (counting from 1, end included)
        """
        start -= 1
        if end is None:
            end = start + 1
        elif end == -1:
            end = len(self.lines.list)
        for line in self.lines.list[start:end]:
            line.mod = mod
        return self

    def delete_lines(self, start: int, end=None):
        """Delete a range of lines."""
        if end is None:
            end = start
        if end == -1:
            end = len(self.lines.list)
        self.lines.list = self.lines.list[:start] + self.lines.list[end + 1 :]
