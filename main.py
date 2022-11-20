"""Grab all `Step` sections in the main.tex file
and duplicate / modify them for animation.
"""

from pathlib import Path
from typing import Tuple, cast

from clients import ClientsSlide
from document import Document
from fork import ForkSlide
from pizzas import PizzasSlide
from remote import RemoteSlide

main_tex = Path("tex", "main.tex")
with open(main_tex, "r") as file:
    content = file.read()

doc = Document(content)

# Extract all slides individually.
(clients, pizzas, remote, fork) = cast(
    Tuple[
        ClientsSlide,
        PizzasSlide,
        RemoteSlide,
        ForkSlide,
    ],
    doc.slides,
)

# Animate, taking care of dependencies among slides.
clients.animate()
rp, ft, df = pizzas.animate()
remote.animate(rp, ft, df)
fork.animate()

doc.compile("res.pdf", "Remote", 17, -1)
