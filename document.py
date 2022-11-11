"""Modifiers concerned with the global structure of the tex file to edit.
"""

import os
from pathlib import Path
import shutil as shu
from typing import cast, List

from modifiers import Constant, TextModifier
from slides import *


class Document(TextModifier):
    """Root-level modifier, splitting the whole file into slides to animate,
    but keeping track of preamble and what's between slides for later rendering.
    Actually a sequence of <non-slide> and <slide> chunks.
    """

    _startmark = "% SLIDE"
    _endmark = "% ENDSLIDE"

    def __init__(self, input: str):
        self.non_slides: List[Constant] = []
        self.slides : List['Slide'] = []
        chunks = input.split(self._startmark)
        self.non_slides.append(Constant(chunks.pop(0)))
        for c in chunks:
            s, ns = c.rsplit(self._endmark, 1)
            self.slides.append(Slide(s))
            self.non_slides.append(Constant(ns))

    def render(self) -> str:
        ns = iter(self.non_slides)
        s = iter(self.slides)
        result = next(ns).render()
        for (slide, non_slide) in zip(s, ns):
            result += self._startmark + slide.render() + self._endmark
            result += non_slide.render()
        return result

    def compile(self, filename: str):
        """Render to a file then compile.
        Use a temporary folder destroyed afterwards.
        """
        output = Path(filename)

        build = Path("tex")
        if not os.path.exists(build):
            raise RuntimeError(f"Could not find {build} folder.")

        current = os.getcwd()
        os.chdir(build)
        genname = "generated_steps"
        texfile = Path(genname + ".tex")
        print(f"Render to {texfile}..")
        with open(texfile, "w") as file:
            file.write(self.render())
        print(f"Compile {texfile}..")
        # Compile three times so `remember pictures` eventually works.
        for _ in range(3):
            os.system(f"lualatex {str(texfile)}")
        os.chdir(current)

        print(f"Copy to {output}..")
        shu.copy(Path(build, genname + ".pdf"), output)

        print("done.")


class Slide(TextModifier):
    """The slide section is parsed for header and body.
    Bodies may be multiplied and edited into steps, but the header remains the same.
    The section name determines which parser to use for the body.
    """

    def __init__(self, input: str):
        name, body = input.split("\n", 1)
        header, body = body.split(r"\Step{", 1)
        body, _ = body.rsplit(r"}", 1)
        self.name = name.strip()
        self.header = Constant(header)
        SlideType = eval(self.name)
        self.steps = [cast(Step, SlideType(body.rstrip()))]

    def render(self) -> str:
        return " {}\n{}{} ".format(
            self.name,
            self.header.raw,
            "\n".join(f"\\Step{{{s.render()}}}" for s in self.steps),
        )

    def pop_step(self) -> Step:
        """Useful to start from without using what's initially in the stub document."""
        return self.steps.pop()

    def add_step(self, step: Step):
        """Copy current state and record into the document.
        """
        self.steps.append(step.copy())

