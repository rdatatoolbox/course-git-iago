"""Grab all `Step` sections in the main.tex file
and duplicate / modify them for animation.
"""

from pathlib import Path
from typing import Tuple, cast

from clients import ClientsSlide
from document import Document
from pizzas import PizzasSlide
from remote import RemoteSlide

main_tex = Path("tex", "main.tex")
with open(main_tex, "r") as file:
    content = file.read()

doc = Document(content)

# Extract all slides individually.
(clients, pizzas, remote) = cast(
    Tuple[
        ClientsSlide,
        PizzasSlide,
        RemoteSlide,
    ],
    doc.slides,
)

# Animate, taking care of dependencies among slides.
clients.animate()
rp, ft, df = pizzas.animate()
remote.animate(rp, ft, df)

# Setup page numbers and progress.
total = len(doc.slides)
for i, slide in enumerate(doc.slides):
    pagenum = str(i + 1)
    slide.header.page = pagenum
    slide.header.progress = f"{pagenum}/{total}"

doc.generate_tex(48, -1)

doc.compile("res.pdf")
