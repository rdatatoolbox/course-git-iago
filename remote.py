"""Slide(s) to work with a remote, 3-ways.
"""

from typing import List, cast

from diffs import DiffedFile
from document import Slide
from filetree import FileTree
from modifiers import (
    PlaceHolder,
    AnonymousPlaceHolder,
    ConstantBuilder,
    ListBuilder,
    ListOf,
    Regex,
)
from repo import Command, RemoteArrow, RemoteRepoLabel, Repo
from steps import Step


Images = ListBuilder(ConstantBuilder, "\n", head=False, tail=True)


class RemoteStep(Step):
    def parse_body(self):
        input = self.body
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

    def render_body(self) -> str:
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
        url._layer = "highlight-behind"  # To not cover the highlights.

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
        command.on().text = r"git \gkw{remote add} github <url>"
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
        command.on().text = r"git \gkw{push} github main"
        command.location = "0, -.25"
        STEP()

        my_flow = step.add_epilog(
            RemoteArrow("-.8, -.15", "left=5 of remote-HEAD.west", bend="30")
        )
        remote.hi_on("main")
        my_repo.hi_on("main")
        STEP()

        remote.hi_off("main")
        remote.populate(pizzas_repo)
        my_pointer.end = "remote.south west"
        my_flow.end = "left=5 of remote.west"
        [remote.hi_on(c) for c in remote.commits]
        my_repo.add_remote_branch("github/main")
        remote.intro.location = ".1, .07"
        STEP()

        [remote.hi_off(c) for c in remote.commits]
        my_repo.hi_off("main")
        command.off()
        my_flow.off()
        STEP()

        remote.hi_on("main")
        my_repo.hi_on("github/main")
        my_pointer.style = "hi"
        hi_git.on()
        STEP()

        remote.hi_off("main")
        my_repo.hi_off("github/main")
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
        c = my_repo.add_commit("I", "aa0299e", "Add Diavola.")
        my_repo.hi_on(c)
        command.off()
        STEP()

        my_repo.hi_off(c)
        remote.hi_on("main")
        my_repo.hi_on("github/main")
        STEP()

        remote.hi_off("main")
        my_repo.hi_off("github/main")
        STEP()

        # Pushing new commit to remote.
        command.on().text = r"git \gkw{push} github main"
        command.location = "0, -.20"
        STEP()

        my_flow.on()
        my_repo.hi_on("main")
        remote.hi_on("main")
        STEP()

        c = remote.add_commit(c.copy())
        remote.hi_on(c)
        remote.hi_off("main")
        my_repo.remote_to_branch("github/main")
        STEP()

        remote.hi_off(c)
        my_repo.hi_off("main")
        my_repo.hi_on("github/main")
        my_flow.off()
        command.off()
        STEP()

        my_repo.hi_off("github/main")
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
        SPLIT("Collaborate", "Collaborate", "You're not Alone.")

        # Cloning on their side.
        command_side("right")
        command.on().text = r"git \gkw{clone} <url>"
        command.location = "0, -.15"
        STEP()

        their_flow = step.add_epilog(
            RemoteArrow("remote.center", "above=30 of theirmachine", bend="30")
        )
        STEP()

        their_pointer = step.add_epilog(
            RemoteArrow(
                ".65, -.25",
                "right=5 of remote-d1e8c8c-message.south east",
                name="origin",
            )
        )
        their_repo.on().populate(remote)
        [their_repo.hi_on(c) for c in their_repo.commits]
        their_files.on()
        their_files.intro.location = ".54, 1"
        their_files.populate(my_files)
        command.start = "above=10 of HEAD.west"
        their_files.all_mod("+")
        their_repo.add_remote_branch("origin/main")
        STEP()

        [their_repo.hi_off(c) for c in their_repo.commits]
        their_flow.off()
        command.off()
        their_files.all_mod("0")
        STEP()

        their_pointer.style = "hi"
        their_repo.hi_on("origin/main")
        hi_their_git = their_files.highlight("git")
        STEP()

        their_pointer.style = ""
        hi_their_git.off()
        their_repo.hi_off("origin/main")
        STEP()

        my_opacity(1)
        STEP()

        step.bump_epilog(pic).on().which = "Matrix"
        pic.location = "0, 0"
        h = pic.height
        pic.height = "12cm"
        STEP()

        pic.off().height = h
        STEP()

        my_opacity()
        STEP()

        # New commit on their side: Siciliana!
        step.bump_epilog(pic).on().which = "Siciliana"
        pic.location = "-.5, -.5"
        their_siciliana = their_files.append("siciliana.md", mod="+")
        (their_readme := their_files["readme"]).mod = "m"
        STEP()

        command.on().text = "git commit"
        pic.off()
        command.location = "0, -.10"
        command.start = "left=2 of HEAD.south west"
        their_readme.mod = their_siciliana.mod = "0"
        c = their_repo.add_commit("I", "636694f", "Add Siciliana.")
        their_repo.hi_on(c)
        STEP()

        command.off()
        their_repo.hi_off(c)
        STEP()

        command.on().text = r"git push \ghi{origin} main"
        command.end = ".5"
        their_pointer.style = "hi"
        their_repo.hi_on("main")
        remote.hi_on("main")
        STEP()

        their_pointer.style = ""
        f = their_flow.on()
        f.start, f.end = f.end, f.start
        f.side = "right"
        f.bend = "20"
        c = remote.add_commit(c.copy())
        remote.hi_on(c)
        remote.hi_off("main")
        their_pointer.start = "above=5 of origin/main.north"
        their_repo.remote_to_branch("origin/main")
        STEP()

        remote.hi_off(c)
        command.off()
        their_repo.hi_off("main")
        their_flow.off()
        STEP()

        # Fetch commit.
        my_opacity(1)
        their_opacity()
        STEP()

        command.on().text = r"git \gkw{fetch} github"
        command_side("left")
        my_pointer.style = "hi"
        STEP()

        my_pointer.style = ""
        f = my_flow.on()
        f.start = f.end
        f.end = "-.8, -.1"
        f.side = "right"
        f.bend = "20"
        c = my_repo.add_commit(c.copy(), _branch="github/main")
        my_repo.hi_on(c)
        my_pointer.start = "$(mine-636694f) + (15, 25)$"
        STEP()

        my_repo.hi_off(c)
        command.off()
        my_flow.off()
        STEP()

        # Navigating to new commit and back.
        my_repo.hi_on("HEAD")
        STEP()

        command.on().text = r"git checkout \ghi{github/main}"
        my_repo.hi_on("github/main")
        STEP()

        my_repo.checkout_detached("636694f")
        (my_siciliana := my_files.append(their_siciliana.copy())).mod = "+"
        hi_siciliana = my_files.highlight("siciliana")
        my_readme.mod = "m"
        hi_readme = my_files.highlight("readme")
        STEP()

        command.on().text = r"git checkout \ghi{main}"
        hi_siciliana.off()
        my_repo.checkout_branch("main")
        my_repo.hi_off("github/main")
        my_repo.hi_on("main")
        my_files.pop(my_siciliana)
        my_readme.mod = "0"
        STEP()

        hi_readme.off()
        command.off()
        my_repo.hi_off("main")
        my_repo.hi_off("HEAD")
        STEP()

        # Merging commit.
        command.on().text = r"git \gkw{merge} github/main"
        my_repo.hi_on("main")
        STEP()

        my_repo.move_branch("main", c.hash)
        my_repo.checkout_branch("main")
        my_repo.remote_to_branch("github/main")
        my_files.append(my_siciliana).mod = "+"
        my_readme.mod = "m"
        STEP()

        command.off()
        hi_readme.off()
        my_readme.mod = "0"
        my_siciliana.mod = "0"
        my_repo.hi_off("main")
        STEP()

        their_opacity(1)
        SPLIT("Forking", None, "When you Diverge")

        for repo in (my_repo, remote, their_repo):
            repo.fade_commits(1, 4)
        STEP()

        for repo in (my_repo, remote, their_repo):
            repo.trim(4)
        their_repo.intro.location = ".40, -1"
        their_repo.intro.anchor = "south west"
        my_pointer.start = "$(mine-main.north west) + (-5, 10)$"
        remote.intro.location = ".0, .08"
        their_pointer.start = "$(theirs-main.north east) + (5, 10)$"
        their_pointer.end = "remote.south east"
        STEP()

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
        c_calzone = my_repo.add_commit("I", "4ac80b2", "Add Calzone (the best).")
        c_marinara = their_repo.add_commit("I", "0fcd744", "Add Marinara.")
        my_repo.hi_on(c_calzone)
        their_repo.hi_on(c_marinara)
        my_command.off()
        their_command.off()
        my_git_hi = my_files.highlight("git")
        their_git_hi = their_files.highlight("git")
        STEP()

        my_git_hi.off()
        their_git_hi.off()
        my_repo.hi_off(c_calzone)
        their_repo.hi_off(c_marinara)
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
        my_command.location = "-.07, -.28"
        STEP()

        my_command.style = "error"
        their_command.style = "ok"
        STEP()

        # Their commit is pushed.
        my_command.off().style = ""
        their_pointer.style = "hi"
        their_repo.hi_on("main")
        remote.hi_on("main")
        their_flow.on().start = "$(theirs-main.north east) + (10, 20)$"
        their_flow.end = "remote.east"
        STEP()

        c_marinara = remote.add_commit(c_marinara.copy())
        their_repo.remote_to_branch("origin/main")
        remote.hi_on(c_marinara)
        their_repo.hi_off("main")
        remote.hi_off("main")
        STEP()

        remote.hi_off(c_marinara)
        their_command.off().style = ""
        my_command.off()
        their_flow.off()
        their_pointer.style = ""
        STEP()

        # My commit cannot be pushed anymore.
        my_command.on()
        my_command.location = ".0, -.35"
        my_command.end = ".1"
        my_repo.hi_on("main")
        remote.hi_on("main")
        my_pointer.style = "hi"
        STEP()

        my_command.style = "error"
        STEP()

        my_command.off().style = ""
        my_repo.hi_off("main")
        remote.hi_off("main")
        my_pointer.style = ""
        STEP()

        # Fetching their commits.
        their_opacity()
        STEP()

        my_command.on().text = r"git \gkw{fetch} github"
        STEP()

        my_flow.on().end = "$(mine-4ac80b2-hash.north east) + (15, 40)$"
        my_flow.bend = "25"
        my_pointer.style = "hi"
        remote.hi_on("main")
        my_repo.hi_on("github/main")
        STEP()

        c_marinara = my_repo.add_commit(c_marinara.copy(), _branch="github/main")
        my_repo.hi_on(c_marinara)
        my_repo["4ac80b2"].type = "Y"
        my_pointer.start = "above=5 of mine-github/main.north"
        remote.hi_off("main")
        my_repo.hi_off("github/main")
        my_pointer.style = ""
        STEP()

        my_repo.hi_off(c_marinara)
        my_command.off()
        my_flow.off()
        STEP()

        pic.on().which = "OMG"
        pic.anchor = "center"
        pic.location = "+.02, -.5"
        pic.height = "9cm"
        STEP()

        # Navigating from ours to theirs and back.
        pic.off()
        STEP()

        my_readme_hi.on()
        my_calzone_hi.on()
        my_repo.hi_on("HEAD")
        STEP()

        my_command.on().text = r"git checkout \ghi{github/main}"
        my_command.location = "-.0, -.35"
        STEP()

        my_repo.checkout_detached("0fcd744")
        my_files.pop(my_calzone)
        my_calzone_hi.off()
        my_marinara = my_files.append("marinara.md")
        my_marinara_hi = my_files.highlight("marinara")
        STEP()

        my_command.on().text = r"git checkout \ghi{main}"
        my_repo.checkout_branch("main")
        my_files.pop(my_marinara)
        my_marinara_hi.off()
        my_files.append(my_calzone)
        my_calzone_hi.on()
        STEP()

        my_calzone_hi.off()
        my_readme_hi.off()
        my_command.off()
        my_repo.hi_off("HEAD")
        STEP()

        my_command.on().text = "git push github main"
        my_command.style = "error"
        STEP()

        my_command.off().style = ""
        STEP()

        pic.on().which = "NowWhat"
        pic.location = ".05, -.5"
        STEP()

        # Focus on current repo to illustrate merge and rebase.
        for m in (
            my_files,
            their_files,
            my_repo,
            remote,
            their_repo,
            my_pointer,
            their_pointer,
            url,
            pic,
            pic_my,
            pic_github,
            pic_their,
        ):
            m.off()
        left = step.add_prolog(my_repo.copy()).on()
        left.intro.name = "left"
        left.intro.location = "-.9, -.9"
        left.intro.alignment = "double"
        left.left_labels.add("github/main")
        SPLIT("Merging", "Merge and Rebase", "Two Git Philosophies")

        merge_title = step.add_prolog(
            AnonymousPlaceHolder(
                r"""
                \AutomaticCoordinates{c}{<location>}
                \node[scale=4, Dark3] at (c)
                    {\textcolor{Purple3}{\textbf{<text>}} strategy};
                """,
                "new",
                location="-.5, .8",
                text=r"Merge",
            )
        )
        STEP()

        rebase_title = step.add_prolog(merge_title.copy())
        rebase_title.location = "+.5, .8"
        rebase_title.text = "Rebase"
        right = step.add_prolog(left.copy())
        right.intro.name = "right"
        right.intro.location = "+.1, -.9"
        STEP()

        # Merge.
        left_command = step.add_epilog(my_command.copy()).on()
        (l := left_command).text = r"git \gkw{merge} \ghi{github/main}"
        l.start, l.end, l.aperture = "-.40, -.15", ".3", "6"
        l.location = ".0, .2"
        left_safe = left.copy()
        left.hi_on("HEAD")
        STEP()

        left.add_commit("A", "007e53f", "Merge github/main into main.")
        left.hi_on("007e53f")
        left.hi_off("HEAD")
        STEP()

        left_command.off()
        left.hi_off("007e53f")
        STEP()

        # Rebase
        right_command = step.add_epilog(left_command.copy()).on()
        (r := right_command).text = r"git \gkw{rebase} \ghi{github/main}"
        r.start, r.end, r.aperture = ".20, -.15", ".55", "5"
        right_safe = right.copy()
        right.hi_on("HEAD")
        STEP()

        a = right.fade_commit("4ac80b2")
        b = right.add_commit("I", "a136a71", a.message)
        [right.hi_on(c.hash) for c in (a, b)]
        right.hi_off("HEAD")
        STEP()

        right_command.off()
        [right.hi_off(c.hash) for c in (a, b)]
        STEP()

        right.commits.list.pop(2)  # Surgery-cleanup. (UNSTABLE)
        right.labels.pop(2)
        STEP()

        # Rewind.
        merged_safe = left.copy()
        rebased_safe = right.copy()
        message = step.add_epilog(
            AnonymousPlaceHolder(
                r"""
                \AutomaticCoordinates{c}{<location>}
                \node[scale=3, Dark3] at (c) {\bf <text>};
                """,
                "new",
                location="0, .4",
                text="Wait, do this again.",
            )
        )
        STEP()

        step.remove_from_prolog(left)
        left = step.add_prolog(left_safe)
        step.remove_from_prolog(right)
        right = step.add_prolog(right_safe)
        for m in (message, merge_title, rebase_title):
            m.off()
        right.off()
        STEP()

        # Fetching one new commit.
        left_command.on().text = "git fetch"
        left_command.start = ""
        both = (left, right)
        c = None
        for r in both:
            c = r.add_commit("I", "9549b2a", "Add Napoletana.", _branch="github/main")
        c = cast(PlaceHolder, c)
        left.hi_on(c.hash)
        STEP()

        # Producing one new commit.
        left.hi_off("9549b2a")
        left_command.text = "git commit"
        for r in (left, right):
            c = r.add_commit("H", "8dd46ef", "Surprise pizza.")
            # Swap for better rendering: UNSTABLE SURGERY AT PLAY.
            r.commits.list.insert(3, r.commits.list.pop())
            r.labels.insert(3, r.labels.pop())
        left.hi_on(c.hash)
        STEP()

        left.hi_off(c.hash)
        left_command.off()
        STEP()

        merge_title.on()
        STEP()

        rebase_title.on()
        right.on()
        STEP()

        # Merge 4 commits.
        left_command.on().text = r"git \gkw{merge} \ghi{github/main}"
        left_command.location = ".0, .35"
        left_command.start = "-.35, 0"
        left.hi_on("HEAD")
        STEP()

        c = left.add_commit("A", "cbcce18", "Merge github/main into main.")
        left.hi_off()
        left.hi_off("HEAD")
        STEP()

        left.hi_off(c.hash)
        left_command.off()
        STEP()

        # Rebase 2 commits.
        right_command.on().text = r"git \gkw{rebase} \ghi{github/main}"
        right_command.location = left_command.location
        right_command.end = ".6"
        right_command.start = ".18, 0"
        right.hi_on("HEAD")
        STEP()

        a = right.fade_commit(right["4ac80b2"])
        b = right.fade_commit(right["8dd46ef"])
        c = right.add_commit("I", "a03a2bb", a.message)
        [right.hi_on(k.hash) for k in (a, c)]
        right.hi_off("HEAD")
        STEP()

        [right.hi_off(k.hash) for k in (a, c)]
        c = right.add_commit("I", "4a6ebf4", b.message)
        [right.hi_on(k.hash) for k in (b, c)]
        right.hi_on(c.hash)
        STEP()

        [right.hi_off(k.hash) for k in (b, c)]
        right_command.off()
        STEP()

        right.commits.list.pop(2)  # Surgery-cleanup. (UNSTABLE)
        right.commits.list.pop(2)
        right.labels.pop(2)
        right.labels.pop(2)
        STEP()

        # Now back to our three-way repos to propagate the merge.
        for m in (left, right, merge_title, rebase_title):
            m.off()
        for m in (
            my_repo,
            remote,
            my_pointer,
            their_pointer,
            their_repo,
            my_files,
            their_files,
            pic_my,
            pic_github,
            pic_their,
            url,
        ):
            m.on()
        repos_safe = []
        for r in (my_repo, remote, their_repo):
            r.intro.alignment = "double"
            r.intro.anchor = "base"
            repos_safe.append(r.copy())
        my_repo.left_labels.add("github/main")
        my_repo.intro.location = "-.60, -.95"
        my_pointer.start = "-.6, -.4"
        remote.intro.location = "0, .1"
        their_repo.intro.location = "+.52875, -.95"
        their_pointer.start = ".75, -.4"
        their_pointer.end = ".25, .1"
        SPLIT("PropagateMerge", "Share integrated work", "(Merge style)")

        # Merge.
        (mc := my_command).on().text = r"git \gkw{merge} github/main"
        mc.location, mc.start, mc.end = "0, -.2", "-.3, -.5", ".3"
        my_pointer.start = "-.6, -.2"
        c = my_repo.add_commit("A", "5d3fd0b", "Merge commit.")
        my_repo.hi_on(c)
        my_files.append(my_marinara)
        [m.on() for m in (my_marinara_hi, my_calzone_hi, my_readme_hi)]
        STEP()

        my_repo.hi_off(c)
        my_command.off()
        [m.off() for m in (my_marinara_hi, my_calzone_hi, my_readme_hi)]
        STEP()

        # Push merge commit to remote.
        my_command.on().text = "git push github main"
        (mf := my_flow).on()
        mf.start, mf.end = "-.70, -.2", mf.start
        mf.side = "left"
        remote.clear().populate(my_repo)
        my_repo.remote_to_branch("github/main")
        my_repo.left_labels.remove("github/main")
        [remote.hi_on(h) for h in ["4ac80b2", "5d3fd0b"]]
        # Why would the bases not stick? :(
        remote.intro.location = ".0875, .1"
        my_repo.intro.location = "-.5475, -.95"
        STEP()

        my_command.off()
        my_flow.off()
        [remote.hi_off(h) for h in ["4ac80b2", "5d3fd0b"]]
        STEP()

        # Pull merge commit on their side.
        their_opacity(1)
        (tc := their_command).on().text = r"git \gkw{pull} origin main"
        tc.location = my_command.location
        tc.start, tc.end = "$(theirs.west) + (-5, 5)$", ".6"
        (tf := their_flow).on()
        tf.start, tf.end = "remote.east", ".75 ,-.2"
        tf.side = "left"
        their_repo.clear().populate(remote)
        their_repo.add_remote_branch("origin/main")
        [their_repo.hi_on(h) for h in ["4ac80b2", "5d3fd0b"]]
        their_pointer.start = ".70, -.25"
        their_calzone = their_files.append(my_calzone)
        their_calzone_hi = their_files.highlight("calzone")
        [m.on() for m in (their_marinara_hi, their_calzone_hi, their_readme_hi)]
        # Why would the bases not stick either? :(
        their_repo.intro.location = "+.60, -.95"
        STEP()

        [m.off() for m in (their_marinara_hi, their_calzone_hi, their_readme_hi)]
        [their_repo.hi_off(h) for h in ["4ac80b2", "5d3fd0b"]]
        their_flow.off()
        their_command.off()
        STEP()

        files_6 = files_4 + ("my_marinara", "their_calzone")
        for f in files_6:
            eval(f + "_hi").on()
        STEP()

        for f in files_6:
            eval(f + "_hi").off()
        STEP()

        # Same with rebase instead.
        for r, s in zip((my_repo, remote, their_repo), repos_safe):
            r.intro.alignment = "double"
            r.intro.anchor = "base"
            r.intro.alignment = "mixed"
            r.clear().populate(s)
        their_opacity()
        my_repo.add_remote_branch('github/main')
        my_repo.move_branch('main', '4ac80b2')
        their_repo.add_remote_branch('origin/main')
        my_files.pop('marinara')
        their_files.pop('calzone')
        my_repo.intro.location = "-.60, -.95"
        my_pointer.start = "-.6, -.35"
        remote.intro.location = "0, .1"
        their_repo.intro.location = "+.5495, -.95"
        their_pointer.start = ".75, -.4"
        their_pointer.end = ".25, .1"
        SPLIT("PropagateRebase", "Share integrated work", "(Rebase style)")

        # Rebase.
        (mc := my_command).on().text = r"git \gkw{rebase} github/main"
        mc.start, mc.end = "-.25, -.5", ".4"
        c = my_repo['4ac80b2']
        my_repo.fade_commit(c)
        my_repo.hi_on(c)
        c = my_repo.add_commit("I", "394e864", c.message)
        my_repo.hi_on(c)
        my_pointer.start = "above=5 of mine-main.north"
        my_files.append(my_marinara)
        [m.on() for m in (my_marinara_hi, my_calzone_hi, my_readme_hi)]
        STEP()

        my_repo.commits.list.pop(2)
        my_repo.labels.pop(2)
        my_pointer.start = "above=10 of mine-main.north"
        # Why would the bases not stick? :(
        my_repo.intro.location = "-.6205, -.95"
        STEP()

        my_repo.hi_off(c)
        my_command.off()
        [m.off() for m in (my_marinara_hi, my_calzone_hi, my_readme_hi)]
        STEP()

        # Push rebased commit to remote.
        my_command.on().text = "git push github main"
        my_flow.on()
        c = remote.add_commit(c.copy())
        remote.hi_on(c)
        my_repo.remote_to_branch("github/main")
        # Why would the bases not stick? :(
        remote.intro.location = ".0875, .1"
        STEP()

        # Pull rebased commit on their side.
        remote.hi_off(c)
        their_opacity(1)
        my_command.off()
        my_flow.off()
        their_command.on().text = r"git \gkw{pull} origin main"
        their_flow.on()
        their_pointer.start = '.7, -.35'
        c = their_repo.add_commit(c.copy())
        their_repo.hi_on(c)
        their_repo.remote_to_branch('origin/main')
        their_calzone = their_files.append(my_calzone)
        their_calzone_hi = their_files.highlight("calzone")
        [m.on() for m in (their_marinara_hi, their_calzone_hi, their_readme_hi)]
        # Why would the bases not stick either? :(
        their_repo.intro.location = "+.60, -.95"
        STEP()

        [m.off() for m in (their_marinara_hi, their_calzone_hi, their_readme_hi)]
        their_repo.hi_off(c)
        their_flow.off()
        their_command.off()
        STEP()

        for f in files_6:
            eval(f + "_hi").on()
        STEP()

        for f in files_6:
            eval(f + "_hi").off()
        STEP()

