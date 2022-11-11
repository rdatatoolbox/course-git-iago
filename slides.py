"""Modifiers concerned with individual slides and their very concrete content.
"""

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
            r"\s*\\.*?mod=(.).*?(|, last)\]{(.*?)}{(.*?)}{(.*?)}",
            "mod last pos name filename",
        )


class FileTree(TextModifier):
    """Within the file tree. Take advantage that we know it exactly.
    Be careful that when hiding one file line,
    the chain of relative positionning needs to be reconnected.
    """

    def __init__(self, input: str):
        # Refer to them as list to easily reconnect the chain.
        self._list = [FileLine(l) for l in input.split("\n")]
        lines = iter(self._list)
        # And also as individual files for random access.
        self.root = next(lines)
        self.git = next(lines)
        self.readme = next(lines)
        self.margherita = next(lines)
        self.regina = next(lines)

    def render(self) -> str:
        return "\n".join(
            m.render()
            for m in (
                self.root,
                self.git,
                self.readme,
                self.margherita,
                self.regina,
            )
        )
