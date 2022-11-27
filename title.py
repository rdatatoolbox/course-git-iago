"""Special single-step slide just used for transitions before regular slides.
"""

from document import Slide
from modifiers import Constant
from steps import Step


class TitleStep(Step):
    def parse_body(self):
        input = self.body
        self.content = Constant(input)

    def render_body(self) -> str:
        return self.content.render()


class TitleSlide(Slide):
    # No animation required.
    pass
