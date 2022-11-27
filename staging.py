"""Slide to explain all steps towards one commit.
"""

from typing import Tuple, cast

from diffs import DiffedFile
from document import FindPlaceHolder, Slide
from modifiers import AnonymousPlaceHolder, Constant, ListBuilder, Regex, RegexBuilder
from repo import Repo
from steps import Step

AreasBuilder = RegexBuilder(r"\\MakeArea.*{.*?}{.*?}{.*?}{(.*?)}.*", "text")
Areas = ListBuilder(AreasBuilder, "\n")

ArrowModifier, Arrow = FindPlaceHolder("SwitchArrow")
Arrows = ListBuilder(Arrow, "\n")


class StagingStep(Step):
    def parse_body(self):
        input = self.body
        chunks = input.split("\n\n")
        it = iter(chunks)
        self.repo = Repo(next(it))
        self.areas = Areas.parse(next(it))
        self.ondisk = Regex(next(it), r".*(next).*(stage).*", "up area")
        self.inram = Constant(next(it))
        self.file = Regex(
            next(it),
            r".*?(last).*{(.*?)}\n.*(0).*(filename.ext).*",
            "area location mod filename",
        )
        self.arrows = Arrows.parse(next(it))
        self.diff = DiffedFile(next(it))
        try:
            while some := next(it):
                assert not some.strip()
        except StopIteration:
            pass

    def render_body(self) -> str:
        return "\n\n".join(
            m.render()
            for m in [
                self.repo,
                self.areas,
                self.ondisk,
                self.inram,
                self.file,
                self.arrows,
                self.diff,
            ]
        )


