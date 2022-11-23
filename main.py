"""Grab all `Step` sections in the main.tex file
and duplicate / modify them for animation.
"""

from pathlib import Path
from typing import Tuple, cast

from clients import ClientsSlide
from conflicts import ConflictsSlide
from document import Document
from pizzas import PizzasSlide
from remote import RemoteSlide

main_tex = Path("tex", "main.tex")
with open(main_tex, "r") as file:
    content = file.read()

doc = Document(content)

# Extract all slides individually.
(clients, pizzas, remote, conflicts) = cast(
    Tuple[
        ClientsSlide,
        PizzasSlide,
        RemoteSlide,
        ConflictsSlide,
    ],
    doc.slides,
)

# Animate, taking care of dependencies among slides.
clients.animate()
repo, filetree, diffs = pizzas.animate()
remote.animate(repo, filetree, diffs)
conflicts.animate()

# Setup page numbers and progress.
total = len(doc.slides)
for i, slide in enumerate(doc.slides):
    pagenum = str(i + 1)
    slide.header.page = pagenum
    slide.header.progress = f"{pagenum}/{total}"

doc.generate_tex("Pizzas")

doc.compile("res.pdf")
