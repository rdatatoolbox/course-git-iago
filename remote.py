"""Slide(s) to work with a remote, 3-ways.
"""

from typing import cast

from diffs import DiffList
from document import Slide
from filetree import FileTree
from modifiers import (
    AnonymousPlaceHolder,
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
            ]
        )


class RemoteSlide(Slide):
    def animate(
        self,
        pizzas_repo: Repo,
        pizzas_files: FileTree,
        pizzas_diffs: DiffList,
    ):

        # Use this dynamical step as a workspace for edition,
        # regularly copied into actually recorded steps.
        step = cast(RemoteStep, self.pop_step())

        # Keep a reference to the current slide, possibly changed on SPLIT.
        slide = [self]
        STEP = lambda: slide[0].add_step(step)

        def SPLIT(*args):
            slide[0] = slide[0].split(*args, step=step)

        my_files = step.myfiles
        their_files = step.theirfiles.off()
        diffs = step.diffs
        pic_github, pic_my, pic_their = cast(ListOf, step.images.list)
        my_repo = step.my_repo
        remote = step.remote.off()
        their_repo = step.their_repo.off()

        my_label = step.add_epilog(
            LocalRepoLabel("base west", "Canvas.west", "my machine")
        )
        url = step.add_epilog(RemoteRepoLabel("north", "0, 1", "MyAccount", "")).off()
        their_label = step.add_epilog(
            LocalRepoLabel("base east", "Canvas.east", "their machine")
        ).off()

        pic_github.off()
        pic_their.off()

        my_files.populate(pizzas_files)

        diffs.clear()
        for pizza_diff in pizzas_diffs.files:
            diffs.files.append(pizza_diff.copy())

        my_repo.populate(pizzas_repo)
        STEP()

        # Create Account.
        pic_github.on()
        STEP()

        diffs.off()
        url.highlight = "account"
        url.on()
        STEP()

        remote.on()
        url.name = "Pizzas"
        url.highlight = "name"
        STEP()

        # Create remote.
        url.highlight = ""
        command = step.add_epilog(Command("0, 0", "-"))

        def command_side(side: str):
            if side == "left":
                command.start = "$(command)!.35!(Canvas.south west)$"
                command.end = ".3"
            elif side == "right":
                command.start = "$(command)!.35!(Canvas.south east)$"
                command.end = ".7"
            else:
                raise ValueError(f"Pick either left or right, not {repr(side)}.")
            return command

        command_side("left")
        command.location = "0, -.20"
        command.on().text = "git remote add github <url>"
        STEP()

        my_pointer = step.add_epilog(
            RemoteArrow(
                "$($(mine-HEAD.east)!.5!(mine-main.west)$) + (6, 10)$",
                "remote-HEAD.south west",
                name="github",
                highlight="-hi",
            )
        )
        command.off()
        STEP()

        my_pointer.highlight = ""
        STEP()

        # First push
        step.bump_epilog(command)
        command.on().text = "git push github main"
        command.location = "0, -.25"
        STEP()

        my_flow = step.add_epilog(
            RemoteArrow("-.8, -.2", "remote-HEAD.west", bend="30")
        )
        remote.highlight(True, "main")
        my_repo.highlight(True, "main")
        STEP()

        remote.populate(pizzas_repo)
        my_pointer.end = "remote.south west"
        my_flow.end = "remote.west"
        my_repo.add_remote_branch("github/main")
        STEP()

        command.off()
        my_flow.off()
        remote.highlight(False, "main")
        my_repo.highlight(False, "main")
        STEP()

        remote.highlight(True, "main")
        my_repo.highlight(True, "github/main")
        my_pointer.highlight = "-hi"
        STEP()

        remote.highlight(False, "main")
        my_repo.highlight(False, "github/main")
        my_pointer.highlight = ""
        STEP()

        # Local commit: Diavola.
        pic_pizza = step.add_epilog(
            AnonymousPlaceHolder(
                r"\AutomaticCoordinates{c}{<position>}" + "\n"
                r"\node (pizza) at (c) {\Pic<pizza>{<width>}{<height>}};",
                "new",
                position=".5, -.5",
                pizza="Diavola",
                width="!",
                height="10cm",
            )
        )
        my_diavola = my_files.append(
            "AppendSibling", connect=True, filename="diavola.md", mod="+"
        )
        (my_readme := my_files["README.md"]).mod = "m"
        STEP()

        pic_pizza.off()
        command.on().text = "git commit"
        STEP()

        my_readme.mod = "0"
        my_diavola.mod = "0"
        new_commit = my_repo.add_commit("I", "aa0299e", "Add Diavola.")
        command.off()
        STEP()

        remote.highlight(True, "main")
        my_repo.highlight(True, "github/main")
        STEP()

        remote.highlight(False, "main")
        my_repo.highlight(False, "github/main")
        STEP()

        # Pushing new commit to remote.
        command.on().text = "git push github main"
        command.location = "0, -.20"
        STEP()

        my_flow.on()
        remote.add_commit(new_commit)
        my_repo.highlight(True, "main")
        remote.highlight(True, "main")
        STEP()

        my_repo.remote_to_branch("github/main")
        my_repo.highlight(False, "main")
        my_repo.highlight(True, "github/main")
        STEP()

        my_flow.off()
        command.off()
        my_repo.highlight(False, "github/main")
        remote.highlight(False, "main")
        STEP()

        pic_their.on()
        SPLIT("Collaborate", None, "Working with another person")

        # Cloning on their side.
        command_side("right")
        command.on().text = "git clone <url>"
        command.location = "0, -.15"
        STEP()

        their_flow = step.add_epilog(
            RemoteArrow("remote.center", "above=30 of theirmachine", bend="40")
        )
        their_pointer = step.add_epilog(
            RemoteArrow(
                ".6, -.25",
                "remote-d1e8c8c-message.south east",
                name="origin",
            )
        )
        their_repo.on().populate(remote)
        their_files.on()
        their_files.xy.location = ".56, 1"
        their_files.populate(my_files)
        command.start = "above=10 of HEAD.west"
        for file in their_files.list:
            file.mod = "+"
        # TODO: unecessary fix once FileTree is refreshed.
        their_files["README.md"].set_keyword_option("last", False)
        their_repo.add_remote_branch("origin/main")
        STEP()

        their_flow.off()
        command.off()
        for file in their_files.list:
            file.mod = "0"
        STEP()

        their_pointer.highlight = "-hi"
        their_repo.highlight(True, "origin/main")
        STEP()

        their_pointer.highlight = ""
        their_repo.highlight(False, "origin/main")
        STEP()

        # New commit on their side: Capricciosa!
        step.bump_epilog(pic_pizza).on().pizza = "Capricciosa"
        pic_pizza.position = "-.5, -.5"
        their_diavola = their_files.append(
            "AppendSibling", connect=True, filename="capricciosa.md", mod="+"
        )
        (their_readme := their_files["README.md"]).mod = "m"
        STEP()

        command.on().text = "git commit"
        pic_pizza.off()
        command.location = "0, -.10"
        command.start = "left=2 of HEAD.south west"
        their_readme.mod = their_diavola.mod = "0"
        new_commit = their_repo.add_commit("I", "636694f", "Add Capricciosa.")
        STEP()

        command.off()
        STEP()

        command.on().text = "git push origin main"
        command.end = ".5"
        STEP()

        f = their_flow.on()
        f.start, f.end = f.end, f.start
        f.side = "right"
        f.bend = "30"
        remote.add_commit(new_commit)
        their_pointer.start = "above=5 of origin/main.north east"
        their_repo.highlight(True, "main")
        remote.highlight(True, "main")
        their_repo.remote_to_branch("origin/main")
        STEP()

        command.off()
        their_repo.highlight(False, "main")
        remote.highlight(False, "main")
        their_flow.off()
        STEP()
