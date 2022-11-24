"""Craft/edit diffed files.
"""

import re
from textwrap import dedent
from typing import Iterable, List, Tuple, cast

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

    @staticmethod
    def latex_escape(input: str) -> str:
        """Escape special characters for LaTeX input."""
        input = input.replace("_", r"\_")
        input = input.replace("#", r"\#")
        return input

    def line_index(self, i=-1) -> int:
        """Convert from natural line indexing to python index."""
        return len(self.lines) - 1 if i == -1 else i - 1

    def line_index_range(self, start=1, end: int | None = None) -> Tuple[int, int]:
        """Convert from natural line range to python index:
        7 : line 7 alone
        1 : first line
        1, 3 : line 1 to 3 included
        4, -1 : line 4 down to the end
        """
        start -= 1
        if end is None:
            end = start
        elif end == -1:
            end = len(self.lines)
        return start, end

    def __getitem__(self, i: int) -> PlaceHolder:  # Line
        return self.lines[self.line_index(i)]

    def pop(self, i: int) -> PlaceHolder:  # Line
        return self.lines.list.pop(self.line_index(i))

    def lines_range(self, *args, **kwargs) -> Iterable[PlaceHolder]:  # DiffLine
        if len(args) == 1 and not kwargs:
            if type(i := args[0]) is int:
                yield self[i]
            else:
                indices = cast(List[int], i)
                for i in indices:
                    yield self[i]
        else:
            s, e = self.line_index_range(*args, **kwargs)
            yield from self.lines.list[s:e]

    def erase_lines(self, *args, **kwargs) -> "DiffedFile":
        s, e = self.line_index_range(*args, **kwargs)
        del self.lines.list[s:e]
        return self

    def clear(self) -> "DiffedFile":
        self.lines.list.clear()
        return self

    def set_mod(self, mod: str, *args, **kwargs) -> "DiffedFile":
        """Modify the state of one or several lines."""
        for line in self.lines_range(*args, **kwargs):
            line.mod = mod
        return self

    def reset(self, mod="0") -> "DiffedFile":
        """Set all lines modes + file's."""
        self.mod = mod
        for line in self.lines:
            line.mod = mod
        return self

    def insert_lines(
        self,
        input: str | PlaceHolder | List[PlaceHolder],
        mod: str | int = "0",
        index=-1,
    ) -> "DiffedFile":
        r"""Construct the lines list from raw text.
        Input is stripped, unless it starts with \n\n in which case \n is kept.
        """
        if type(input) is str:
            lines = dedent(self.latex_escape(input)).strip().split("\n")
            if input.startswith("\n\n"):
                lines = [""] + lines
            lines = [self.lines.builder.new("<nomod>", l) for l in lines]
        elif isinstance(input, PlaceHolder):
            lines = [input]
        else:
            lines = cast(List[PlaceHolder], input)

        if type(mod) is int:
            assert index == -1  # Don't provide two indices.
            index = mod
            mod = "0"
        mod = cast(str, mod)

        for line in lines:
            line.mod = mod

        i = self.line_index(index)
        self.lines.list[i:i] = lines
        return self

    def replace_in_line(
        self, i: int, pattern: str, replace: str
    ) -> Tuple[PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder]:  # DiffLine
        """Duplicate the line with correct patches so it displays,
        Provide regex pattern with 1 group to be replaced.
        Return the three lines variants + a variant for after merging.
        """
        i = self.line_index(i)
        original = self.lines.list.pop(i)
        before, after, merged = (original.copy() for _ in range(3))
        before.mod = "-"
        after.mod = "+"
        merged.mod = "0"

        rg = re.compile(pattern)
        for line, c in ((before, 1), (after, 2), (merged, 3)):
            for m in reversed([*rg.finditer(original.text)]):
                s, e = m.span(1)
                t = line.text
                if c == 1:
                    rep = m.group(1)
                else:
                    rep = replace
                if c in (1, 2) and rep:
                    rep = r"\dhi{" + rep + "}"
                line.text = t[:s] + rep + t[e:]

        self.lines.list[i:i] = [before, after]
        return tuple(l.copy() for l in (original, before, after, merged))

    def populate(self, other: "DiffedFile") -> "DiffedFile":
        """Import all lines and mods, from another diffed file."""
        self.clear()
        for line in other.lines:
            self.lines.append(line.copy())
        self.mod = other.mod
        return self

    def mark_lines(self, *args, **kwargs) -> "DiffedFile":
        r"""Wrap whole lines into \dhi{}."""
        for line in self.lines_range(*args, **kwargs):
            line.text = r"\dhi{" + line.text + "}"
        return self

    def unmark_lines(self, *args, **kwargs) -> "DiffedFile":
        r"""Remove \dhi{} marks from the given line."""
        for line in self.lines_range(*args, **kwargs):
            line.text = line.text.replace(r"\dhi{", "").replace("}", "")
        return self

    def unmark_all(self) -> "DiffedFile":
        return self.unmark_lines(1, -1)
