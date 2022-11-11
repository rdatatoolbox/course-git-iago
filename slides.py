"""Modifiers concerned with individual slides and their very concrete content.
"""

import re
from textwrap import dedent
from typing import cast

from modifiers import Constant, ListOf, MakeListOf, Regex, TextModifier


def increment_name(name: str) -> str:
    """If ending with an integer, increment and return.
    Otherwise append 1.
    """
    try:
        m = cast(re.Match, re.compile(r"(.*)(\d+)$").match(name))
        name, n = m.group(1), int(m.group(2))
    except:
        n = 0
    return name + str(n + 1)


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
        self.repo = next(it)
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
                )
            )
            + "\n\n"
        )


class FileTree(TextModifier):
    """Within the file tree.
    Be careful that when hiding one file line,
    the chain of relative positionning needs to be reconnected.
    """

    def __init__(self, input: str):
        # Refer to them as list to easily reconnect the chain.
        self.list = [FileTreeLine(l) for l in input.split("\n")]

    def render(self) -> str:
        return "\n".join(m.render() for m in self.list)

    def append(self, command: str, **kwargs) -> "FileTreeLine":
        # Default connect to previous one and use the same name +1.
        # Start default names with "F".
        # But the first one needs an explicit position.
        if not "pos" in kwargs:
            kwargs["pos"] = self.list[-1].name
        if not "name" in kwargs:
            prevname = cast(str, self.list[-1].name if self.list else "F")
            kwargs["name"] = increment_name(prevname)
        file = FileTreeLine.new(command, **kwargs)
        for option in "type mod".split():
            if option in kwargs:
                setattr(file, option, kwargs[option])
        for option in "connect last".split():
            if option in kwargs:
                file.set_keyword_option(option, kwargs[option])
        self.list.append(file)
        return file

    def erase(self, file: "FileTreeLine"):
        """Remove from the chain, taking care of preserving the chain structure."""
        i = 0
        l = self.list
        assert l  # or it's erasing from empty list
        for i, f in enumerate(l):
            if f is file:
                break
        if i == len(l):
            # When erasing last one, previous needto become the last.
            l.pop()
            if not l:
                return
            l[-1].set_keyword_option("last", True)
            return
        # When erasing not the last one, reconnect.
        l.pop(i)
        l[i].pos = cast(str, file.pos)

    def clear(self):
        self.list.clear()


class FileTreeLine(Regex):
    """Parse special line displaying one file in the tree folder."""

    def __init__(self, input: str):
        super().__init__(
            input,
            r"\s*\\.*?\[(.*?),.*?mod=(.).*?(|, connect)(|, last)\]{(.*?)}{(.*?)}{(.*?)}",
            "type mod connect last pos name filename",
        )

    @staticmethod
    def new(command, **kwargs) -> "FileTreeLine":
        """Create a new line with given parameters.
        Cannot set options via this interface, though.
        """
        model = r"\{cmd}[file, mod=0]{{{pos}}}{{{name}}}{{{filename}}}"
        return FileTreeLine(model.format(cmd=command, **kwargs))

    def set_keyword_option(self, option: str, on: bool):
        """Lame options because of the comma, fix with this interface."""
        setattr(self, option, f", {option}" if on else "")


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
            r"\[(.*?)\]" * 3 + r"{(.*?)}.*?" * 2 + r"{(.*)}",
            "mod anchor name pos filename lines",
            lines=DiffLines,
        )

    @staticmethod
    def new(**kwargs) -> "Diff":
        """Create a new line with given parameters (minus leading separator)."""
        model = "[{mod}][{anchor}][{name}]{{{pos}}}{{{filename}}}{{}}"
        return Diff(model.format(**kwargs))

    def set_text(self, input: str):
        """Construct the lines list from raw text.
        Escaping for tex.
        """
        input = input.replace("_", r"\_")
        input = input.replace("#", r"\#")
        for line in dedent(input).strip().split("\n"):
            cast(ListOf, self.lines).append(mod=0, text=line)

    def render(self) -> str:
        """Cheat a tiny bit to insert newline in front of first line."""
        l = cast(ListOf, self.lines).list
        if l:
            first = cast(Regex, l[0])
            m = first._match
            if not m.string.startswith("\n"):
                first._match = cast(re.Match, m.re.match("\n" + m.string))
                assert first._match  # or the cheat failed.
        return super().render()


class DiffLine(Regex):
    """One diff line."""

    def __init__(self, input: str):
        super().__init__(
            input,
            r"\s*(.*?)/{(.*)}",
            "mod text",
        )

    @staticmethod
    def new(**kwargs) -> "DiffLine":
        model = "{mod}/{{{text}}}"
        return DiffLine(model.format(**kwargs))


DiffLines = MakeListOf(DiffLine, tail=True)
