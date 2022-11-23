"""Slide(s) to work with a remote, 3-ways.
"""

from typing import List, cast

from diffs import DiffedFile
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
from repo import Command, RemoteArrow, RemoteRepoLabel, Repo
from steps import Step


Images = ListBuilder(ConstantBuilder, "\n", head=False, tail=True)


class RemoteStep(Step):
    def __init__(self, input: str):
        chunks = input.split("\n\n")
        it = iter(chunks)
        self.myfiles = FileTree(next(it))
        self.theirfiles = FileTree(next(it))
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
        pizzas_diffs: List[DiffedFile],
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
        pic_github, pic_my, pic_their = cast(ListOf, step.images.list)
        my_repo = step.my_repo
        remote = step.remote.off()
        their_repo = step.their_repo.off()

        url = step.add_prolog(RemoteRepoLabel("north", "0, 1", "MyAccount", "")).off()
        url._layer = "highlight"  # To not cover the highlights.

        pic_github.off()
        pic_their.off()

        my_files.populate(pizzas_files)

        my_repo.populate(pizzas_repo)
        diffs = [step.add_epilog(d.copy()) for d in pizzas_diffs]
        STEP()

        # Create Account.
        pic_github.on()
        STEP()

        [step.remove_from_epilog(d) for d in diffs]
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
        my_pointer.style = "hi"
        command.off()
        STEP()

        my_pointer.style = ""
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
        my_pointer.style = "hi"
        hi_git.on()
        STEP()

        remote.highlight(False, "main")
        my_repo.highlight(False, "github/main")
        my_pointer.style = ""
        hi_git.off()
        STEP()

        # Local commit: Diavola.
        pic = step.add_epilog(
            AnonymousPlaceHolder(
                r"\AutomaticCoordinates{c}{<location>}" + "\n"
                r"\node[anchor=<anchor>] (pizza) at (c)"
                r" {\Pic<which>{<width>}{<height>}};",
                "new",
                which="Diavola",
                location=".5, -.5",
                anchor="center",
                width="!",
                height="10cm",
            )
        )
        my_diavola = my_files.append("diavola.md", mod="+")
        (my_readme := my_files["readme"]).mod = "m"
        STEP()

        pic.off()
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

        def my_opacity(o=0.4):
            my_repo.intro.opacity = str(o)
            my_pointer._opacity = o
            my_files._opacity = o / 2 if o < 1 else o

        def their_opacity(o=0.4):
            their_repo.intro.opacity = str(o)
            their_pointer._opacity = o
            their_files._opacity = o / 2 if o < 1 else o

        pic_their.on()
        my_opacity()
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
                ".65, -.25",
                "right=5 of remote-d1e8c8c-message.south east",
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

        their_pointer.style = "hi"
        their_repo.highlight(True, "origin/main")
        hi_their_git = their_files.highlight("git")
        STEP()

        their_pointer.style = ""
        hi_their_git.off()
        their_repo.highlight(False, "origin/main")
        STEP()

        # New commit on their side: Capricciosa!
        step.bump_epilog(pic).on().which = "Capricciosa"
        pic.location = "-.5, -.5"
        their_capricciosa = their_files.append("capricciosa.md", mod="+")
        (their_readme := their_files["readme"]).mod = "m"
        STEP()

        command.on().text = "git commit"
        pic.off()
        command.location = "0, -.10"
        command.start = "left=2 of HEAD.south west"
        their_readme.mod = their_capricciosa.mod = "0"
        new_commit = their_repo.add_commit("I", "636694f", "Add Capricciosa.")
        STEP()

        command.off()
        STEP()

        command.on().text = "git push origin main"
        command.end = ".5"
        their_pointer.style = "hi"
        STEP()

        their_pointer.style = ""
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
        their_opacity()
        STEP()

        command.on().text = "git fetch github"
        command_side("left")
        my_pointer.style = "hi"
        STEP()

        my_pointer.style = ""
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

        their_opacity(1)
        SPLIT("Forking", None, "Synchronous modifications")

        for repo in (my_repo, remote, their_repo):
            repo.trim(4)
        their_repo.intro.location = ".65, -1"
        my_pointer.start = "$(mine-main.north west) + (-5, 10)$"
        remote.intro.location = ".0, .08"
        their_pointer.start = "$(theirs-main.north east) + (15, 10)$"
        their_pointer.end = "remote.south east"

        # Two diverging commits.
        pic.on().which = "Calzone"
        pic.anchor = "south west"
        pic.location = "-1, -1"
        pic.height = "12cm"
        (pic_other := step.add_epilog(pic.copy())).which = "Marinara"
        pic_other.anchor = "south east"
        pic_other.location = ".98, -1"
        STEP()

        my_calzone = my_files.append("calzone.md", mod="+")
        their_marinara = their_files.append("marinara.md", mod="+")
        my_readme.mod = "m"
        their_readme.mod = "m"
        my_readme_hi = my_files.highlight("readme")
        their_readme_hi = their_files.highlight("readme")
        my_calzone_hi = my_files.highlight("calzone")
        their_marinara_hi = their_files.highlight("marinara")
        STEP()

        pic.off()
        pic_other.off()
        STEP()

        command.aperture = "7"
        (my_command := command.on()).text = "git commit"
        their_command = step.add_epilog(command.copy())
        del command
        their_command.start = their_command.start.replace("west", "east")
        my_command.end = ".23"
        their_command.end = ".78"
        my_command.location = "-.07, -.29"
        their_command.location = "+.07, -.40"
        STEP()

        files_4 = ("my_calzone", "my_readme", "their_marinara", "their_readme")
        for f in files_4:
            eval(f).mod = "0"
            eval(f + "_hi").off()
        calzone_commit = my_repo.add_commit("I", "4ac80b2", "Add Calzone (the best).")
        marinara_commit = their_repo.add_commit("I", "0fcd744", "Add Marinara.")
        my_command.off()
        their_command.off()
        my_repo.highlight(True)
        their_repo.highlight(True)
        my_git_hi = my_files.highlight("git")
        their_git_hi = their_files.highlight("git")
        STEP()

        my_repo.highlight(False)
        their_repo.highlight(False)
        my_git_hi.off()
        their_git_hi.off()
        STEP()

        for f in files_4:
            eval(f + "_hi").on()
        STEP()

        for f in files_4:
            eval(f + "_hi").off()
        STEP()

        # Cannot both push at the same time.
        my_command.on().text = "git push github main"
        their_command.on().text = "git push origin main"
        my_command.start = "right=30 of mine-main.north east"
        their_command.start = "above=5 of theirs-HEAD.north west"
        my_command.location = "-.07, -.27"
        STEP()

        my_command.style = "error"
        their_command.style = "ok"
        STEP()

        # Their commit is pushed.
        my_command.off().style = ""
        their_pointer.style = "hi"
        their_repo.highlight(True, "main")
        remote.highlight(True, "main")
        their_flow.on().start = "$(theirs-main.north east) + (15, 23)$"
        their_flow.end = "remote.east"
        STEP()

        remote.add_commit(marinara_commit)
        STEP()

        their_command.off().style = ""
        my_command.off()
        their_flow.off()
        their_repo.highlight(False, "main")
        remote.highlight(False, "main")
        their_pointer.style = ""
        STEP()

        # My commit cannot be pushed anymore.
        my_command.on()
        my_repo.highlight(True, "main")
        remote.highlight(True, "main")
        my_pointer.style = "hi"
        STEP()

        my_command.style = "error"
        STEP()

        my_command.off().style = ""
        my_repo.highlight(False, "main")
        remote.highlight(False, "main")
        my_pointer.style = ""
        STEP()

        # Fetching their commits.
        their_opacity()
        STEP()

        my_command.on().text = "git fetch github"
        STEP()

        my_flow.on().end = "above=30 of mine-main.north west"
        my_pointer.style = "hi"
        remote.highlight(True, "main")
        my_repo.highlight(True, "github/main")
        STEP()

        my_repo.add_commit(marinara_commit, _branch="github/main")
        my_repo["4ac80b2"].type = "Y"
        my_pointer.start = "above=5 of mine-github/main.north"
        STEP()

        my_command.off()
        my_flow.off()
        my_pointer.style = ""
        remote.highlight(False, "main")
        my_repo.highlight(False, "github/main")
        STEP()

        pic.on().which = "OMG"
        pic.anchor = "center"
        pic.location = "0, -.5"
        pic.height = "9cm"
        STEP()

        # Navigating from ours to theirs and back.
        pic.off()
        STEP()

        my_readme_hi.on()
        my_calzone_hi.on()
        my_repo.highlight(True, "HEAD")
        STEP()

        my_command.on().text = "git checkout github/main"
        my_command.location = "-.0, -.35"
        STEP()

        my_repo.checkout_detached("0fcd744")
        my_files.remove(my_calzone)
        my_calzone_hi.off()
        my_marinara = my_files.append("marinara.md")
        my_marinara_hi = my_files.highlight("marinara")
        STEP()

        my_command.on().text = "git checkout main"
        my_repo.checkout_branch("main")
        my_files.remove(my_marinara)
        my_marinara_hi.off()
        my_files.append(my_calzone)
        my_calzone_hi.on()
        STEP()

        my_calzone_hi.off()
        my_readme_hi.off()
        my_command.off()
        my_repo.highlight(False, "HEAD")
        STEP()

        pic.on().which = "NowWhat"
        pic.location = ".05, -.5"
        STEP()
