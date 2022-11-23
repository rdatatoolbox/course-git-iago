"""Slide to explain diffs, conflict and markers.
"""

from document import Slide
from modifiers import Constant, render_method
from steps import Step


class ConflictsStep(Step):
    def __init__(self, input: str):
        self.content = Constant(input)

    @render_method
    def render(self) -> str:
        return self.content.render()


class ConflictsSlide(Slide):
    def animate(self):
        pass
