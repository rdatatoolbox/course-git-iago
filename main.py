"""Grab all `Step` sections in the main.tex file
and duplicate / modify them for animation.
"""

from pathlib import Path
from typing import cast

from document import Document
from repo import Branch, Head
from slides import Pizzas

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

# Duplicate with small modifications.
step = cast(Pizzas, pizzas.pop_step())
ft = step.filetree

ft.clear()
root = ft.append("FirstFile", pos="Canvas.north west", filename="pizzas", type="folder")
git = ft.append("FirstChild", filename=".git", type="folder")
t_readme = ft.append("AppendSibling", filename="README.md", connect=True)
t_margherita = ft.append("AppendSibling", filename="margherita.md", connect=True)
t_regina = ft.append("AppendSibling", filename="regina.md", connect=True, last=True)

df = step.diffs
df.clear()
d_readme = df.append(pos="Canvas.north east", filename="README.md")
d_readme.set_text(
    """
    Collect and distribute the best pizzas recipes.

    Where to find the pizza in the project:

    - __Margherita__: `./margherita.md`
    - __Regina__: `./regina.md`
    """
)
d_margherita = df.append(filename="margherita.md")
d_margherita.set_text(
    """
    # Margerita

    The simplest and most famous,
    the one to pick when you're unsure
    whether the cook is good.

    __Base:__ tomato sauce
    __Topping:__
    - Mozzarella
    - Basil

    *Note:*
    It is said that this pizza
    has only three ingredients
    corresponding to the three colors
    on the Italian flag.
    Nevertheless, it is always good
    and *authorized* to add
    olive oil, salt, or oregano.
    """
)
d_regina = df.append(filename="regina.md")
d_regina.set_text(
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
)

rp = step.repo
rp.clear()
rp.commits.append("01e8c8c", "First commit, the intent.")
rp.commits.append("4e29052", "First pizza: Margherita.")
rp.commits.append("45a5b65", "Add note to the Margherita.")
rp.commits.append("17514f2", "Add Regina. List pizzas in README.")
rp.labels.append("Blue4", "17514f2", "40:20", "-.5:0", "main")
rp.labels.append("45a5b65", "155:20", ".5:0")

pizzas.add_step(step)

doc.compile("res.pdf", 1, 0)
