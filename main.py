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
cm = cast(Command, step.command)
ft.clear()
df.clear()
rp.clear()
cm._visible = False
STEP = lambda: pizzas.add_step(step)

root = ft.append("FirstFile", pos="Canvas.north west", filename="pizzas", type="folder")
readme = ft.append("FirstChild", filename="README.md")
d_readme = df.append(pos="Canvas.north east", filename="README.md")
d_readme.set_text(
    """
    Collect and distribute the best pizzas recipes.

    """
)
STEP()

cm._visible = True
cm.cmd = "git init"
STEP()

doc.compile("res.pdf", 1)
