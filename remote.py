"""Slide to work with a remote, 3-ways.
"""

from typing import cast

from diffs import DiffList
from document import Slide
from filetree import FileTree
from modifiers import (
    Constant,
    ConstantBuilder,
    ListBuilder,
    ListOf,
    Regex,
    render_method,
)
from repo import Command, LocalRepoLabel, RemoteArrow, RemoteRepoLabel, Repo
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
        self.my_repo = Repo(next(it), "50, 5")
        self.remote = Repo(next(it), "-5, +7")
        self.their_repo = Repo(next(it), "-50, 5")
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
        pic_github, pic_my, pic_their = cast(ListOf, step.images.list)
        my_repo = step.my_repo
        remote = step.remote.off()
        their_repo = step.their_repo.off()
        my_pointer = step.my_pointer.off()
        their_pointer = step.their_pointer.off()
        flow = step.flow.off()

        my_label = step.add_epilog(
            LocalRepoLabel("base west", "Canvas.west", "my machine")
        )
        url = step.add_epilog(RemoteRepoLabel("north", "0, 1", "MyAccount")).off()
        their_label = step.add_epilog(
            LocalRepoLabel("base east", "Canvas.east", "their machine")
        ).off()

        pic_github.off()
        pic_their.off()

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

        my_repo.populate(pizzas_repo)
        STEP()

        # Create Account.
        pic_github.on()
        STEP()

        diffs.off()
        url.on()
        STEP()

        remote.on()
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

        remote.populate(pizzas_repo)
        my_pointer.end = "remote.south west"
        flow.end = "remote.west"
        my_repo.add_remote_branch("github/main")
        STEP()

        my_command.off()
        flow.off()
        STEP()

        def hi_remote_main(on: bool):
            remote.highlight(on, "main")
            my_repo.highlight(on, "github/main")

        hi_remote_main(True)
        STEP()

        hi_remote_main(False)
        STEP()

        # Local commit: Diavola.
        diavola = step.add_epilog(
            Constant(
                r"\node (diavola) at ($(Canvas.center)!.5!(Canvas.south east)$)"
                r"      {\PicDiavola{!}{10cm}};"
            )
        )
        my_diavola = my_files.append(
            "AppendSibling", connect=True, filename="diavola.md", mod="+"
        )
        (my_readme := my_files["README.md"]).mod = "m"
        STEP()

        step.remove_from_epilog(diavola)
        my_command.on().text = "git commit"
        STEP()

        my_readme.mod = "0"
        my_diavola.mod = "0"
        new_commit = my_repo.add_commit("I", "aa0299e", "Add Diavola.")
        STEP()

        my_command.off()
        STEP()

        hi_remote_main(True)
        STEP()

        hi_remote_main(False)
        STEP()

        # Pushing new commit to remote.
        my_command.on().text = "git push github main"
        STEP()

        flow.on()
        remote.add_commit(new_commit)
        my_repo.remote_to_branch("github/main")
        hi_remote_main(True)
        STEP()

        flow.off()
        my_command.off()
        hi_remote_main(False)
        STEP()

