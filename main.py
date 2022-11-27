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
from transition import TransitionSlide
from title import TitleSlide

main_tex = Path("tex", "main.tex")
with open(main_tex, "r") as file:
    content = file.read()

doc = Document(content)

# Extract all slides individually.
(title, transition, clients, pizzas, stage, remote, conflicts) = cast(
    Tuple[
        TitleSlide,
        TransitionSlide,
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
    transition,
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
ts = lambda t: transition.split("Transition", t, step=transition.steps[0].copy())
doc.slides = [
    title,
    ts("The Various Git Clients"),
    clients,
    ts("Pizzas with Git"),
    pizzas,
    ts("How to Make a Commit"),
    stage,
    ts("Share Your Project Online"),
    remote,
    ts("Collaborate"),
    collaborate,
    ts("Collaboration Divergence"),
    fork,
    ts("Conflicts"),
    conflicts,
    ts("Integrate Diverging Works"),
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
    if not isinstance(slide, TransitionSlide):
        slide.header.page = str(i_slide)
        i_slide += 1
    for step in slide.steps:
        step.intro.progress = f"{i_step}/{n_steps}"
        i_step += 1

doc.generate_tex("Title")

doc.compile("res.pdf")
