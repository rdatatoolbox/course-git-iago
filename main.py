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

for slide in doc.slides:
    slide.animate()

doc.compile("res.pdf")
