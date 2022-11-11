"""Modifiers concerned with individual slides and their very concrete content.
"""

from typing import cast

from modifiers import Constant, Regex, TextModifier


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
        self.diffconfig = Constant(next(it))
        self.readme = next(it)
        self.margherita = next(it)
        self.regina = next(it)
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
                    self.diffconfig,
                    self.readme,
                    self.margherita,
                    self.regina,
                    self.repo,
                )
            )
            + "\n\n"
        )


class FileLine(Regex):
    """Parse special line displaying one file in the tree folder."""

    def __init__(self, input: str):
        super().__init__(
            input,
            r"\s*\\.*?\[(.*?),.*?mod=(.).*?(|, connect)(|, last)\]{(.*?)}{(.*?)}{(.*?)}",
            "type mod connect last pos name filename",
        )

    @staticmethod
    def new(command, **kwargs) -> "FileLine":
        """Create a new line with given model.
        Cannot set options via this interface, though.
        """
        model = r"\{cmd}[file, mod=0]{{{pos}}}{{{name}}}{{{filename}}}"
        return FileLine(model.format(cmd=command, **kwargs))

    def set_connect(self, on: bool):
        """Lame option because of the comma, fix with this interface."""
        self.connect = ", connect" if on else ""

    def set_last(self, on: bool):
        """Lame option because of the comma, fix with this interface."""
        self.connect = ", last" if on else ""


class FileTree(TextModifier):
    """Within the file tree.
    Be careful that when hiding one file line,
    the chain of relative positionning needs to be reconnected.
    """

    def __init__(self, input: str):
        # Refer to them as list to easily reconnect the chain.
        self.list = [FileLine(l) for l in input.split("\n")]

    def render(self) -> str:
        return "\n".join(m.render() for m in self.list)

    def append(self, command: str, **kwargs) -> FileLine:
        # Default connect to previous one and use the same name +-next.
        if not "pos" in kwargs:
            kwargs["pos"] = self.list[-1].name
        if not "name" in kwargs:
            kwargs["name"] = self.list[-1].name + "-next"
        file = cast(FileLine, FileLine.new(command, **kwargs))
        self.list.append(file)
        return file

    def erase(self, file: FileLine):
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
            l[-1].set_last(True)
            return
        # When erasing not the last one, reconnect.
        l.pop(i)
        l[i].pos = file.pos

    def clear(self):
        self.list.clear()
