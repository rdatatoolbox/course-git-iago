"""Grab all `Step` sections in the main.tex file
and duplicate / modify them for animation.
"""

from pathlib import Path

# All imports needed for subclasses of `Step` and `Slide` to be generated.
import clients
from document import Document
import pizzas


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

for slide in doc.slides:
    slide.animate()

doc.compile("res.pdf")
