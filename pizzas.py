"""The slide with repo / project folder / file content."""

from typing import cast

from diffs import DiffList
from document import Slide
from filetree import FileTree
from modifiers import TextModifier, render_function
from repo import Branch, Head, Repo
from steps import Command, Step


class PizzasStep(Step):
    """The slide with repo / project folder / file content."""

    def __init__(self, input: str):
        chunks = input.split("\n\n")
        it = iter(chunks)
        next(it)  # Ignore leading_whitespace
        self.filetree = FileTree(next(it))
        self.diffs = DiffList(next(it))
        self.repo = Repo(next(it))
        try:
            self.command = Command(next(it))
        except StopIteration:
            self.command = Command("")
        try:
            while some := next(it):
                assert not some
        except StopIteration:
            pass

    @render_function
    def render(self) -> str:
        return (
            "\n\n"
            + "\n\n".join(
                m.render() if isinstance(m, TextModifier) else m
                for m in (
                    self.filetree,
                    self.diffs,
                    self.repo,
                    self.command,
                )
            )
            + "\n"
        )


class PizzasSlide(Slide):
    """Animate pizzas slide so it reproduces the small git history."""

    def animate(self):
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
            # Margerita

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

        _ = ft.append(  # root.
            "FirstFile", pos="Canvas.north west", filename="pizzas", type="folder"
        )
        readme = ft.append("FirstChild", filename="README.md")
        d_readme = df.append(pos="Canvas.north east", filename="README.md")
        d_readme.append_text(readme_text[0])
        STEP()

        cmd._rendered = True
        cmd.on().text = "git init"
        ft.erase(readme)
        git = ft.append("FirstChild", type="folder", filename=".git", mod="+")
        readme = ft.append("AppendSibling", filename="README.md", connect=True)
        STEP()

        cmd.text = "git commit"
        rp.commits.append("01e8c8c", "First commit, the intent.")
        head = cast(Head, rp.labels.append("01e8c8c", "140:20", ".5,0"))
        main = cast(
            Branch, rp.labels.append("Blue4", "01e8c8c", "40:20", "-.5,0", "main")
        )
        git.mod = "0"
        STEP()

        cmd.off()
        STEP()

        cmd.off()
        margherita = ft.append("AppendSibling", connect=True, filename="margherita.md")
        d_margherita = df.append(filename="margherita.md")
        d_margherita.append_text(margherita_text[0])
        STEP()

        cmd.on().text = "git diff"
        margherita.mod = d_margherita.mod = "+"
        d_margherita.set_mod("+", 0, -1)
        STEP()

        cmd.text = "git commit"
        margherita.mod = d_margherita.mod = "0"
        d_margherita.set_mod("0", 0, -1)
        rp.commits.append("4e29052", "First pizza: Margerita.")
        head.hash = main.hash = "4e29052"
        STEP()

        cmd.off()
        STEP()

        margherita.mod = d_margherita.mod = "m"
        d_margherita.append_text(margherita_text[1], mod="+")
        STEP()

        cmd.on().text = "git commit"
        margherita.mod = d_margherita.mod = "0"
        d_margherita.set_mod("0", 0, -1)
        rp.commits.append("45a5b65", "Add note to the Margerita.")
        head.hash = main.hash = "45a5b65"
        STEP()

        cmd.off()
        readme.mod = d_readme.mod = "m"
        d_readme.append_text(readme_text[1], mod="+")
        regina = ft.append("AppendSibling", connect=True, filename="regina.md", mod="+")
        d_regina = df.append(filename="regina.md", mod="+")
        d_regina.append_text(regina_text[0], mod="+")
        STEP()

        cmd.on().text = "git status"
        d_readme.mod = "0"
        d_regina.mod = "0"
        STEP()

        cmd.on().text = "git commit"
        readme.mod = regina.mod = "0"
        regina.mod = "0"
        d_readme.set_mod("0", 0, -1)
        d_regina.set_mod("0", 0, -1)
        rp.commits.append("17514f2", "Add Regina. List pizzas in README.")
        head.hash = main.hash = "17514f2"
        STEP()

        cmd.off()
        STEP()

        cmd.on().text = "git checkout 45a5b65"
        head.hash = "45a5b65"
        head.offset = "157:20"
        readme.mod = d_readme.mod = "m"
        regina.mod = d_regina.mod = "-"
        d_readme.set_mod("-", 1, -1)
        d_regina.set_mod("-", 0, -1)
        STEP()

        cmd.off()
        d_readme.delete_lines(1, -1)
        readme.mod = d_readme.mod = "0"
        ft.erase(regina)
        df.erase(d_regina)
        STEP()

        cmd.on().text = "git checkout 01e8c8c"
        ft.erase(margherita)
        df.erase(d_margherita)
        d_readme.delete_lines(0, -1)
        d_readme.append_text(readme_text[0])
        head.hash = "01e8c8c"
        STEP()

        cmd.off()
        STEP()

        cmd.on().text = "git checkout main"
        margherita = ft.append("AppendSibling", connect=True, filename="margherita.md")
        d_margherita = df.append(filename="margherita.md")
        d_margherita.append_text(margherita_text[0] + margherita_text[1])
        regina = ft.append("AppendSibling", connect=True, filename="regina.md")
        d_regina = df.append(filename="regina.md")
        d_regina.append_text(regina_text[0])
        d_readme.append_text(readme_text[1])
        head.hash = "17514f2"
        head.offset = "140:20"
        STEP()

        cmd.off()
        STEP()