class StagingSlide(Slide):
    def animate(self):

        step = cast(StagingStep, self.pop_step())
        STEP = lambda: self.add_step(step)

        repo = step.repo
        ondisk = step.ondisk.off()
        inram = step.inram.off()
        file = step.file.off()
        diff = step.diff.off()

        repo.intro.location = "-.82, -.73"

        areas = (
            # l.e.m.s.n.
            last,
            editor,
            modified,
            stage,
            next,
        ) = [a.off() for a in step.areas]
        arrows = (
            keyboard,
            ctrls,
            add,
            commit,
            soft,
            reset,
            hard_nl,
            hard_sl,
            hard_ml,
            ctrlz,
        ) = (a.off() for a in step.arrows)
        forwards = (keyboard, ctrls, add, commit)
        backwards = (soft, reset, hard_ml, hard_sl, hard_nl, ctrlz)

        # Zoomed baby repo.
        repo._render_labels = False
        nohash = "???????"
        last_commit = repo.add_commit("I", "a03a2bb", "One commit.")
        next_commit = repo.add_commit("I", nohash, "Next commit.")

        def repo_down():
            repo.checkout_detached(last_commit.hash)
            repo.fade_commit(next_commit).hash = nohash

        def repo_up(new_hash: str):
            repo.unfade_commit(next_commit).hash = new_hash
            repo.checkout_detached(next_commit.hash)

        repo_down()

        def copy(
            file: Regex,
            area: str,
            name: str | Tuple[float, float] = "",
            pos: Tuple[float, float] | None = None,
            mod: str | None = None,
        ):
            new = file.copy()
            new.area = area
            if type(name) is str and name:
                new.filename = name
            elif type(name) is tuple:
                pos = name
            if pos is not None:
                new.location = "{}, {}".format(*pos)
            if mod is not None:
                new.mod = mod
            return step.add_epilog(new)

        def disk_to(area_name: str):
            if area_name == "last":
                inram.off()
            elif area_name == "editor":
                inram.on()
                area_name = "last"
            ondisk.on().up = area_name
            ondisk.area = "stage" if area_name == "next" else area_name

        def fade_after(area_name, new_hash=""):
            i_next = "last editor modified stage next".split().index(area_name) + 1
            for area in areas[:i_next]:
                if area._opacity != 0:  # Leave phantoms alone.
                    area._opacity = 1
            for area in areas[i_next:]:
                area._opacity = 0.3
            if i_next == len(areas):
                assert new_hash  # Must provide one when reaching the top.
                repo_up(new_hash)
            else:
                repo_down()
            disk_to(area_name)

        # Initial commit.
        x_left = -0.3
        y_mid = 0.15
        l_readme = copy(file, "last", "README.md", (x_left, y_mid))
        x_right = 0.25
        l_margherita = copy(file, "last", "margherita.md", (x_right, y_mid))
        STEP()

        last.on()
        l_readme.on()
        l_margherita.on()
        STEP()

        # Edit file.
        editor.on()._opacity = 0  # Phantom for the arrow to construct.
        keyboard.on()
        e_readme = copy(l_readme, "editor", mod="m")
        STEP()

        ctrlz.on()
        STEP()

        editor._opacity = 1
        disk_to("editor")
        STEP()

        # Save file.
        keyboard.labeled = ctrlz.labeled = "0"
        modified.on()._opacity = 0
        ctrls.on()
        disk_to("modified")
        m_readme = copy(l_readme, "modified")
        STEP()

        ctrls.labeled = "0"
        STEP()

        neq = step.add_epilog(
            Constant(
                r"""
                \draw[line width=1.5, -Stealth, m,
                      shorten <=2*\CommitRadius mm,
                      shorten >=45mm]
                  (a03a2bb) -- (modified.west)
                  node[scale=4, above] {$\neq$}
                  -- (modified.center);
                """
            )
        )
        STEP()

        step.remove_from_epilog(neq)
        m_readme.mod = "m"
        modified._opacity = 1
        STEP()

        # Not ready to commit yet.
        stage.on()._opacity = 0  # Phantom to show next commit first.
        next.on()._opacity = 0.3
        STEP()

        commit.on()
        what = step.add_epilog(
            AnonymousPlaceHolder(
                r"\AutomaticCoordinates{c}{<location>}" + "\n"
                r"\node[scale=4, <color>] at (c) {\bf <text>};",
                "new",
                text=r"\texttimes",
                location="-.25, .30",
                color= "Red3",
            )
        )
        STEP()

        commit.off()
        what.text = "???"
        what.location = "stage"
        STEP()

        what.off()
        STEP()

        # Git add.
        add.on().text = add.text + " " + cast(str, m_readme.filename)
        add_offset_safe = [add.offset]
        add.offset = "3"
        s_readme = copy(m_readme, "stage")
        disk_to("stage")
        STEP()

        add.labeled = "0"
        STEP()

        # Create a new file.
        for a in forwards:
            a.off().labeled = "1"
        keyboard.on()
        e_regina = copy(l_readme, "editor", "regina.md", (x_right, y_mid), mod="+")
        ctrlz.off().labeled = "1"
        STEP()

        # Save it.
        keyboard.labeled = "0"
        ctrls.on()
        m_regina = copy(e_regina, "modified")
        STEP()

        # Stage it.
        ctrls.labeled = "0"
        add.text = add.text.removesuffix(cast(str, m_readme.filename)) + cast(
            str, m_regina.filename
        )
        add.on()
        s_regina = copy(m_regina, "stage")
        STEP()

        add.labeled = "0"
        STEP()

        # Commit.
        commit.on()
        what.on().text, what.color = r"\checkmark", "Green5"
        what.location = "right=9 of n"
        STEP()

        what.off()
        fade_after("next", "4b87875")
        n_readme = copy(s_readme, "next", (x_left, 0.25), mod="0")
        y_up = 0.63
        y_down = -0.07
        n_regina = copy(s_regina, "next", (x_right, y_up), mod="0")
        n_margherita = copy(l_margherita, "next", (x_right, y_down), mod="0")
        commit.labeled = "0"
        STEP()

        # Unveil the staging area.
        stage._opacity = 1
        stage.text = r"\bf Stage"
        STEP()

        # Summarize.
        for a in forwards:
            a.on().labeled = "1"
        add.text = r"\$ git \gkw{add}"
        STEP()

        # Rewind.
        stage.text = "Stage"
        [a.off() for a in forwards]
        for a in "nsme":
            for f in "readme regina margherita".split():
                varname = f"{a}_{f}"
                if varname in locals():
                    eval(varname).off()
        fade_after("last")
        STEP()

        # Create personal file.
        keyboard.on()
        e_readme.on()
        fade_after("editor")
        STEP()

        e_regina.on().location = n_regina.location
        STEP()

        e_todo = copy(n_margherita, "editor", "todo.txt", mod="+").on()
        STEP()

        keyboard.labeled = "0"
        ctrls.on()
        fade_after("modified")
        m_readme.on()
        m_regina.on()
        m_todo = copy(e_todo, "modified")
        m_pdf = copy(e_todo, "modified", "result.pdf", mod="+").off()
        for f, y in zip((m_regina, m_todo, m_pdf), (0.88, 0.28, -0.32)):
            f.location = str((x_right, y)).strip("()")
        STEP()

        # Generate non-source file.
        ctrls.labeled = "0"
        m_pdf.on()
        STEP()

        # Stage wrong files.
        add.on().text = r"\$ git \gkw{add} \ghi{--all}"
        add_offset_safe.append(add.offset)
        add.offset = add_offset_all = "-5"
        fade_after("stage")
        s_readme.on()
        s_regina.on().location = m_regina.location
        s_todo = copy(m_todo, "stage")
        s_pdf = copy(m_pdf, "stage")
        STEP()

        add.offset = add_offset_safe.pop()
        add.labeled = "0"
        STEP()

        # Unstage wrong files.
        reset_safe = reset.copy()
        reset.slide, reset.crit, reset.offset = ".85", ".40", "-8"
        reset.on()
        STEP()

        s_todo.off()
        s_pdf.off()
        s_readme.off().location = l_readme.location
        s_regina.off().location = l_margherita.location
        add.off().labeled = "1"
        STEP()

        reset.off()
        STEP()

        # Stage only the right files.
        add.on().text = r"\$ git \gkw{{add}} \ghi{{{}}}".format(m_readme.filename)
        s_readme.on()
        STEP()

        add.text = r"\$ git \gkw{{add}} \ghi{{{}}}".format(m_regina.filename)
        s_regina.on()
        STEP()

        add.labeled = "0"
        add.offset = add_offset_safe[0]  # Don't pop, still useful once.
        STEP()

        # Commit only the right files.
        commit.on()
        fade_after("next", "4b87875")
        [f.on() for f in (n_readme, n_regina, n_margherita)]
        STEP()

        commit.labeled = "0"
        STEP()

        # Forgot to create a .gitignore: reset --soft!
        soft_safe = soft.copy()
        soft.on().slide, soft.crit, soft.offset = ".85", ".48", "5"
        STEP()

        fade_after("stage")
        [f.off() for f in (n_readme, n_regina, n_margherita)]
        commit.off().labeled = "1"
        STEP()

        # Unstage again.
        soft.off().__dict__.update(soft_safe.__dict__)
        add.off().labeled = "1"
        reset.on().offset = "0"
        STEP()

        reset.off().__dict__.update(reset_safe.__dict__)
        fade_after("modified")
        [f.off() for f in (s_readme, s_regina)]
        STEP()

        # Create gitignore.
        ctrls.off().labeled = "1"
        keyboard.labeled = "1"
        e_gitignore = copy(e_regina, "editor", ".gitignore")
        e_readme.location = str((x_left, y_up)).strip("()")
        e_gitignore.location = str((x_left, y_down)).strip("()")
        diff.on()
        STEP()

        diff.insert_lines(cast(str, e_todo.filename), "+", 2)
        STEP()

        diff.insert_lines("*.pdf", "+", 3)
        STEP()

        ctrls.on()
        keyboard.labeled = "0"
        m_gitignore = copy(e_gitignore, "modified")
        m_readme.location = e_readme.location
        m_pdf.mod = "0"
        m_todo.mod = "0"
        diff.intro.location = diff.intro.location.replace("editor", "modified")
        STEP()

        # Can git add --all without worrying.
        ctrls.labeled = "0"
        add.on().text = r"\$ git \gkw{add} \ghi{--all}"
        add.offset = add_offset_all
        fade_after("stage")
        s_readme.on().location = m_readme.location
        s_regina.on().location = str((x_right, 0.25)).strip("()")
        s_gitignore = copy(m_gitignore, "stage")
        diff.intro.location = diff.intro.location.replace("modified", "stage")
        STEP()

        add.offset = add_offset_safe.pop()
        add.labeled = "0"
        STEP()

        # And finally commit without the undesired files.
        commit.on()
        fade_after("next", "e790b0c")
        n_gitignore = copy(s_gitignore, "next", mod="0")
        n_readme.location = s_readme.location
        [f.on() for f in (n_regina, n_readme, n_margherita)]
        diff.reset()
        STEP()

        for arrow in forwards:
            arrow.off().labeled = "1"
        diff.off()
        STEP()

        # Git reset --hard.
        [a.on() for a in (hard_nl, hard_sl, hard_ml)]
        hard_safe = hard_ml.copy()
        hard_ml.crit, hard_ml.offset = ".30", "6"
        STEP()

        for a in "nsme":
            for f in "readme gitignore regina margherita todo pdf".split():
                varname = f"{a}_{f}"
                if varname in locals():
                    eval(varname).off()
        fade_after("last")
        STEP()

        [a.off() for a in (hard_nl, hard_sl, hard_ml)]
        hard_ml.__dict__.update(hard_safe.off().__dict__)
        STEP()

        # Summary, with an abstract file instead.
        for f in (l_readme, e_readme, m_readme, s_readme, n_readme):
            f.filename = "myfile.ext"
        l_margherita.off()
        keyboard.on()
        ctrlz.on()
        last_commit.hash = "310dafc"
        fade_after("editor")
        l_readme.on()
        e_readme.on().location = l_readme.location
        STEP()

        ctrls.on()
        fade_after("modified")
        m_readme.on().location = e_readme.location
        STEP()

        add.on().text = r"\$ git \gkw{add}"
        fade_after("stage")
        s_readme.on().location = m_readme.location
        STEP()

        commit.on()
        fade_after("next", "c451c98")
        n_readme.on().location = s_readme.location
        STEP()

        soft.on()
        soft.text = r"\$ git reset \CommandHighlight{Green1}{--soft}"
        STEP()

        reset.on()
        STEP()

        hard_nl.on()
        hard_sl.on()
        hard_ml.on()
        hard_ml.text = r"\$ git reset \CommandHighlight{Red1}{--hard}"
        STEP()
