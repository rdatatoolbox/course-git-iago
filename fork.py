"""Slide to work with a fork, 4-ways.
"""

from diffs import DiffList
from document import Slide
from filetree import FileTree
from modifiers import Constant, Regex, render_method
from repo import Command, RemoteArrow, Repo
from steps import Step


class ForkStep(Step):
    def __init__(self, input: str):
        chunks = input.split("\n\n")
        it = iter(chunks)
        self.files = FileTree(next(it))
        self.diffs = DiffList(next(it))
        self.images = Constant(next(it))
        self.my_repo = Repo(next(it), "50, 5")
        self.remote = Repo(next(it), "-10, -15")
        self.fork = Repo(next(it), "10, -15")
        self.their_repo = Repo(next(it), "-50, 5")
        m, t, r = next(it).split("\n")
        self.my_command = Command.parse(m)
        self.their_command = Command.parse(t)
        self.remote_command = Command.parse(r)
        self.flow = RemoteArrow.parse(next(it))
        self.button = Regex(next(it).strip(), r"\\node.*{(.*?)}", "filename")
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
                self.files,
                self.diffs,
                self.images,
                self.my_repo,
                self.remote,
                self.fork,
                self.their_repo,
                self.my_command,
                self.their_command,
                self.remote_command,
                self.flow,
                self.button,
            ]
        )


class ForkSlide(Slide):
    pass
