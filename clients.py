"""Good example of simple slide to animate simply with various chunks."""

from typing import cast

from document import Slide
from modifiers import ConstantBuilder, ListBuilder
from steps import Step


ListOfChunks = ListBuilder(
    ConstantBuilder,
    "\n\n",
    head=True,
    tail=True,
)


class ClientsStep(Step):
    """Good example of simple slide to animate simply with various chunks."""

    def __init__(self, input: str):
        self.list = ListOfChunks.parse(input)

    def render(self) -> str:
        return self.list.render()


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
