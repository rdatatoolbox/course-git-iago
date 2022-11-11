"""Grab all `Step` sections in the main.tex file
and duplicate / modify them for animation.
"""

from pathlib import Path
from textwrap import dedent

from modifiers import Document, Regex

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
step = pizzas.steps[0].copy()
step.filetree.git.mod = "+"
step.filetree.readme.mod = "-"
step.filetree.margherita.mod = "m"
step.filetree.regina.filename = r"da\_queen.md"

pizzas.steps.append(step)

doc.compile("res.pdf")
