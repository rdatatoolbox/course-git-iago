"""Slide(s) to work with a remote, 3-ways.
"""

from typing import cast

from diffs import DiffList
from document import HighlightSquare, Slide
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
        self.my_repo = Repo(next(it))
        self.remote = Repo(next(it))
        self.their_repo = Repo(next(it))
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

        url = step.add_prolog(RemoteRepoLabel("north", "0, 1", "MyAccount", "")).off()
        url._layer = "highlight"  # To not cover the highlights.

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
        remote.intro.location = ".0, .15"
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
        hi_git = my_files.highlight("git")
        command.off()
        STEP()

        my_pointer.highlight = ""
        hi_git.off()
        STEP()

        # First push
        step.bump_epilog(command)
        command.on().text = "git push github main"
        command.location = "0, -.25"
        STEP()

        my_flow = step.add_epilog(
            RemoteArrow("-.8, -.15", "left=5 of remote-HEAD.west", bend="30")
        )
        remote.highlight(True, "main")
        my_repo.highlight(True, "main")
        STEP()

        remote.populate(pizzas_repo)
        my_pointer.end = "remote.south west"
        my_flow.end = "left=5 of remote.west"
        my_repo.add_remote_branch("github/main")
        remote.intro.location = ".1, .08"
        STEP()

        command.off()
        my_flow.off()
        remote.highlight(False, "main")
        my_repo.highlight(False, "main")
        STEP()

        remote.highlight(True, "main")
        my_repo.highlight(True, "github/main")
        my_pointer.highlight = "-hi"
        hi_git.on()
        STEP()

        remote.highlight(False, "main")
        my_repo.highlight(False, "github/main")
        my_pointer.highlight = ""
        hi_git.off()
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
        my_diavola = my_files.append("diavola.md", mod="+")
        (my_readme := my_files["readme"]).mod = "m"
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

        def my_opacity(o: float):
            my_repo.intro.opacity = str(o)
            my_pointer._opacity = o
            my_files._opacity = o / 2 if o < 1 else o

        def their_opacity(o: float):
            their_repo.intro.opacity = str(o)
            their_pointer._opacity = o
            their_files._opacity = o / 2 if o < 1 else o

        pic_their.on()
        my_opacity(0.4)
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
        their_files.intro.location = ".56, 1"
        their_files.populate(my_files)
        command.start = "above=10 of HEAD.west"
        their_files.all_mod("+")
        their_repo.add_remote_branch("origin/main")
        STEP()

        their_flow.off()
        command.off()
        their_files.all_mod("0")
        STEP()

        their_pointer.highlight = "-hi"
        their_repo.highlight(True, "origin/main")
        hi_their_git = their_files.highlight("git")
        STEP()

        their_pointer.highlight = ""
        hi_their_git.off()
        their_repo.highlight(False, "origin/main")
        STEP()

        # New commit on their side: Capricciosa!
        step.bump_epilog(pic_pizza).on().pizza = "Capricciosa"
        pic_pizza.position = "-.5, -.5"
        their_capricciosa = their_files.append("capricciosa.md", mod="+")
        (their_readme := their_files["readme"]).mod = "m"
        STEP()

        command.on().text = "git commit"
        pic_pizza.off()
        command.location = "0, -.10"
        command.start = "left=2 of HEAD.south west"
        their_readme.mod = their_capricciosa.mod = "0"
        new_commit = their_repo.add_commit("I", "636694f", "Add Capricciosa.")
        STEP()

        command.off()
        STEP()

        command.on().text = "git push origin main"
        command.end = ".5"
        their_pointer.highlight = "-hi"
        STEP()

        their_pointer.highlight = ""
        f = their_flow.on()
        f.start, f.end = f.end, f.start
        f.side = "right"
        f.bend = "30"
        remote.add_commit(new_commit.copy())
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

        # Fetch commit.
        my_opacity(1)
        their_opacity(0.4)
        STEP()

        command.on().text = "git fetch github"
        command_side("left")
        my_pointer.highlight = "-hi"
        STEP()

        my_pointer.highlight = ""
        f = my_flow.on()
        f.start = f.end
        f.end = "-.8, -.1"
        f.side = "right"
        f.bend = "30"
        my_repo.add_commit(new_commit.copy(), _branch="github/main")
        my_repo.highlight(True, "github/main")
        remote.highlight(True, "main")
        my_pointer.start = "-.6, -.1"
        STEP()

        my_repo.highlight(False, "github/main")
        remote.highlight(False, "main")
        command.off()
        my_flow.off()
        STEP()

        command.on().text = "git merge github/main"
        my_repo.highlight(True, "main")
        STEP()

        my_repo.move_branch("main", new_commit.hash)
        my_repo.checkout_branch("main")
        my_repo.remote_to_branch("github/main")
        my_readme.mod = "m"
        (my_capricciosa := my_files.append(their_capricciosa.copy())).mod = "+"
        hi_readme = my_files.highlight("readme")
        hi_capricciosa = my_files.highlight("capricciosa")
        STEP()

        command.off()
        hi_readme.off()
        hi_capricciosa.off()
        my_readme.mod = "0"
        my_capricciosa.mod = "0"
        my_repo.highlight(False, "main")
        STEP()

        for repo in (my_repo, remote, their_repo):
            repo.trim(4)
        my_pointer.start = "above=30 of mine-636694f"
        remote.intro.location = ".0, .08"
        their_opacity(1)
        their_pointer.start = "$(theirs-main.north east) + (15, 10)$"
        their_pointer.end = "remote.south east"
        SPLIT("Forking", None, "When we both work at the same time")

        # HERE: debug the two new pizzas.
        pic_pizza.on().pizza = "Calzone"
        (pic_other := step.add_epilog(pic_pizza.copy())).pizza = "Marinara"
        pic_other.position = ".5, -.5"
        STEP()
