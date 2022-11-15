"""Good example of simple slide to animate simply with various chunks."""

from typing import cast

from document import Slide
from modifiers import Constant, MakeListOf
from steps import Step


ListOfChunks = MakeListOf(Constant, sep="\n\n", head=True, tail=True)


class ClientsStep(Step, ListOfChunks):  # type: ignore
    """Good example of simple slide to animate simply with various chunks."""


class ClientsSlide(Slide):
    def animate(self):
        step = cast(ClientsStep, self.pop_step())
        STEP = lambda: self.add_step(step)

        (
            git,
            console,
            vscode,
            rstudio,
            github,
            gitlab,
            arrows,
            highlight,
        ) = [m.off() for m in step.list]

        git.on()
        STEP()

        console.on()
        vscode.on()
        rstudio.on()
        STEP()

        github.on()
        gitlab.on()
        STEP()

        arrows.on()
        highlight.on()
        STEP()
