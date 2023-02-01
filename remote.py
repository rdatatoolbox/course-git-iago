"""Slide(s) to work with a remote, 3-ways.
"""

from typing import List, cast

from diffs import DiffedFile
from document import Slide
from filetree import FileTree
from modifiers import (AnonymousPlaceHolder, Constant, ConstantBuilder,
                       ListBuilder, ListOf, PlaceHolder, Regex)
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
        pizzas_diffs: List[DiffedFile | Constant],
    ):

        # Use this dynamical step as a workspace for edition,
        # regularly copied into actually recorded steps.
        step = cast(RemoteStep, self.pop_step())

        # Keep a reference to the current slide, possibly changed on SPLIT.
        slide = [self]
        STEP = lambda: slide[0].add_step(step)

        def SPLIT(*args):
            slide[0] = slide[0].split(*args, step=step)

        website = "gitlab"  # (previously 'github')

        my_files = step.myfiles
        their_files = step.theirfiles.off()
        pic_website, pic_my, pic_their = cast(ListOf, step.images.list)
        my_repo = step.my_repo
        remote = step.remote.off()
        their_repo = step.their_repo.off()

        # Initial location of the repos.
        # Change on split to adjust branches going offscreen, if any.
        y_down_repos = ", -.94"
        y_up_repos = ", +.1"
        my_repo.intro.location = "-.82" + y_down_repos
        remote.intro.location = "-.2" + y_up_repos
        their_repo.intro.location = ".28" + y_down_repos

        url = step.add_prolog(RemoteRepoLabel("north", "0, 1", "MyAccount", "")).off()
        url._layer = "highlight-behind"  # To not cover the highlights.

        pic_website.off()
        pic_their.off()

        my_files.populate(pizzas_files)

        my_repo.populate(pizzas_repo)
        diffs = [step.add_epilog(d.copy()) for d in pizzas_diffs]
        STEP()

        # Create Account.
        pic_website.on()
        STEP()

        [step.remove_from_epilog(d) for d in diffs]
        url.highlight = "account"
        url.on()
        STEP()

        remote_location_safe = remote.intro.location
        remote.on().intro.location = ".10" + y_up_repos
        url.name = "Pizzas"
        url.highlight = "name"
        STEP()

        # Create remote.
        url.highlight = ""
        command = step.add_epilog(Command("0, 0", "-"))

        def command_side(side: str, crit=0.35):
            if side == "left":
                command.start = f"$(command)!{crit}!(Canvas.south west)$"
                command.end = ".3"
            elif side == "right":
                command.start = f"$(command)!{crit}!(Canvas.south east)$"
                command.end = ".7"
            else:
                raise ValueError(f"Pick either left or right, not {repr(side)}.")
            return command

        command_side("left")
        command.location = "0, -.20"
        command.on().text = rf"git \gkw{{remote add}} \ghi{{{website}}} <url>"
        STEP()

        my_pointer = step.add_epilog(
            RemoteArrow(
                "above right=25 and 10 of mine-last.east",
                "remote-HEAD.south west",
                name=website,
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

        # First push.
        command.on().text = rf"git \gkw{{push}} {website} main"
        command.location = "0, -.25"
        STEP()

        command.on().text = rf"git \gkw{{push}} \ghi{{{website}}} main"
        my_pointer.style = "hi"
        STEP()
        my_pointer.style = ""

        my_flow = step.add_epilog(
            RemoteArrow(
                "$(mine-HEAD.north east) + (5, 10)$",
                "left=5 of remote-HEAD.west",
                bend="30",
            )
        )
        command.on().text = rf"git \gkw{{push}} {website} \ghi{{main}}"
        remote.hi_on("main")
        my_repo.hi_on("main")
        STEP()

        remote.populate(pizzas_repo)
        remote.intro.location = remote_location_safe
        my_flow.end = "left=5 of remote-2-hash.north west"
        my_pointer.end = "above left=4 and 5 of remote-1-hash.south west"
        [remote.hi_on(c) for c in remote.commits]
        web_main = f"{website}/main"
        my_repo.add_remote_branch(web_main)
        STEP()

        [remote.hi_off(c) for c in remote.commits]
        remote.hi_off("main")
        my_repo.hi_off("main")
        command.off()
        my_flow.off()
        STEP()

        remote.hi_on("main")
        my_repo.hi_on(web_main)
        my_pointer.style = "hi"
        hi_git.on()
        STEP()

        remote.hi_off("main")
        my_repo.hi_off(web_main)
        my_pointer.style = ""
        hi_git.off()
        STEP()

        # Not alone.
        pic = step.add_epilog(
            AnonymousPlaceHolder(
                r"\AutomaticCoordinates{c}{<location>}" + "\n"
                r"\node[anchor=<anchor>] (pizza) at (c)"
                r" {\Pic<which>{<width>}{<height>}};",
                "new",
                which="NotAlone",
                location=".5, -.55",
                anchor="center",
                width="!",
                height="10cm",
            )
        )
        STEP()

        SPLIT("NotAlone", "Maintain Your Project", "You're Not Alone.")

        remote.hi_on("main")
        STEP()

        # Protect main branch.
        remote.lock_branch("main")
        STEP()

        remote.hi_off("main")
        STEP()

        # New pizza: Diavola.
        pic.which = "Diavola"
        my_diavola = my_files.append("diavola.md", mod="+")
        (my_readme := my_files["readme"]).mod = "m"
        STEP()

        pic.which = "NotAlone"
        STEP()

        # Create dedicated branch.
        command.on().text = r"git \gkw{branch} dev"
        command.location = "0, -.08"
        command_side("left", 0.25)
        STEP()

        my_repo.add_branch("dev", "17514f2")
        my_repo.hi_on("dev")
        STEP()

        command.off()
        my_repo.hi_off("dev")
        STEP()

        command.on().text = r"git checkout \ghi{dev}"
        my_repo.hi_on("dev")
        my_repo.hi_on("HEAD")
        STEP()

        my_repo.checkout_branch("dev")
        STEP()

        my_repo.hi_off("dev")
        my_repo.hi_off("HEAD")
        command.off()
        STEP()

        # New local commit.
        command.on().text = "git commit"
        STEP()

        my_readme.mod = "0"
        my_diavola.mod = "0"
        c = my_repo.add_commit("I", "aa0299e", "Add Diavola.")
        my_repo.hi_on(c)
        command.off()
        STEP()

        my_repo.hi_off(c)
        STEP()

        remote.hi_on("main")
        my_repo.hi_on(web_main)
        STEP()

        remote.hi_off("main")
        my_repo.hi_off(web_main)
        STEP()

        # Pushing new commit to remote.
        command.on().text = rf"git \gkw{{push}} {website} \ghi{{dev}}"
        STEP()

        my_flow.on()
        my_repo.hi_on("dev")
        STEP()
        my_repo.hi_off("dev")

        remote.add_branch("dev", "17514f2")
        # Fake on remote, because HEAD remains pointed to main.
        remote.checkout_branch("dev")
        c = remote.add_commit(c.copy())
        remote.checkout_branch("main")
        remote.hi_on(["dev", c])
        web_dev = f"{website}/dev"
        my_repo.add_remote_branch(web_dev)
        STEP()
        remote.hi_off(["dev", c])

        my_flow.off()
        command.off()
        STEP()

        my_repo.hi_on(web_dev)
        remote.hi_on("dev")
        STEP()

        my_repo.hi_off(web_dev)
        remote.hi_off("dev")
        STEP()

        # Stepping `main` forward.
        command.on().text = r"git checkout \ghi{main}"
        my_repo.hi_on(["HEAD", "main"])
        STEP()
        my_repo.hi_off(["HEAD", "main"])

        my_repo.checkout_branch("main")
        my_files.pop(my_diavola)
        STEP()

        command.off()
        STEP()

        command.on().text = r"git \gkw{merge} dev"
        my_repo.hi_on(["HEAD", "dev"])
        STEP()
        my_repo.hi_off(["HEAD", "dev"])

        my_repo.move_branch("main", c.hash)
        my_files.append(my_diavola)
        my_repo.hi_on("main")
        STEP()
        my_repo.hi_off("main")

        command.off()
        STEP()

        my_repo.hi_on(web_main)
        remote.hi_on("main")
        STEP()

        my_repo.hi_off(web_main)
        remote.hi_off("main")
        STEP()

        # Pushing main to remote.
        command.on().text = rf"git push {website} \ghi{{main}}"
        command_side("left", 0.20)
        remote.hi_on("main")
        my_flow.on()
        my_repo.hi_on("main")
        STEP()
        my_repo.hi_off("main")

        remote.move_branch("main", c.hash)
        my_repo.remote_to_branch(web_main)
        STEP()

        my_flow.off()
        remote.hi_off("main")
        command.off()
        STEP()

        ballons = step.add_epilog(
            Constant(
                r"""
                \begin{scope}[local to=pizza, every path/.style={fill=Light1}]
                  \path (.1, .35) circle [x radius=.12, y radius=.12] node (a){};
                  \path (.65, .40) circle [x radius=.13, y radius=.10] node (b){};
                  \path (.7, -.20) circle [x radius=.17, y radius=.14] node (c){};
                  \path (.0, .12) node (a'){} -- ($(a')!1!6:(a)$) -- ($(a')!1!-6:(a)$) -- cycle;
                  \path (.55, .20) node (b'){} -- ($(b')!1!4:(b)$) -- ($(b')!1!-4:(b)$) -- cycle;
                  \path (.6, -.45) node (c'){} -- ($(c')!1!8:(c)$) -- ($(c')!1!-8:(c)$) -- cycle;
                  \node[scale=3, Red3] (a) at (a) {\bf !!};
                  \node[scale=2, Red3] (b) at (b) {\vphantom{p}\bf \`o.\'o};
                  \node[scale=3, Red3] (c) at (c) {\bf <3<3};
                \end{scope}
                """
            )
        )
        STEP()

        ballons.off()
        STEP()

        # Checkout `dev` again.
        command.on().text = r"git checkout \ghi{dev}"
        my_repo.hi_on("dev")
        STEP()

        my_repo.checkout_branch("dev")
        STEP()

        command.off()
        my_repo.hi_off("dev")
        STEP()

        pic.off()

        def my_opacity(o=0.3):
            my_repo.intro.opacity = str(o)
            my_pointer._opacity = o
            my_files._opacity = o / 2 if o < 1 else o

        def their_opacity(o=0.3):
            their_repo.intro.opacity = str(o)
            their_pointer._opacity = o
            their_files._opacity = o / 2 if o < 1 else o

        pic_their.on()
        my_opacity()
        SPLIT("Collaborate", "Collaborate", "You're Not Alone")

        # Cloning on their side.
        command_side("right")
        command.on().text = r"git \gkw{clone} <url>"
        command.location = "0, -.15"
        STEP()

        their_flow = step.add_epilog(
            RemoteArrow("website.center", "above=30 of theirmachine", bend="30")
        )
        STEP()

        their_pointer = step.add_epilog(
            RemoteArrow(
                ".65, -.25",
                "above right=4 and 5 of remote-d1e8c8c-message.south east",
                name="origin",
            )
        )
        their_repo.on().populate(remote)
        [their_repo.hi_on(c) for c in their_repo.commits]
        their_files.on()
        their_files.populate(my_files)
        command.start = "above=10 of HEAD.west"
        their_files.all_mod("+")
        their_repo.add_remote_branch("origin/main")
        their_repo.add_remote_branch("origin/dev", c.hash)
        STEP()

        [their_repo.hi_off(c) for c in their_repo.commits]
        their_flow.off()
        command.off()
        their_files.all_mod("0")
        STEP()

        their_pointer.style = "hi"
        their_repo.hi_on("origin/main")
        their_repo.hi_on("origin/dev")
        hi_their_git = their_files.highlight("git")
        STEP()

        their_pointer.style = ""
        hi_their_git.off()
        their_repo.hi_off("origin/main")
        their_repo.hi_off("origin/dev")
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

        # New branch on their side.
        command.on().text = r"git checkout \gkw{-b} \ghi{alien}"
        command.start = "left=2 of HEAD.south west"
        command.end = ".6"
        their_repo.add_branch("alien", c.hash)
        their_repo.hi_on("alien")
        their_repo.checkout_branch("alien")
        STEP()

        command.off()
        their_repo.hi_off("alien")
        STEP()

        # New commit on their side: Siciliana!
        step.bump_epilog(pic).on().which = "Siciliana"
        pic.location = "-.5, -.55"
        their_siciliana = their_files.append("siciliana.md", mod="+")
        (their_readme := their_files["readme"]).mod = "m"
        STEP()

        command.on().text = "git commit"
        command.location = "0, -.07"
        STEP()

        pic.off()
        their_readme.mod = their_siciliana.mod = "0"
        c = their_repo.add_commit("I", "636694f", "Add Siciliana.")
        their_repo.hi_on(c)
        STEP()

        command.off()
        their_repo.hi_off(c)
        STEP()

        # They push their commit on the shared repo.
        command.on().text = r"git push \ghi{origin} alien"
        command.location, command.end = "-.04, -.07", ".5"
        their_repo.hi_on("alien")
        their_pointer.style = "hi"
        STEP()
        their_pointer.style = ""
        their_repo.hi_off("alien")

        f = their_flow.on()
        f.start, f.end = f.end, f.start
        f.side = "right"
        f.bend = "20"
        remote.add_branch("alien", remote.head.ref)
        remote.checkout_branch("alien")
        c = remote.add_commit(c.copy())
        remote.checkout_branch("main")
        remote.hi_on(c)
        remote.hi_on("alien")
        their_pointer.start = "above=5 of origin/alien.north"
        their_repo.add_remote_branch("origin/alien")
        STEP()

        remote.hi_off(c)
        remote.hi_off("alien")
        command.off()
        their_flow.off()
        STEP()

        # Fetch commit.
        my_opacity(1)
        their_opacity()
        STEP()

        command.on().text = rf"git \gkw{{fetch}} {website}"
        command_side("left", 0.20)
        my_pointer.style = "hi"
        STEP()

        my_pointer.style = ""
        f = my_flow.on()
        f.start = f.end
        f.end = "-.8, -.1"
        f.side = "right"
        f.bend = "20"
        web_alien = f"{website}/alien"
        my_repo.add_remote_branch(web_alien, "aa0299e")
        c = my_repo.add_commit(c.copy(), _branch=web_alien)
        my_repo.hi_on(c)
        my_pointer.start = "above=20 of mine-636694f-message.north"
        STEP()

        my_repo.hi_off(c)
        command.off()
        my_flow.off()
        STEP()

        # Navigating to new commit and back.
        my_repo.hi_on("HEAD")
        STEP()

        command.on().text = rf"git checkout \ghi{{{web_alien}}}"
        command.anchor = "base west"
        command.location = "$(mine-636694f-message.north east) + (17, 26)$"
        command.start = "right=60 of mine-636694f-message.north east"
        command.end = "60mm"
        my_repo.hi_on(web_alien)
        STEP()

        my_repo.checkout_detached("636694f")
        (my_siciliana := my_files.append(their_siciliana.copy())).mod = "+"
        hi_siciliana = my_files.highlight("siciliana")
        my_readme.mod = "m"
        hi_readme = my_files.highlight("readme")
        STEP()

        command.on().text = r"git checkout \ghi{dev}"
        hi_readme.off()
        hi_siciliana.off()
        my_repo.checkout_branch("dev")
        my_repo.hi_off(web_alien)
        my_repo.hi_on("dev")
        my_files.pop(my_siciliana)
        my_readme.mod = "0"
        STEP()

        hi_readme.off()
        command.off()
        my_repo.hi_off("dev")
        my_repo.hi_off("HEAD")
        STEP()

        # Merging their commit.
        command.on().text = rf"git \gkw{{merge}} {web_alien}"
        my_repo.hi_on(["HEAD", web_alien])
        STEP()
        my_repo.hi_off(["HEAD", web_alien])

        my_repo.move_branch("dev", c.hash)
        my_repo.checkout_branch("dev")
        my_files.append(my_siciliana).mod = "+"
        my_readme.mod = "m"
        my_repo.hi_on("dev")
        STEP()
        my_repo.hi_off("dev")

        command.off()
        hi_readme.off()
        my_readme.mod = "0"
        my_siciliana.mod = "0"
        STEP()

        # Pushing the merge.
        command.on().text = rf"git \gkw{{push}} {website} \ghi{{dev}}"
        my_repo.hi_on("dev")
        remote.hi_on("dev")
        f = my_flow.on()
        f.start, f.end = f.end, f.start
        f.side = "left"
        STEP()

        remote.move_branch("dev", c.hash)
        my_repo.remote_to_branch(web_dev)
        STEP()

        command.off()
        my_flow.off()
        my_repo.hi_off("dev")
        remote.hi_off("dev")
        STEP()

        their_opacity(1)
        STEP()

        SPLIT("Fork", None, "When you Diverge")

        for repo in (my_repo, remote, their_repo):
            repo.fade_commits(1, 4)
        STEP()

        for repo in (my_repo, remote, their_repo):
            repo.trim(4)
        remote.intro.location = "-.10" + y_up_repos
        their_repo.intro.location = ".40" + y_down_repos
        my_pointer.start = "above right=25 and 10 of mine-last"
        my_pointer.end = "left=5 of remote-1-hash.south west"
        their_pointer.start = "above right=25 and 50 of theirs-last"
        their_pointer.end = "right=5 of remote-1-message.south east"
        for p in (my_pointer, their_pointer):
            p.end = p.end.replace("d1e8c8c", remote.commits[0].hash)
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

        # Rename and duplicate command.
        command.aperture = "7"
        command.anchor = "base"
        (my_command := command.on()).text = "git commit"
        their_command = step.add_epilog(command.copy())
        del command
        my_command.location = "-.07, -.29"
        their_command.location = "+.07, -.40"
        my_command.start = "above right=20 and 80 of mine-last"
        their_command.start = "above left=8 and 25 of theirs-last"
        my_command.end = ".23"
        their_command.end = ".65"
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

        # Both push at the same time.
        my_command.on().text = f"git push {website} dev"
        their_command.on().text = "git push origin alien"
        my_command.start = "above right=10 and 70 of mine-last"
        my_command.location = "-.08, -.28"
        their_command.location = "+.05, -.40"
        STEP()

        their_command.style = "ok"
        my_command.style = "fade"
        STEP()

        their_repo.hi_on("alien")
        remote.hi_on("alien")
        their_flow.on().end = "right=5 of remote-last-message.north east"
        their_flow.start = "above right=30 and 15 of theirmachine.north"
        their_pointer.style = "hi"
        STEP()
        their_pointer.style = ""

        remote.checkout_branch("alien")
        (c_marinara := remote.add_commit(c_marinara.copy()))
        remote.hi_on(c_marinara.hash)
        remote.checkout_branch("main")
        their_repo.remote_to_branch("origin/alien")
        their_repo.hi_off("alien")
        STEP()

        their_flow.off()
        remote.hi_off("alien")
        remote.hi_off(c_marinara.hash)
        their_command.style = "fade"
        my_command.style = "ok"
        my_flow.on().end = "left=5 of remote-3-hash.north west"
        step.bump_epilog(my_command)
        remote.hi_on("dev")
        my_pointer.style = "hi"
        my_repo.hi_on("dev")
        STEP()
        my_repo.hi_off("dev")
        my_pointer.style = ""

        remote.checkout_branch("dev")
        remote.add_commit(c_calzone.copy(), i=2).type = "Y"
        remote.hi_on(c_calzone.hash)
        remote.checkout_branch("main")
        my_repo.remote_to_branch(web_dev)
        STEP()

        my_command.off().style = ""
        their_command.off().style = ""
        my_flow.off()
        my_repo.hi_off("dev")
        my_pointer.style = ""
        remote.hi_off("dev")
        remote.hi_off("alien")
        remote.hi_off(c_calzone.hash)
        remote.hi_off(c_marinara.hash)
        STEP()

        pic.on().which = "OMG"
        pic.anchor = "center"
        pic.location = "+.02, -.5"
        pic.height = "9cm"
        my_opacity()
        their_opacity()
        STEP()

        # Fetching their commits.
        pic.off()
        my_opacity(1)
        STEP()

        my_command.on().text = rf"git \gkw{{fetch}} {website}"
        my_command.location = "-.06, -.20"
        my_command.start = "above right=45 and 80 of mine-2"
        STEP()

        my_flow.on().start = "left=5 of remote-3-hash.west"
        my_flow.end = "above right=68 and 30 of mine-2-hash"
        my_flow.bend = "30"
        my_flow.side = "right"
        remote.hi_on("alien")
        my_repo.hi_on(web_alien)
        STEP()

        my_repo.add_commit(c_marinara.copy(), _branch=web_alien)
        my_repo[c_calzone.hash].type = "Y"
        my_repo.hi_on(c_marinara.hash)
        # The ring clashes with commit highlight.
        my_repo.hi_off(web_alien)
        my_repo.hi_on(web_alien, False)
        STEP()

        remote.hi_off("alien")
        my_repo.hi_off(web_alien, False)  # Remove the ring correctly.
        my_repo.hi_off(c_marinara.hash)
        my_command.off()
        my_flow.off()
        STEP()

        # Navigating from ours to theirs and back.
        my_readme_hi.on()
        my_calzone_hi.on()
        my_repo.hi_on("HEAD")
        STEP()

        my_command.on().text = rf"git checkout \ghi{{{web_alien}}}"
        my_command.anchor = "base west"
        my_command.location = "above right=45 and 80 of mine-last"
        my_command.end = "30mm"
        STEP()

        my_repo.checkout_detached("0fcd744")
        my_files.pop(my_calzone)
        my_calzone_hi.off()
        my_marinara = my_files.append("marinara.md")
        my_marinara_hi = my_files.highlight("marinara")
        STEP()

        my_command.on().text = r"git checkout \ghi{dev}"
        my_repo.checkout_branch("dev")
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
            pic_website,
            pic_their,
        ):
            m.off()
        left = step.add_prolog(my_repo.copy()).on()
        left.intro.name = "left"
        left.intro.alignment = "double"
        right = step.add_prolog(left.copy()).off()
        right.intro.name = "right"
        left.intro.location = "-.65, -.8"
        right.intro.location = "+.4, -.8"
        my_command.anchor = their_command.anchor = "center"
        SPLIT("Fusion", "Merge and Rebase", "Two Git Philosophies")

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
        rebase_title.location = "+.45, .8"
        rebase_title.text = "Rebase"
        right.on()
        STEP()

        # Merge.
        left_command = step.add_epilog(my_command.copy()).on()
        (l := left_command).text = rf"git \gkw{{merge}} \ghi{{{web_alien}}}"
        l.start, l.end, l.aperture = "-.35, -.11", ".3", "6"
        l.location = ".0, .2"
        left_safe = left.copy()
        left.hi_on(["HEAD", web_alien])
        STEP()

        left.add_commit("A", "007e53f", f"Merge {web_alien} into dev.")
        left.hi_on(["007e53f", "dev"])
        left.hi_off(["HEAD", web_alien])
        STEP()
        left.hi_off(["007e53f", "dev"])

        left_command.off()
        STEP()

        # Push.
        left_command.on().text = rf"git push {website} \ghi{{dev}}"
        left.hi_on(web_dev)
        STEP()

        left.remote_to_branch(web_dev)
        STEP()

        left_command.off()
        left.hi_off(web_dev)
        STEP()

        # Rebase
        right_command = step.add_epilog(left_command.copy()).on()
        (r := right_command).text = rf"git \gkw{{rebase}} \ghi{{{web_alien}}}"
        r.start, r.end, r.aperture = ".20, -.15", ".55", "5"
        right_safe = right.copy()
        right.hi_on(["HEAD", web_alien])
        STEP()
        right.hi_off(["HEAD", web_alien])

        a = right["4ac80b2"]
        b = right.add_commit("I", "a136a71", a.message)
        right.fade_commit(a, "shade")
        right.hi_on([b, "dev"])
        STEP()
        right.hi_off([b, "dev"])
        right.unfade_commit(a, "shade")

        right_command.off()
        STEP()

        # Push.
        right_command.on().text = rf"git push {website} \ghi{{dev}}"
        right.hi_on(web_dev)
        STEP()

        right_command.style = "error"
        STEP()

        right_command.off().style = ""
        right.hi_off(web_dev)
        STEP()
        right.hi_on(web_dev)

        right_command.on().text = rf"git push \gkw{{--force}} {website} \ghi{{dev}}"
        STEP()

        right.remote_to_branch(web_dev)
        right.fade_commit(c_calzone.hash)
        STEP()

        right_command.off()
        right.hi_off(web_dev)
        STEP()

        right.pop_commit(c_calzone.hash)
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
            c = r.add_commit("I", "9549b2a", "Add Napoletana.", _branch=web_alien)
        c = cast(PlaceHolder, c)
        left.hi_on(c.hash)
        STEP()

        # Producing one new commit.
        left.hi_off("9549b2a")
        left_command.text = "git commit"
        for r in (left, right):
            c = r.add_commit("H", "8dd46ef", "Surprise pizza.", i=3)
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
        left_command.on().text = rf"git \gkw{{merge}} \ghi{{{web_alien}}}"
        left_command.location = ".0, .50"
        left_command.start = "-.35, .15"
        left.hi_on(["HEAD", web_alien])
        STEP()
        left.hi_off(["HEAD", web_alien])

        c = left.add_commit("A", "cbcce18", f"Merge {web_alien} into dev.")
        left.hi_on(c)
        STEP()
        left.hi_off(c)

        left_command.off()
        STEP()

        # Push
        left_command.on().text = rf"git push {website} \ghi{{dev}}"
        left.hi_on(web_dev)
        STEP()

        left.remote_to_branch(web_dev)
        STEP()

        left_command.off()
        left.hi_off(web_dev)
        STEP()

        # Rebase 2 commits.
        right_command.on().text = rf"git \gkw{{rebase}} \ghi{{{web_alien}}}"
        right_command.location = left_command.location
        right_command.end = ".6"
        right_command.start = ".18, .15"
        right.hi_on(["HEAD", web_alien])
        STEP()
        right.hi_off(["HEAD", web_alien])

        a = right["4ac80b2"]
        b = right.fade_commit("8dd46ef")
        c = right.add_commit("I", "a03a2bb", a.message)
        right.hi_on(c)
        right.fade_commit(a, "shade")
        STEP()
        right.unfade_commit(a, "shade")
        right.hi_off(c)

        c = right.add_commit("I", "4a6ebf4", b.message)
        right.hi_on(c)
        right.fade_commit(b, "shade")
        STEP()
        right.unfade_commit(b, "shade")
        right.hi_off(c)

        right_command.off()
        STEP()

        # Force-push
        right_command.on().text = rf"git push \gkw{{--force}} {website} \ghi{{dev}}"
        right.hi_on(web_dev)
        STEP()

        right.remote_to_branch(web_dev)
        right.fade_commit(a.hash)
        STEP()

        right_command.off()
        right.hi_off(web_dev)
        STEP()

        [right.pop_commit(k.hash) for k in (a, b)]
        STEP()

        # Commit one last time just to see.
        pic.on().which = "Capricciosa"
        pic.location, pic.height = ".0, -.2", "12cm"
        STEP()

        left_command.on().text = "git commit"
        left_command.start = ""
        STEP()

        pic.off()
        a = left.add_commit("I", "4f87c03", "Add Capricciosa.")
        b = right.add_commit("I", "ca8b8e8", "Add Capricciosa.")
        left.hi_on(a)
        right.hi_on(b)
        STEP()

        left.hi_off(a)
        right.hi_off(b)
        left_command.off()
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
            pic_website,
            pic_their,
            url,
        ):
            m.on()
        repos_safe = []
        for r in (my_repo, remote, their_repo):
            r.intro.alignment = "double"
            repos_safe.append(r.copy())
        my_pointer.start = "-.72, -.4"
        their_pointer.start = ".75, -.4"
        SPLIT("PropagateMerge", "Share integrated work", "(Merge style)")

        # Save for later rewinding.
        safe = [r.copy() for r in (my_repo, remote, their_repo)]

        # Merge.
        (mc := my_command).on().text = rf"git \gkw{{merge}} \ghi{{{web_alien}}}"
        mc.location, mc.start, mc.end = "0, -.2", "-.3, -.5", ".3"
        [my_repo.hi_on(r) for r in ("HEAD", web_alien)]
        STEP()

        [my_repo.hi_off(r) for r in ("HEAD", web_alien)]
        c_merge = my_repo.add_commit("A", "5d3fd0b", "Merge commit.")
        my_repo.hi_on(c_merge)
        my_pointer.start = "-.6, -.2"
        my_files.append(my_marinara)
        [m.on() for m in (my_marinara_hi, my_calzone_hi, my_readme_hi)]
        STEP()

        my_repo.hi_off(c_merge)
        my_command.off()
        [m.off() for m in (my_marinara_hi, my_calzone_hi, my_readme_hi)]
        STEP()

        # Push merge commit to remote.
        my_command.on().text = f"git push {website} dev"
        my_command.location = "-.01, -.15"
        [r.hi_on("dev") for r in (my_repo, remote)]
        my_pointer.style = "hi"
        STEP()

        (mf := my_flow).on()
        mf.start, mf.end = "-.70, -.2", mf.start
        mf.side = "left"
        remote.checkout_branch("dev")
        remote.add_commit(c_merge)
        remote.checkout_branch("main")
        my_repo.remote_to_branch(web_dev)
        [remote.hi_on(k.hash) for k in [c_merge]]
        [r.hi_off("dev") for r in (my_repo, remote)]
        my_pointer.style = ""
        STEP()

        my_command.off()
        my_flow.off()
        [remote.hi_off(k.hash) for k in [c_merge]]
        STEP()

        # Pull merge commit on their side.
        their_opacity(1)
        (tc := their_command).on().text = r"git \gkw{pull} origin dev"
        tc.location = my_command.location
        tc.start, tc.end = ".15, -.38", ".6"
        their_pointer.style = "hi"
        remote.hi_on("dev")
        their_repo.hi_on("origin/dev")
        their_repo.hi_on("HEAD")
        STEP()

        (tf := their_flow).on()
        tf.start, tf.end = (
            "remote-last-message.south east",
            "left=15 of calzone-icon.west",
        )
        tf.bend = "25"
        tf.side = "left"
        their_repo.add_commit(c_calzone, i=2)
        their_repo.move_branch("origin/dev", c_calzone.hash)
        their_repo.add_commit(c_merge)
        their_repo.move_branch("origin/dev", c_merge.hash)
        their_pointer.start = ".60, -.23"
        [their_repo.hi_on(k.hash) for k in [c_calzone, c_merge]]
        their_calzone = their_files.append(my_calzone)
        their_calzone_hi = their_files.highlight("calzone")
        [m.on() for m in (their_marinara_hi, their_calzone_hi, their_readme_hi)]
        remote.hi_off("dev")
        their_repo.hi_off("origin/dev")
        their_repo.hi_off("HEAD")
        their_pointer.style = ""
        STEP()

        [m.off() for m in (their_marinara_hi, their_calzone_hi, their_readme_hi)]
        [their_repo.hi_off(k.hash) for k in [c_calzone, c_merge]]
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
            r.intro.alignment = "mixed"
            r.become(s)
        their_opacity()
        my_files.pop("marinara")
        their_files.pop("calzone")
        my_pointer.start = "above right=10 and -10 of mymachine"
        their_pointer.start = ".75, -.4"
        their_pointer.end = ".25, .1"
        SPLIT("PropagateRebase", "Share integrated work", "(Rebase style)")

        # Rebase.
        (mc := my_command).on().text = rf"git \gkw{{rebase}} \ghi{{{web_alien}}}"
        mc.location = "0, -.25"
        mc.start, mc.end = "-.20, -.5", ".4"
        [my_repo.hi_on(r) for r in ("HEAD", web_alien)]
        STEP()
        [my_repo.hi_off(r) for r in ("HEAD", web_alien)]

        c_calzone = my_repo["4ac80b2"]
        c_rebased = my_repo.add_commit("I", "394e864", c_calzone.message)
        my_files.append(my_marinara)
        [m.on() for m in (my_marinara_hi, my_calzone_hi, my_readme_hi)]
        my_repo.fade_commit(c_calzone, "shade")
        my_repo.hi_on(c_rebased)
        STEP()
        my_repo.hi_off(c_rebased)
        my_repo.unfade_commit(c_calzone, "shade")
        [m.off() for m in (my_marinara_hi, my_calzone_hi, my_readme_hi)]

        my_command.off()
        STEP()

        # Push rebased commit to remote.
        my_command.on().text = rf"git push \gkw{{--force}} {website} \ghi{{dev}}"
        my_command.location = ".1, -.20"
        [r.hi_on("dev") for r in (my_repo, remote)]
        my_pointer.style = "hi"
        STEP()

        [r.hi_off("dev") for r in (my_repo, remote)]
        my_pointer.style = ""
        my_flow.on()
        remote.checkout_branch("dev")
        remote.add_commit(c_rebased)
        remote.checkout_branch("main")
        my_repo.remote_to_branch(web_dev)
        [r.fade_commit(c_calzone.hash) for r in (remote, my_repo)]
        [remote.hi_on(k.hash) for k in [c_rebased]]
        STEP()

        my_command.off()
        my_flow.off()
        [remote.hi_off(k.hash) for k in [c_rebased]]
        STEP()

        my_repo.pop_commit(2)
        remote.pop_commit(2)
        STEP()

        # Pull rebased commit on their side.
        their_opacity(1)
        their_command.on().text = r"git \gkw{pull} origin \ghi{{dev}}"
        their_command.location = "0, -.20"
        remote.hi_on("dev")
        their_repo.hi_on("origin/dev")
        their_pointer.style = "hi"
        STEP()
        their_pointer.style = ""
        remote.hi_off("dev")
        their_repo.hi_off("origin/dev")

        their_flow.on()
        their_flow.start = "remote-last-message.south"
        c_rebased = their_repo.add_commit(c_rebased)
        their_repo.move_branch("origin/dev", c_rebased.hash)
        their_calzone = their_files.append(my_calzone)
        their_calzone_hi = their_files.highlight("calzone")
        their_repo.hi_on(c_rebased)
        [m.on() for m in (their_marinara_hi, their_calzone_hi, their_readme_hi)]
        STEP()
        [m.off() for m in (their_marinara_hi, their_calzone_hi, their_readme_hi)]
        their_repo.hi_off(c_rebased)

        their_flow.off()
        their_command.off()
        STEP()

        for f in files_6:
            eval(f + "_hi").on()
        STEP()

        for f in files_6:
            eval(f + "_hi").off()
        STEP()
