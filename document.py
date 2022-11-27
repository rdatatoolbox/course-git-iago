"""Modifiers concerned with the global structure of the tex file to edit.
"""

import os
from pathlib import Path
import re
import shutil as shu
from textwrap import dedent
from typing import Any, Tuple
from typing import Callable, List, Self, cast

from modifiers import (
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
        self.slides: List[Slide] = []
        chunks = input.split(self._startmark)
        self.head = chunks.pop(0)
        end = ""
        for c in chunks:
            s, end = c.rsplit(self._endmark, 1)
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
            assert SlideType
            self.slides.append(SlideType(name, s, self))
        self.tail = end

    @render_method
    def render(self) -> str:
        result = self.head
        for slide in self.slides:
            result += self._startmark + slide.render() + self._endmark + "\n\n"
        result += self.tail
        return result

    @property
    def build_folder(self) -> Path:
        build = Path("tex")
        if not os.path.exists(build):
            raise RuntimeError(f"Could not find {build} folder.")
        return build

    @property
    def genbasename(self) -> str:
        return "generated_steps"

    @property
    def texfile(self) -> Path:
        return Path(self.build_folder, self.genbasename + ".tex")

    @property
    def pdffile(self) -> Path:
        return Path(self.build_folder, self.genbasename + ".pdf")

    def generate_tex(
        self,
        slidename: str | int | None = None,
        start: int | None = None,
        stop: int | None = None,
    ):
        """Render to the generated file, possibly restricting to only a few steps.

            i : only step i (absolute, 1-starting)
            i, j : only steps i to j (included, absolute)
            name : only this slide (all steps)
            name, i : only this step in the slide (relative)
            name, i, j: only steps i to j in the slide (included, relative)

        Indices i and j start counting from 1 and -1 means <end>.
        """

        print(f"Select slides and steps..")
        # Construct a list of rendered slides/steps to help restricting later.
        which_rendered: List[Tuple[str, int]] = []
        if slidename is None:
            restrict = self
            # In the no-restriction case, render as abs indices to ease targetting.
            i_abs = 0
            for slide in restrict.slides:
                for _ in range(len(slide.steps)):
                    i_abs += 1
                    which_rendered.append((slide.name, i_abs))
        elif type(slidename) is str:
            # Look for a slide containing the given name.
            found = False
            last_step = 0
            for last_step, slide in enumerate(self.slides):
                if slidename in slide.name:
                    found = True
                    break
            if not found:
                raise ValueError(f"Found no such slide: {repr(slidename)}")
            restrict = self.copy()
            restrict.slides = [slide := restrict.slides[last_step]]
            if start is None:
                # All steps rendered.
                selection = range(len(slide.steps))
            elif stop is None:
                # One step rendered.
                selection = range(start - 1, start)
            elif stop == -1:
                # Render from target step to the end.
                selection = range(start - 1, len(slide.steps))
            else:
                # Render given (inclusive) range.
                selection = range(start - 1, stop)
            steps = slide.steps
            slide.steps = []
            for s in selection:
                slide.steps.append(steps[s])
                which_rendered.append((slide.name, s + 1))
        else:
            sstart = cast(int, slidename)
            restrict = self.copy()
            # Look for a specific range of steps, starting count from first slide.
            if (sstop := start) is None:
                # Only one desired.
                selection = range(sstart - 1, sstart)
            elif sstop == -1:
                # Render for current to the end.
                selection = range(
                    sstart - 1,
                    sum(len(slide.steps) for slide in restrict.slides),
                )
            else:
                # Render to the desired absolute index.
                selection = range(sstart - 1, sstop)
            i_abs = 0
            for slide in restrict.slides:
                steps = slide.steps
                slide.steps = []
                for step in steps:
                    if i_abs in selection:
                        which_rendered.append((slide.name, i_abs + 1))
                        slide.steps.append(step)
                    i_abs += 1

        print(f"Render to {self.texfile}..")
        with open(self.texfile, "w") as file:
            file.write(restrict.render())

        print("All the following slides/steps have been rendered:")
        current_slide = ""
        step = previous_step = 0  # To shorten e.g. 1 2 3 5 6 into 1:3 5:6
        res = ""
        for slide, step in which_rendered:
            if not current_slide or slide != current_slide:
                if current_slide and res.endswith("-"):
                    res += str(previous_step)
                res += f"\n  {slide}: {step}"
                current_slide = slide
                previous_step = step
            else:
                if step == cast(int, previous_step) + 1:
                    if not res.endswith("-"):
                        res += "-"
                    previous_step = step
                else:
                    res += f"{previous_step} {step}"
        if res.endswith("-"):
            res += str(previous_step)
        print(res + "\n")

    def compile(self, filename: str):
        """Assuming all steps have been generated to the correct file,
        compile with latex then copy to desired location.
        """
        output = Path(filename)

        print(f"Compiling {self.texfile}..")
        current_folder = os.getcwd()
        os.chdir(self.build_folder)
        # Cleanup any previous build.
        for file in Path(".").rglob(self.genbasename + "*"):
            if not str(file).endswith(".tex"):
                file.unlink()
        # Compile three times so `remember pictures` eventually works.
        for _ in range(3):
            assert not os.system(f"lualatex --halt-on-error {self.genbasename}.tex")
        os.chdir(current_folder)

        print(f"Copy to {output}..")
        shu.copy(self.pdffile, output)

        print("done.")


SlideHeaderModifier, SlideHeader = MakePlaceHolder(
    "SlideHeader",
    dedent(
        r"""
        \renewcommand{\TitleText}{<title>}
        \renewcommand{\SubTitleText}{<subtitle>}
        \renewcommand{\PageNumText}{<page>}<tail>
        """
    ).strip(),
)


class Slide(TextModifier):
    """The slide section is parsed for header and body.
    Bodies may be multiplied and edited into steps, but the header remains the same.
    The section name determines which parser to use for the body.
    Like Step, keep a meta-list of subclasses to be matched against document data
    for finding the correct type to construct.

    The slide keeps a cross-reference to the containing document,
    so that it's possible to transform current step into a new slide
    during the "animate" function, a process called 'split'.
    """

    def __init__(self, name: str, input: str, document: Document):
        """Assume there is only one step during parsing."""
        self._document = document
        self.name = name
        # Split on \Step command but preserve options.
        prefix = re.compile(r"\\Step(\[.*?\])?{")
        head, options, body = (
            cast(str, "" if b is None else b) for b in prefix.split(input, 1)
        )
        self.header = SlideHeader.parse(head)
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
        self.steps = [
            cast(Step, cast(Callable, StepType)(r"\Step" + options + "{" + body))
        ]

    def copy(self):
        """Don't copy backref to the document,
        the document referred to remains the same when the slide is copied.
        """
        doc = self._document
        self._document = None
        new = super().copy()
        new._document = doc
        self._document = doc
        return new

    @render_method
    def render(self) -> str:
        return " {}\n{}\n{} ".format(
            self.name,
            self.header.render(),
            "\n".join(s.render() for s in self.steps),
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

    def split(
        self,
        name: str,
        title: str | None = None,
        subtitle: str | None = None,
        step: Step | None = None,
    ) -> Self:
        """Split self into a new slide with possibly new title(s),
        and correctly insert it into the document.
        The newly created slide only contains a copy of the given step.
        """
        # Find ourselves within the document.
        assert self._document
        slides = self._document.slides
        i = slides.index(self)
        # Insert a copy with only one step right after self.
        fork = self.copy()
        fork.steps = [step.copy()] if step else []
        fork.name = name
        fork.header.title = title if title else self.header.title
        fork.header.subtitle = subtitle if subtitle else self.header.subtitle
        slides.insert(i + 1, fork)
        return fork


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
HighlightSquareRingModifier, HighlightSquareRing = FindPlaceHolder(
    "HighlightSquareRing"
)
HighlightShadeModifier, HighlightShade = FindPlaceHolder("HighlightShade")
IntensiveCoordinatesModifier, IntensiveCoordinates = FindPlaceHolder(
    "IntensiveCoordinates"
)
AutomaticCoordinatesModifier, AutomaticCoordinates = FindPlaceHolder(
    "AutomaticCoordinates"
)
