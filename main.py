"""Grab all `Step` sections in the main.tex file
and duplicate / modify them for animation.
"""

from pathlib import Path
from typing import cast

from diffs import DiffList
from document import Document
from filetree import FileTree
from repo import Repo
from repo import Branch, Head
from slides import Pizzas, Command

main_tex = Path("tex", "main.tex")
with open(main_tex, "r") as file:
    content = file.read()

doc = Document(content)

# Check that rendering works well,
# so the document is exactly the same if no modifications has been made.
# TODO: remove this check to get more latitude with whitespacing.
if not (r := doc.render()) == content:
    filename = "wrong_render"
    with open(filename, "w") as file:
        file.write(r)
    raise ValueError(
        "Rendering without modifications did not yield a result identical to input. "
        f"Diff {repr(filename)} against {repr(str(main_tex))} to investigate."
    )

introduction, pizzas = doc.slides

# Animate pizzas slide so it reproduces the small git history.
step = cast(Pizzas, pizzas.pop_step())
ft = cast(FileTree, step.filetree)
df = cast(DiffList, step.diffs)
rp = cast(Repo, step.repo)
cmd = cast(Command, step.command)
ft.clear()
df.clear()
rp.clear()
cmd.off()
STEP = lambda: pizzas.add_step(step)

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

root = ft.append("FirstFile", pos="Canvas.north west", filename="pizzas", type="folder")
readme = ft.append("FirstChild", filename="README.md")
d_readme = df.append(pos="Canvas.north east", filename="README.md")
d_readme.append_text(readme_text[0])
STEP()

cmd._visible = True
cmd.on().text = "git init"
ft.erase(readme)
git = ft.append("FirstChild", type="folder", filename=".git", mod="+")
readme = ft.append("AppendSibling", filename="README.md", connect=True)
STEP()

cmd.text = "git commit"
rp.commits.append("01e8c8c", "First commit, the intent.")
head = cast(Head, rp.labels.append("01e8c8c", "140:20", ".5,0"))
main = cast(Branch, rp.labels.append("Blue4", "01e8c8c", "40:20", "-.5,0", "main"))
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


doc.compile("res.pdf", 1)
