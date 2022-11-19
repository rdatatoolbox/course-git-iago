"""The slide with repo / project folder / file content."""

from typing import Tuple, cast

from diffs import DiffList
from document import HighlightSquare, Slide
from filetree import FileTree
from modifiers import AnonymousPlaceHolder, PlaceHolder, render_method
from repo import Command, HighlightCommit, Repo, hi_label
from steps import Step


class PizzasStep(Step):
    """The slide with repo / project folder / file content."""

    def __init__(self, input: str):
        chunks = input.split("\n\n")
        it = iter(chunks)
        self.filetree = FileTree(next(it))
        self.diffs = DiffList(next(it))
        self.repo = Repo(next(it))
        self.command = Command.parse(next(it))
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
                self.filetree,
                self.diffs,
                self.repo,
                self.command,
            ]
        )


class PizzasSlide(Slide):
    """Animate pizzas slide so it reproduces the small git history."""

    def animate(self) -> Tuple[Repo, FileTree, DiffList]:
        step = cast(PizzasStep, self.pop_step())
        ft = step.filetree
        df = step.diffs
        rp = step.repo
        cmd = step.command
        ft.clear()
        df.clear()
        rp.clear()
        cmd.off()
        STEP = lambda: self.add_step(step)

        image = step.add_epilog(
            AnonymousPlaceHolder(
                r"\node (im) at (Canvas.center) {\Pic<file>{15cm}{!}};",
                file="VariousPizzas",
            )
        ).on()
        STEP()

        readme_text = [
            """
            Collect and distribute the best pizzas recipes.
            """,
            """

            Where to find the pizza in the project:

            - __Margherita__: `./margherita.md`
            - __Regina__: `./regina.md`
            """,
        ]
        margherita_text = [
            """
            # Margherita

            The simplest and most famous,
            the one to pick when you're unsure
            whether the cook is good.

            __Base:__ tomato sauce
            __Topping:__
            - Mozzarella
            - Basil
            """,
            """

            *Note:*
            It is said that this pizza
            has only three ingredients
            corresponding to the three colors
            on the Italian flag.
            Nevertheless, it is always good
            and *authorized* to add
            olive oil, salt, or oregano.
            """,
        ]
        regina_text = [
            """
            # Regina

            This audacious pizza
            would be named from queen
            Elena of Montenegro.
            Created by pizzaiolo
            Raffaele Esposito.

            __Base:__ tomato sauce
            __Topping:__
            - Mozzarella
            - Ham
            - Mushrooms
            """
        ]

        # Root folder.
        _ = ft.append(
            "FirstFile", pos="Canvas.north west", filename="pizzas", type="folder"
        )
        f_readme = ft.append("FirstChild", filename="README.md")
        d_readme = df.append(pos="Canvas.north east", filename="README.md")
        d_readme.append_text(readme_text[0])
        STEP()

        image.off()
        STEP()

        # Git init.
        cmd._rendered = True
        cmd.on().text = "git init"
        STEP()

        ft.erase(f_readme)
        git = ft.append(
            "FirstChild",
            type="folder",
            filename=".git",
            mod="+",
            name="git",
        )
        f_readme = ft.append("AppendSibling", filename="README.md", connect=True)

        # No commit yet, repo in degenerated state.
        main = rp.labels.append("$(repo) + (50, 5)$", "0:0", "noarrow", "main").off()
        head = rp.labels.append("", "", "").off()
        commit = step.add_epilog(HighlightCommit.new("repo")).off()

        def head_on_main() -> PlaceHolder:
            head.ref = "main.base west"
            head.anchor = "base east"
            head.offset = "180:11"
            head.local = "2"
            commit.hash = main.hash
            return head

        def head_detached(hash: str) -> PlaceHolder:
            head.ref = hash
            head.offset = "160:20"
            head.anchor = "center"
            head.local = ".5,0"
            commit.hash = hash
            return head

        head_on_main()
        STEP()

        hi_repo = step.add_epilog(
            HighlightSquare.new("HEAD.south west", "main.north east")
        ).off()
        hi_gitfolder = git.add_epilog(
            HighlightSquare.new(
                "git.south west",
                "file-label.east |- git.north",
                padding=2,
            )
        ).off()

        hi_on = lambda: (hi_gitfolder.on(), hi_repo.on())
        hi_off = lambda: (hi_gitfolder.off(), hi_repo.off())

        git.mod = "0"
        hi_on()
        main.on()
        head.on()
        cmd.off()
        STEP()

        hi_off()
        STEP()

        # First commit.
        cmd.on().text = "git commit"
        STEP()

        rp.commits.append("I", "d1e8c8c", "First commit, the intent.")
        commit.hash = main.hash = "d1e8c8c"
        main.offset = "40:20"
        main.local = "-.5, 0"
        commit.on()
        hi_repo.lower = r"$(repo.south west) + (3*\eps, 3*\eps)$"
        hi_repo.upper = "repo.east |- main.north"
        hi_on()
        STEP()

        hi_off()
        cmd.off()
        STEP()

        # Adding Margherita
        cmd.off()
        f_margherita = ft.append(
            "AppendSibling", connect=True, filename="margherita.md"
        )
        d_margherita = df.append(filename="margherita.md")
        d_margherita.append_text(margherita_text[0])
        image.on().file = "Margherita"
        STEP()

        image.off()
        STEP()

        cmd.on().text = "git diff"
        STEP()

        f_margherita.mod = d_margherita.mod = "+"
        d_margherita.set_mod("+", 0, -1)
        STEP()

        cmd.on().text = "git commit"
        f_margherita.mod = d_margherita.mod = "0"
        d_margherita.set_mod("0", 0, -1)
        rp.commits.append("I", "4e29052", "First pizza: Margherita.")
        commit.hash = main.hash = "4e29052"
        hi_on()
        STEP()

        cmd.off()
        hi_off()
        STEP()

        # Editing Margherita
        d_margherita.append_text(margherita_text[1])
        image.on()
        STEP()

        image.off()
        STEP()

        f_margherita.mod = d_margherita.mod = "m"
        d_margherita.set_mod("+", 10, -1)
        cmd.on().text = "git diff"
        STEP()

        cmd.on().text = "git commit"
        f_margherita.mod = d_margherita.mod = "0"
        d_margherita.set_mod("0", 0, -1)
        rp.commits.append("I", "45a5b65", "Add note to the Margherita.")
        commit.hash = main.hash = "45a5b65"
        hi_on()
        STEP()

        cmd.off()
        hi_off()
        STEP()

        # Adding Regina.
        d_readme.append_text(readme_text[1])
        f_regina = ft.append("AppendSibling", connect=True, filename="regina.md")
        d_regina = df.append(filename="regina.md")
        d_regina.append_text(regina_text[0])
        image.on().file = "Regina"
        STEP()

        image.off()
        STEP()

        f_readme.mod = d_readme.mod = "m"
        d_regina.mod = f_regina.mod = "+"
        d_regina.set_mod("+", 0, -1)
        d_readme.set_mod("+", 1, -1)
        cmd.on().text = "git diff"
        STEP()

        cmd.on().text = "git status"
        d_readme.mod = "0"
        d_regina.mod = "0"
        d_readme.set_mod("0", 0, -1)
        d_regina.set_mod("0", 0, -1)
        STEP()

        d_readme.mod = d_regina.mod = f_regina.mod = f_readme.mod = "0"
        cmd.on().text = "git commit"
        rp.commits.append("I", "17514f2", "Add Regina. List pizzas in README.")
        commit.hash = main.hash = "17514f2"
        hi_on()
        STEP()

        cmd.off()
        hi_off()
        STEP()

        # Rewinding !
        cmd.on().text = "git checkout 45a5b65"
        STEP()

        hi_label(head, True)
        STEP()

        head_detached("45a5b65")
        STEP()

        f_readme.mod = d_readme.mod = "m"
        f_regina.mod = d_regina.mod = "-"
        d_readme.set_mod("-", 1, -1)
        d_regina.set_mod("-", 0, -1)
        STEP()

        d_readme.delete_lines(1, -1)
        f_readme.mod = d_readme.mod = "0"
        ft.erase(f_regina)
        df.erase(d_regina)
        STEP()

        cmd.off()
        hi_label(head, False)
        STEP()

        cmd.on().text = "git checkout d1e8c8c"
        hi_label(head, True)
        STEP()

        ft.erase(f_margherita)
        df.erase(d_margherita)
        d_readme.delete_lines(0, -1)
        d_readme.append_text(readme_text[0])
        head_detached("d1e8c8c")
        STEP()

        hi_label(head, False)
        cmd.off()
        STEP()

        hi_on()
        STEP()
        hi_off()

        cmd.on().text = "git checkout 17514f2"
        STEP()

        cmd.on().text = "git checkout main"
        hi_label(main, True)
        STEP()

        f_margherita = ft.append(
            "AppendSibling", connect=True, filename="margherita.md"
        )
        d_margherita = df.append(filename="margherita.md")
        d_margherita.append_text(margherita_text[0] + margherita_text[1])
        f_regina = ft.append("AppendSibling", connect=True, filename="regina.md")
        d_regina = df.append(filename="regina.md")
        d_regina.append_text(regina_text[0])
        d_readme.append_text(readme_text[1])
        head_on_main()
        STEP()

        hi_label(main, False)
        cmd.off()
        STEP()

        image.on().file = "VariousPizzas"
        STEP()

        return rp, ft, df
