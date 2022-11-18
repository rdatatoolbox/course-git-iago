"""Slide to work with a remote, 3-ways.
"""

from typing import cast

from diffs import DiffList
from document import Slide
from filetree import FileTree
from modifiers import (
    ConstantBuilder,
    ListBuilder,
    ListOf,
    PlaceHolder,
    Regex,
    render_method,
)
from repo import RemoteArrow, Repo
from steps import Command, IntensiveCoordinates, Step


Images = ListBuilder(ConstantBuilder, "\n", head=False, tail=True)


class RemoteStep(Step):
    def __init__(self, input: str):
        chunks = input.split("\n\n")
        it = iter(chunks)
        self.myfiles = FileTree(next(it))
        self.theirfiles = FileTree(next(it))
        self.diffs = DiffList(next(it))
        self.images = Regex(
            next(it), r"\s*\\begin.*?\n(.*)\\end.*", "list", list=Images
        )
        self.my_repo = Repo(next(it))
        self.remote = Repo(next(it))
        self.their_repo = Repo(next(it))
        s, e, a = next(it).split("\n")
        self.start = IntensiveCoordinates.parse(s)
        self.end = IntensiveCoordinates.parse(e)
        self.arrow = RemoteArrow.parse(a)
        m, t = next(it).split("\n")
        self.my_command = Command.parse(m)
        self.their_command = Command.parse(t)
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
    def animate(self, pizzas_repo: Repo, pizzas_ft: FileTree, pizzas_df: DiffList):
        step = cast(RemoteStep, self.pop_step())
        STEP = lambda: self.add_step(step)

        my_files = step.myfiles
        their_files = step.theirfiles
        diffs = step.diffs
        github_logo, my_machine, their_machine = cast(ListOf, step.images.list)
        my_repo = step.my_repo
        remote = step.remote
        their_repo = step.their_repo
        my_command = step.my_command
        their_command = step.their_command
        start = step.start
        end = step.end
        _arrow = step.arrow

        def arrow(on: bool) -> PlaceHolder:
            start.on(on)
            end.on(on)
            return _arrow.on(on)

        github_logo.off()
        their_machine.off()
        my_command.off()
        their_command.off()
        arrow(False)

        # Populate situations from the pizza slide.
        def populate_repo(rp: Repo):
            rp.commits.clear()
            for commit in pizzas_repo.commits:
                rp.commits.list.append(commit.copy())
            for label in pizzas_repo.labels:
                rp.labels.list.append(label.copy())

        my_repo.commits.clear()
        populate_repo(their_repo)
        remote.commits.clear()
        their_repo.off()
        remote.off()

        def populate_folder(ft: FileTree):
            ft.clear()
            for fileline in pizzas_ft.list:
                ft.list.append(fileline.copy())

        populate_folder(my_files)
        populate_folder(their_files)
        their_files.off()

        diffs.clear()
        for pizza_diff in pizzas_df.files:
            diffs.files.append(pizza_diff.copy())

        STEP()

        populate_repo(my_repo)
        STEP()

        github_logo.on()
        STEP()

        remote.on()
        diffs.off()
        STEP()

        my_command.anchor = "center"
        my_command.loc = "0, 0"
        my_command.on().text = "git remote add github <url>"
        STEP()
