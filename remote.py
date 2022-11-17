"""Slide to work with a remote, 3-ways.
"""

from diffs import DiffList
from document import Slide
from filetree import FileTree
from modifiers import Constant, render_method
from repo import RemoteArrow, Repo
from steps import Command, IntensiveCoordinates, Step


class RemoteStep(Step):
    def __init__(self, input: str):
        chunks = input.split("\n\n")
        it = iter(chunks)
        self.myfiles = FileTree(next(it))
        self.theirfiles = FileTree(next(it))
        self.diffs = DiffList(next(it))
        self.images = Constant(next(it))
        self.my_repo = Repo(next(it))
        self.remote = Repo(next(it))
        self.their_repo = Repo(next(it))
        m, t = next(it).split("\n")
        self.my_command = Command.parse(m)
        self.their_command = Command.parse(t)
        s, e, a = next(it).split("\n")
        self.start = IntensiveCoordinates.parse(s)
        self.end = IntensiveCoordinates.parse(e)
        self.arrow = RemoteArrow.parse(a)
        try:
            while some := next(it):
                assert not some
        except StopIteration:
            pass

    @render_method
    def render(self) -> str:
        return "\n\n".join(
            m.render()
            for m in [
                self.myfiles,
                self.theirfiles,
                self.diffs,
                self.images,
                self.my_repo,
                self.remote,
                self.their_repo,
                self.my_command,
                self.their_command,
                self.start,
                self.end,
                self.arrow,
            ]
        )


class RemoteSlide(Slide):
    pass
