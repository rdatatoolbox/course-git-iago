"""Modifiers concerned with the global structure of the tex file to edit.
"""

import os
from pathlib import Path
import re
import shutil as shu
from typing import Any, Tuple
from typing import Callable, List, cast

from modifiers import (
    Constant,
    MakePlaceHolder,
    PlaceHolder,
    PlaceHolderBuilder,
    TextModifier,
    render_method,
)
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

    @render_method
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
        # Restrict to the given slide name (all steps) or to only 1 step
        # (counting from 1 and from the first step in the first slide)
        only_slide: str | int | range | None = None,
        # Restrict to only 1 step with the give slide name.
        only_step: int | range | None = None,  # Counting from 1.
    ):
        """Render to a file then compile in tex folder and copy result to destination."""
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
            if type(only_slide) is str:
                # Look for a slide containing the given name.
                found = False
                i = 0
                for i, slide in enumerate(self.slides):
                    if only_slide in type(slide).__name__:
                        found = True
                        break
                if not found:
                    raise ValueError(f"Found no such slide: {repr(only_slide)}")
                restrict = self.copy()
                restrict.slides = [restrict.slides[i]]
                restrict.non_slides = [
                    Constant("".join(c.render() for c in restrict.non_slides[: i + 1])),
                    Constant("".join(c.render() for c in restrict.non_slides[i + 1 :])),
                ]
                if only_step is not None:
                    if type(only_step) is int:
                        only_step = range(only_step, only_step + 1)
                    only_step = cast(range, only_step)
                    slide = restrict.slides[0]
                    slide.steps = [slide.steps[s - 1] for s in only_step]
            else:
                # Look for a specific range of steps, starting count from first slide.
                selection = (
                    range(only_slide, only_slide + 1)
                    if type(only_slide) is int
                    else cast(range, only_slide)
                )
                restrict = self.copy()
                i_abs = 1
                for slide in restrict.slides:
                    steps = slide.steps
                    slide.steps = []
                    for step in steps:
                        if i_abs in selection:
                            slide.steps.append(step)
                        i_abs += 1
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
    Like Step, keep a meta-list of subclasses to be matched against document data
    for finding the correct type to construct.
    """

    def __init__(self, name: str, input: str):
        self.name = name
        bodies = input.split(r"\Step{")
        header = bodies.pop(0).strip()
        bodies = [b.rsplit("}", 1)[0].strip() for b in bodies]
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

    @render_method
    def render(self) -> str:
        return " {}\n{}\n{} ".format(
            self.name,
            self.header.raw,
            "\n".join("\\Step{{\n{}  \n}}".format(s.render()) for s in self.steps),
        )

    def pop_step(self) -> Step:
        """Useful to start from what's initially in the stub document
        but without using it.
        """
        return self.steps.pop()

    def add_step(self, step: Step):
        """Copy current state and record into the document."""
        self.steps.append(step.copy())

    def animate(self, *args, **kwargs) -> Any:
        """Override to construct individual steps from the current ones.
        Only called once during the generation process,
        in a state where only the stub step(s) are present.
        Default to doing nothing.
        Return possible interesting data for later use by the other slides.
        """
        pass


def FindPlaceHolder(name: str) -> Tuple[type, PlaceHolderBuilder[PlaceHolder]]:
    r"""Scan *.tex files until the given name is found inside a `\NewDocumentCommand`.
    Parse it to construct the correct pattern / options to `MakePlaceHolder()`.
    Use special comments on top of the command to retrieve arguments / fields names.
    `O{default}` arguments become options with the given default value,
    while `m` arguments become just positional.
    In a nutshell, factorize the recurrent, tedious:

        MakePlaceHolder(
            "Branch",
            r"\Branch[<color>][<anchor>][<style>]{<hash>}{<offset>}{<local>}{<name>}",
            color="Blue4",
            anchor="base",
            style="label",
        )

    Into:

        FindPlaceHolder("Branch")

    Because all the information can be just read from latex files.

    """

    # Most generic form with NewDocumentCommand.
    needle_ndc = re.compile(
        r"%\s*((?:\[.*?]\s*)*)"  # Optional arguments names.
        r"((?:{.*?}\s*)*)"  # Positional arguments names.
        r"\\NewDocumentCommand{\\" + name + "}"  # Command name.
        r"{\s*((?:O{.*?}\s*)*)"  # Optional argumens values.
        r"((?:m\s*)*)}"  # Mandatory arguments (no actual information except number).
    )
    # Less generic form with newcommand and only positional arguments.
    needle_nc = re.compile(
        r"%\s*((?:{.*?}\s*)*)"  # Positional arguments names.
        r"\\newcommand{\\" + name + "}"  # Command name.
        r"\[(.*?)]"  # Number of arguments.
    )

    found = False
    onames = pnames = ovalues = pnumber = ""
    for file in Path(".").rglob("*.tex"):

        with open(file, "r") as file:
            content = file.read()

        if m := needle_ndc.search(content):
            found = True
            # Extract all information from the match.
            onames, pnames, ovalues, pnumber = m.groups()
            pnumber = len(l := pnumber.strip().split())
            assert set(l) == {"m"}

        elif m := needle_nc.search(content):
            found = True
            pnames, pnumber = m.groups()
            pnumber = int(pnumber)

        if found:

            # Extract all informations from either match.
            onames, pnames, ovalues = (
                [r.rsplit(c, 1)[0] for r in raw.strip().split(o)[1:]]
                for (raw, (o, c)) in zip(
                    (onames, pnames, ovalues), ("[]", "{}", ("O{", "}"))
                )
            )

            # Check that parameters numbers are consistent with each other.
            assert pnumber == len(pnames)
            assert len(onames) == len(ovalues)

            # Ready to construct associated python types.
            pattern = (
                "\\"
                + name
                + "".join(f"[<{o}>]" for o in onames)
                + "".join(f"{{<{p}>}}" for p in pnames)
            )
            options = {k: v for k, v in zip(onames, ovalues)}
            return MakePlaceHolder(name, pattern, **options)

    raise ValueError(
        f"Could not find `\\NewDocumentCommand{{\\{name}}}` "
        f"or `\\newcommand{{\\{name}}}` in .tex files? "
        f"At least not associated with the appropriate special comment line."
    )


# Common commands.
HighlightSquareModifier, HighlightSquare = FindPlaceHolder("HighlightSquare")
HighlightShadeModifier, HighlightShade = FindPlaceHolder("HighlightShade")
IntensiveCoordinatesModifier, IntensiveCoordinates = FindPlaceHolder(
    "IntensiveCoordinates"
)
