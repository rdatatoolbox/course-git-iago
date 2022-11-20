"""The slide with repo / project folder / file content."""

from typing import Tuple, cast

from diffs import DiffList
from document import HighlightSquare, Slide
from filetree import FileTree
from modifiers import AnonymousPlaceHolder, render_method
from repo import Command, Repo
from steps import Step


class PizzasStep(Step):
    """The slide with repo / project folder / file content."""

    def __init__(self, input: str):
        chunks = input.split("\n\n")
        it = iter(chunks)
        self.filetree = FileTree(next(it))
        self.diffs = DiffList(next(it))
        self.repo = Repo(next(it), "50, 5")
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
        files = step.filetree
        diffs = step.diffs
        repo = step.repo
        command = step.command
        files.clear()
        diffs.clear()
        command.off()
        repo.off()
        STEP = lambda: self.add_step(step)

        image = step.add_epilog(
            AnonymousPlaceHolder(
                r"\node (im) at (Canvas.center) {\Pic<file>{15cm}{!}};",
                "new",
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
        _ = files.append(
            "FirstFile", pos="Canvas.north west", filename="pizzas", type="folder"
        )
        f_readme = files.append("FirstChild", filename="README.md")
        d_readme = diffs.append(pos="Canvas.north east", filename="README.md")
        d_readme.append_text(readme_text[0])
        STEP()

        image.off()
        STEP()

        # Git init.
        command._rendered = True
        command.on().text = "git init"
        STEP()

        files.erase(f_readme)
        git = files.append(
            "FirstChild",
            type="folder",
            filename=".git",
            mod="+",
            name="git",
        )
        f_readme = files.append("AppendSibling", filename="README.md", connect=True)
        STEP()

        hi_gitfolder = git.add_epilog(
            HighlightSquare.new(
                "git.south west",
                "file-label.east |- git.north",
                padding=2,
            )
        ).off()

        hi_on = lambda: (hi_gitfolder.on(), repo.highlight(True))
        hi_off = lambda: (hi_gitfolder.off(), repo.highlight(False))

        git.mod = "0"
        command.off()
        STEP()

        hi_on()
        repo.on()
        STEP()

        hi_off()
        STEP()

        # First commit.
        command.on().text = "git commit"
        STEP()

        repo.add_commit("I", "d1e8c8c", "First commit, the intent.")
        hi_on()
        STEP()

        hi_off()
        command.off()
        STEP()

        # Adding Margherita
        command.off()
        f_margherita = files.append(
            "AppendSibling", connect=True, filename="margherita.md"
        )
        d_margherita = diffs.append(filename="margherita.md")
        d_margherita.append_text(margherita_text[0])
        image.on().file = "Margherita"
        STEP()

        image.off()
        STEP()

        command.on().text = "git diff"
        STEP()

        f_margherita.mod = d_margherita.mod = "+"
        d_margherita.set_mod("+", 0, -1)
        STEP()

        command.on().text = "git commit"
        f_margherita.mod = d_margherita.mod = "0"
        d_margherita.set_mod("0", 0, -1)
        repo.add_commit("I", "4e29052", "First pizza: Margherita.")
        hi_on()
        STEP()

        command.off()
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
        command.on().text = "git diff"
        STEP()

        command.on().text = "git commit"
        f_margherita.mod = d_margherita.mod = "0"
        d_margherita.set_mod("0", 0, -1)
        repo.add_commit("I", "45a5b65", "Add note to the Margherita.")
        hi_on()
        STEP()

        command.off()
        hi_off()
        STEP()

        # Adding Regina.
        d_readme.append_text(readme_text[1])
        f_regina = files.append("AppendSibling", connect=True, filename="regina.md")
        d_regina = diffs.append(filename="regina.md")
        d_regina.append_text(regina_text[0])
        image.on().file = "Regina"
        STEP()

        image.off()
        STEP()

        f_readme.mod = d_readme.mod = "m"
        d_regina.mod = f_regina.mod = "+"
        d_regina.set_mod("+", 0, -1)
        d_readme.set_mod("+", 1, -1)
        command.on().text = "git diff"
        STEP()

        command.on().text = "git status"
        d_readme.mod = "0"
        d_regina.mod = "0"
        d_readme.set_mod("0", 0, -1)
        d_regina.set_mod("0", 0, -1)
        STEP()

        d_readme.mod = d_regina.mod = f_regina.mod = f_readme.mod = "0"
        command.on().text = "git commit"
        repo.add_commit("I", "17514f2", "Add Regina. List pizzas in README.")
        hi_on()
        STEP()

        command.off()
        hi_off()
        STEP()

        # Rewinding !
        command.on().text = "git checkout 45a5b65"
        STEP()

        repo.highlight(True, "HEAD")
        STEP()

        repo.checkout_detached("45a5b65")
        STEP()

        f_readme.mod = d_readme.mod = "m"
        f_regina.mod = d_regina.mod = "-"
        d_readme.set_mod("-", 1, -1)
        d_regina.set_mod("-", 0, -1)
        STEP()

        d_readme.delete_lines(1, -1)
        f_readme.mod = d_readme.mod = "0"
        files.erase(f_regina)
        diffs.erase(d_regina)
        STEP()

        command.off()
        repo.highlight(False, "HEAD")
        STEP()

        command.on().text = "git checkout d1e8c8c"
        repo.highlight(True, "HEAD")
        STEP()

        files.erase(f_margherita)
        diffs.erase(d_margherita)
        d_readme.delete_lines(0, -1)
        d_readme.append_text(readme_text[0])
        repo.checkout_detached("d1e8c8c")
        STEP()

        repo.highlight(False, "HEAD")
        command.off()
        STEP()

        hi_on()
        STEP()
        hi_off()

        command.on().text = "git checkout 17514f2"
        STEP()

        command.on().text = "git checkout main"
        repo.highlight(True, "main")
        STEP()

        f_margherita = files.append(
            "AppendSibling", connect=True, filename="margherita.md"
        )
        d_margherita = diffs.append(filename="margherita.md")
        d_margherita.append_text(margherita_text[0] + margherita_text[1])
        f_regina = files.append("AppendSibling", connect=True, filename="regina.md")
        d_regina = diffs.append(filename="regina.md")
        d_regina.append_text(regina_text[0])
        d_readme.append_text(readme_text[1])
        repo.checkout_branch("main")
        STEP()

        repo.highlight(False, "main")
        command.off()
        STEP()

        image.on().file = "VariousPizzas"
        STEP()

        return repo, files, diffs
