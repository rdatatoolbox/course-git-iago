"""Craft/edit a simple file tree.
"""

from typing import cast

from document import AutomaticCoordinates
from modifiers import Regex, TextModifier, render_method
from utils import increment_name


class FileTree(TextModifier):
    """Within the file tree.
    Be careful that when hiding one file line,
    the chain of relative positionning needs to be reconnected.
    """

    def __init__(self, input: str):
        """First line is an intensive coordinate supposed to locate the second line.
        The chain only contains 1 element in the stub.
        """
        xy, first_file = input.split("\n")
        self.xy = xy = AutomaticCoordinates.parse(xy)
        # Refer to them as a list to easily reconnect the chain.
        first_file = FileTreeLine(first_file)
        first_file.pos = xy.name
        self.list = [first_file]

    @render_method
    def render(self) -> str:
        return "\n".join(m.render() for m in [self.xy] + self.list)

    def populate(self, filetree: "FileTree") -> "FileTree":
        """Import/copy all files from another value."""
        self.clear()
        for file in filetree.list:
            self.list.append(file.copy())
        return self

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
        if i == len(l) - 1:
            # When erasing last one, previous need to become the last.
            l.pop()
            if len(l) <= 1:
                return
            l[-1].set_keyword_option("last", True)
            return
        # When erasing not the last one, reconnect.
        l.pop(i)
        l[i].pos = cast(str, file.pos)

    def clear(self):
        self.list.clear()

    def __getitem__(self, name: str) -> "FileTreeLine":
        """Search and retrieve file by name."""
        for file in self.list:
            if file.filename == name:
                return file
        raise KeyError(f"No such file in file tree: {repr(name)}.")


class FileTreeLine(Regex):
    """Parse special line displaying one file in the tree folder."""

    _short = True

    def __init__(self, input: str):
        super().__init__(
            input.strip(),
            r"\\(.*?)\[(.*?),.*?mod=(.).*?(|, connect)(|, last)\]{(.*?)}{(.*?)}{(.*?)}",
            "cmd type mod connect last pos name filename",
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
