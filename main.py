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
from staging import StagingSlide

main_tex = Path("tex", "main.tex")
with open(main_tex, "r") as file:
    content = file.read()

doc = Document(content)

# Extract all slides individually.
(clients, pizzas, stage, remote, conflicts) = cast(
    Tuple[
        ClientsSlide,
        PizzasSlide,
        StagingSlide,
        RemoteSlide,
        ConflictsSlide,
    ],
    doc.slides,
)

# Animate, taking care of dependencies among slides.
clients.animate()
repo, filetree, diffs = pizzas.animate()
stage.animate()
remote.animate(repo, filetree, diffs)
conflicts.animate()

# Setup page numbers and progress.
total = len(doc.slides)
n_steps = sum(len(slide.steps) for slide in doc.slides)
i_step = 0
for i_slide, slide in enumerate(doc.slides):
    pagenum = str(i_slide + 1)
    slide.header.page = pagenum
    for step in slide.steps:
        i_step += 1
        step.progress = f"{i_step}/{n_steps}"

doc.generate_tex(220, 236)

doc.compile("res.pdf")
