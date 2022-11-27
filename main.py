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
from title import TitleSlide

main_tex = Path("tex", "main.tex")
with open(main_tex, "r") as file:
    content = file.read()

doc = Document(content)

# Extract all slides individually.
(title, clients, pizzas, stage, remote, conflicts) = cast(
    Tuple[
        TitleSlide,
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

# Here are the new slides now that some have been 'split'ted.
(
    title,
    clients,
    pizzas,
    stage,
    remote,
    collaborate,
    fork,
    fusion,
    propagate_merge,
    propagate_rebase,
    conflicts,
) = doc.slides

# Reorganize, inserting transitions.
transition = lambda t: title.split("Title", t, step=title.steps[0].copy())
doc.slides = [
    transition("The Various Git Clients"),
    clients,
    transition("Pizzas with Git"),
    pizzas,
    transition("How to Make a Commit"),
    stage,
    transition("Share Your Project Online"),
    remote,
    transition("Collaborate"),
    collaborate,
    transition("Collaboration Divergence"),
    fork,
    transition("Conflicts"),
    conflicts,
    transition("Integrate Diverging Works"),
    fusion,
    propagate_merge,
    propagate_rebase,
]

# Setup page numbers and progress.
total = len(doc.slides)
n_steps = sum(len(slide.steps) for slide in doc.slides)
i_slide = 1
i_step = 1
for slide in doc.slides:
    if not isinstance(slide, TitleSlide):
        slide.header.page = str(i_slide)
        i_slide += 1
    for step in slide.steps:
        step.intro.progress = f"{i_step}/{n_steps}"
        i_step += 1

doc.generate_tex("Staging")

doc.compile("res.pdf")
