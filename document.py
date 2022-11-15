"""Modifiers concerned with the global structure of the tex file to edit.
"""

import os
from pathlib import Path
import shutil as shu
from typing import Callable, List, cast

from modifiers import Constant, TextModifier, render_function
from steps import Step


class Document(TextModifier):
    """Root-level modifier, splitting the whole file into slides to animate,
    but keeping track of preamble and what's between slides for later rendering.
    Actually a sequence of <non-slide> and <slide> chunks.
    """

    _startmark = "% SLIDE"
    _endmark = "% ENDSLIDE"

    def __init__(self, input: str):
        self.non_slides: List[Constant] = []
        self.slides: List[Slide] = []
        chunks = input.split(self._startmark)
        self.non_slides.append(Constant(chunks.pop(0)))
        for c in chunks:
            s, ns = c.rsplit(self._endmark, 1)
            name, s = s.split("\n", 1)
            name = name.strip()
            # Match name against Slide type names to find the correct type.
            found = False
            SlideType = None
            for SlideType in Slide.__subclasses__():
                if name + "Slide" == SlideType.__name__:
                    found = True
                    break
            if not found:
                raise RuntimeError(
                    f"Could not match name {repr(name)} with a subclass of `Slide`."
                )
            self.slides.append(cast(Slide, cast(Callable, SlideType)(name, s)))
            self.non_slides.append(Constant(ns))

    @render_function
    def render(self) -> str:
        ns = iter(self.non_slides)
        s = iter(self.slides)
        result = next(ns).render()
        for (slide, non_slide) in zip(s, ns):
            result += self._startmark + slide.render() + self._endmark
            result += non_slide.render()
        return result

    def compile(
        self,
        filename: str,
        only_slide: int | None = None,
        only_step: int | None = None,
    ):
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
        if only_slide is not None:
            restrict = self.copy()
            restrict.slides = [restrict.slides[only_slide]]
            restrict.non_slides = [
                Constant(
                    "".join(c.render() for c in restrict.non_slides[: only_slide + 1])
                ),
                Constant(
                    "".join(c.render() for c in restrict.non_slides[only_slide + 1 :])
                ),
            ]
            if only_step is not None:
                slide = restrict.slides[0]
                slide.steps = [slide.steps[only_step]]
        else:
            restrict = self
        with open(texfile, "w") as file:
            file.write(restrict.render())

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
    Like Step, keeps a meta-list of subclasses to be matched against document data
    for finding the correct type to construct.
    """

    def __init__(self, name: str, input: str):
        self.name = name
        bodies = input.split(r"\Step{")
        header = bodies.pop(0)
        bodies = [b.rsplit("}", 1)[0].rstrip() for b in bodies]
        self.header = Constant(header)
        # Match name against Step type names to find the correct type.
        found = False
        StepType = None
        for StepType in Step.__subclasses__():
            if name + "Step" == StepType.__name__:
                found = True
                break
        if not found:
            raise RuntimeError(
                f"Could not match name {repr(self.name)} with a subclass of `Step`."
            )
        self.steps = [cast(Step, cast(Callable, StepType)(b)) for b in bodies]

    @render_function
    def render(self) -> str:
        return " {}\n{}{} ".format(
            self.name,
            self.header.raw,
            "\n".join(f"\\Step{{{s.render()}\n}}" for s in self.steps),
        )

    def pop_step(self) -> Step:
        """Useful to start from without using what's initially in the stub document."""
        return self.steps.pop()

    def add_step(self, step: Step):
        """Copy current state and record into the document."""
        self.steps.append(step.copy())

    def animate(self):
        """Override to construct individual steps from the current ones.
        Only called once during the generation process,
        in a state where only the stub step(s) are present.
        Default to doing nothing.
        """
        pass
