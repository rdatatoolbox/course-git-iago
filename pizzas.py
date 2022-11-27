"""The slide with repo / project folder / file content."""

from typing import List, Tuple, cast

from diffs import DiffedFile
from document import Slide
from filetree import FileTree
from modifiers import AnonymousPlaceHolder
from repo import Command, Repo
from steps import Step


class PizzasStep(Step):
    """The slide with repo / project folder / file content."""

    def parse_body(self):
        input = self.body
        chunks = input.split("\n\n")
        it = iter(chunks)
        self.filetree = FileTree(next(it))
        self.diff = DiffedFile(next(it))
        self.repo = Repo(next(it))
        self.command = Command.parse(next(it))
        try:
            while some := next(it):
                assert not some
        except StopIteration:
            pass

    def render_body(self) -> str:
        return "\n\n".join(
            m.render()
            for m in [
                self.filetree,
                self.diff,
                self.repo,
                self.command,
            ]
        )


class PizzasSlide(Slide):
    """Animate pizzas slide so it reproduces the small git history."""

    def animate(self) -> Tuple[Repo, FileTree, List[DiffedFile]]:

        # Use this dynamical step as a workspace for edition,
        # regularly copied into actually recorded steps.
        step = cast(PizzasStep, self.pop_step())

        STEP = lambda: self.add_step(step)

        files = step.filetree.clear()
        # There will actually be 3 diffs slots,
        # this original diff will therefore be forked in the epilog.
        diff = step.diff.clear().off()
        repo = step.repo.off()
        command = step.command.off()

        repo.intro.location = '-.82, -.94'

        image = step.add_epilog(
            AnonymousPlaceHolder(
                r"\node (im) at (Canvas.center) {\Pic<file>{<width>}{!}};",
                "new",
                file="VariousPizzas",
                width="25cm",
            )
        ).on()
        STEP()

        readme_text = [
            """
            Collect and distribute the best pizzas recipes.
            """,
            """

            Where to find the pizzas in the project:

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
        _ = files.append("pizzas", "folder")
        f_readme = files.append("README.md", "stepin")
        d_readme = (
            diff.on()
            .set_name("diff1")
            .set_filename(f_readme.filename)
            .insert_lines(readme_text[0])
        )
        STEP()

        image.off()
        STEP()

        # Git init.
        command._rendered = True
        command.on().text = r"git \gkw{init}"
        STEP()

        files.pop(f_readme)
        git = files.append(".git", "folder stepin", "+")
        f_readme = files.append("README.md")
        STEP()

        hi_gitfolder = files.highlight("git").off()

        git.mod = "0"
        command.off()
        STEP()

        hi_gitfolder.on()
        safe_loc = repo.intro.location
        repo.intro.location = "-.73, -.95" # Temporary relocate when empty.
        repo.on()
        repo.hi_on()
        STEP()

        hi_gitfolder.off()
        repo.hi_off()
        STEP()

        # First commit.
        command.on().text = r"git \gkw{commit}"
        STEP()

        c = repo.add_commit("I", "d1e8c8c", "First commit, the intent.")
        hi_gitfolder.on()
        repo.hi_on(c)
        repo.intro.location = safe_loc
        STEP()

        hi_gitfolder.off()
        repo.hi_off(c)
        command.off()
        STEP()

        # Adding Margherita
        command.off()
        f_margherita = files.append("margherita.md")
        d_margherita = (
            step.add_epilog(diff.copy().clear())
            .set_name("diff2")
            .set_filename(f_margherita.filename)
            .insert_lines(margherita_text[0])
        )
        d_margherita.intro.location = "below=8 of diff1.south east"
        image.on().file = "Margherita"
        image.width = "17.5cm"
        STEP()

        image.off()
        STEP()

        command.on().text = r"git \gkw{diff}"
        STEP()

        f_margherita.mod = d_margherita.mod = "+"
        d_margherita.set_mod("+", 1, -1)
        hi_gitfolder.on()
        repo.hi_on(c)
        STEP()

        hi_gitfolder.off()
        repo.hi_off(c)
        command.off()
        STEP()

        command.on().text = "git commit"
        f_margherita.mod = d_margherita.mod = "0"
        d_margherita.set_mod("0", 1, -1)
        c = repo.add_commit("I", "4e29052", "First pizza: Margherita.")
        hi_gitfolder.on()
        repo.hi_on(c)
        STEP()

        command.off()
        hi_gitfolder.off()
        repo.hi_off(c)
        STEP()

        # Editing Margherita
        d_margherita.insert_lines(margherita_text[1])
        image.on()
        STEP()

        image.off()
        STEP()

        f_margherita.mod = d_margherita.mod = "m"
        d_margherita.set_mod("+", 11, -1)
        command.on().text = "git diff"
        STEP()

        command.on().text = "git commit"
        f_margherita.mod = d_margherita.mod = "0"
        d_margherita.set_mod("0", 1, -1)
        c = repo.add_commit("I", "45a5b65", "Add note to the Margherita.")
        repo.hi_on(c)
        hi_gitfolder.on()
        STEP()

        command.off()
        hi_gitfolder.off()
        repo.hi_off(c)
        STEP()

        # Adding Regina.
        d_readme.insert_lines(readme_text[1], 2)
        f_regina = files.append("regina.md")
        d_regina = (
            step.add_epilog(diff.copy().clear())
            .set_name("diff3")
            .set_filename(f_regina.filename)
            .insert_lines(regina_text[0])
        )
        d_regina.intro.location = d_margherita.intro.location.replace("diff1", "diff2")
        image.on().file = "Regina"
        STEP()

        image.off()
        STEP()

        f_readme.mod = d_readme.mod = "m"
        d_regina.mod = f_regina.mod = "+"
        d_regina.set_mod("+", 1, -1)
        d_readme.set_mod("+", 2, -1)
        command.on().text = "git diff"
        STEP()

        command.on().text = r"git \gkw{status}"
        d_readme.mod = "0"
        d_regina.mod = "0"
        d_readme.set_mod("0", 1, -1)
        d_regina.set_mod("0", 1, -1)
        STEP()

        command.off()
        STEP()

        d_readme.mod = d_regina.mod = f_regina.mod = f_readme.mod = "0"
        command.on().text = "git commit"
        c = repo.add_commit("I", "17514f2", "Add Regina. List pizzas in README.")
        hi_gitfolder.on()
        repo.hi_on(c)
        STEP()

        command.off()
        hi_gitfolder.off()
        repo.hi_off(c)
        STEP()

        # Rewinding !
        command.on().text = r"git \gkw{checkout} 45a5b65"
        STEP()

        repo.highlight("HEAD")
        STEP()

        repo.checkout_detached("45a5b65")
        STEP()

        f_readme.mod = d_readme.mod = "m"
        f_regina.mod = d_regina.mod = "-"
        d_readme.set_mod("-", 2, -1)
        d_regina.set_mod("-", 1, -1)
        STEP()

        d_readme.erase_lines(2, -1)
        f_readme.mod = d_readme.mod = "0"
        files.pop(f_regina)
        d_regina.off()
        STEP()

        command.off()
        repo.hi_off("HEAD")
        STEP()

        command.on().text = r"git \gkw{checkout} d1e8c8c"
        repo.highlight("HEAD")
        STEP()

        files.pop(f_margherita)
        d_margherita.off()
        d_readme.clear()
        d_readme.insert_lines(readme_text[0])
        repo.checkout_detached("d1e8c8c")
        STEP()

        repo.hi_off("HEAD")
        command.off()
        STEP()

        hi_gitfolder.on()
        repo.hi_on()
        STEP()

        hi_gitfolder.off()
        repo.hi_off()
        STEP()

        command.on().text = "git checkout 17514f2"
        STEP()

        command.on().text = r"git checkout \ghi{main}"
        repo.highlight("main")
        STEP()

        f_margherita = files.append("margherita.md")
        f_regina = files.append("regina.md")
        d_margherita.on()
        d_regina.on().reset()
        d_readme.insert_lines(readme_text[1], 2)
        repo.checkout_branch("main")
        STEP()

        repo.hi_off("main")
        command.off()
        STEP()

        image.on().file = "VariousPizzas"
        STEP()

        return repo, files, [d_readme, d_margherita, d_regina]
