"""Slide to work with a remote, 3-ways.
"""

from typing import cast

from diffs import DiffList
from document import IntensiveCoordinates, Slide
from filetree import FileTree
from modifiers import (
    ConstantBuilder,
    ListBuilder,
    ListOf,
    PlaceHolder,
    Regex,
    render_method,
)
from repo import (
    Command,
    HighlightCommit,
    RemoteArrow,
    RemoteBranch,
    Repo,
    checkout_branch,
    hi_label,
    remote_to_branch,
)
from steps import Step


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
        m, t = next(it).split("\n")
        self.my_pointer = RemoteArrow.parse(m)
        self.their_pointer = RemoteArrow.parse(t)
        self.flow = RemoteArrow.parse(next(it))
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
                self.my_pointer,
                self.their_pointer,
                self.flow,
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
        my_pointer = step.my_pointer.off()
        their_pointer = step.their_pointer.off()
        flow = step.flow


        github_logo.off()
        their_machine.off()
        flow.off()

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
        _, my_main, my_head = my_repo.labels
        my_commit = step.add_epilog(HighlightCommit("mine-17514f2"))
        STEP()

        # Create Account.
        github_logo.on()
        STEP()

        remote.on()
        diffs.off()
        STEP()

        remote.on()
        remote_main = remote.labels.append(
            "$(remote) + (-5, 10)$",
            "0:0",
            "noarrow",
            "main",
        )
        remote_head = remote.labels.append("", "", "")
        remote_commit = step.add_epilog(HighlightCommit.new("remote")).off()
        checkout_branch(remote_head, remote_main, remote_commit)
        STEP()

        # Create remote.
        my_command = step.add_epilog(Command("0, 0", "-"))
        my_command.on().text = "git remote add github <url>"
        my_command.location = "0, -.25"
        STEP()

        my_pointer.on().start = "$($(mine-HEAD.east)!.5!(mine-main.west)$) + (6, 10)$"
        my_pointer.on().end = "remote-HEAD.south west"
        my_command.off()
        STEP()

        # First push
        step.bump_epilog(my_command)
        my_command.on().text = "git push github main"
        STEP()

        flow.on().start = "-.8, -.2"
        flow.end = "remote-HEAD.west"
        flow.bend = "30"
        STEP()

        account = remote.labels[0]
        remote.labels.clear()
        populate_repo(remote)
        remote.labels.append(account)
        remote_commit = step.add_epilog(HighlightCommit("remote-17514f2"))
        my_pointer.end = "remote.south west"
        my_remote_main = my_repo.labels.append(RemoteBranch("", "", "", "github/main"))
        remote_to_branch(my_remote_main, my_main)
        flow.end = "remote.west"
        STEP()

        my_command.off()
        flow.off()
        STEP()

        hi_label(my_remote_main, True)
        STEP()

        hi_label(my_remote_main, False)
        STEP()

