"""Grab all `Step` sections in the main.tex file
and duplicate / modify them for animation.
"""

from pathlib import Path
from typing import cast

from document import Document
from slides import Pizzas

main_tex = Path("tex", "main.tex")
with open(main_tex, "r") as file:
    content = file.read()

doc = Document(content)

# Check that rendering works well,
# so the document is exactly the same if no modifications has been made.
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
root = ft.append("FirstFile", pos="Canvas.north west", name="A", filename="pizzas")
root.type = "folder"

pizzas.add_step(step)

git = ft.append("FirstChild", filename=".git")
git.type = "folder"
git.mod = "+"

pizzas.add_step(step)

doc.compile("res.pdf", 1, 0)
