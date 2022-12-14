"""Modifiers concerned with individual slides and their very concrete content.
"""

from modifiers import TextModifier, AnonymousPlaceHolder


class Step(TextModifier):
    """Special abstract parent of slide bodies,
    whose individual slides inherit of.
    Useful a meta-list of children so we can dynamically pick the right type
    by matching document information with their type name.
    """

    def __init__(self, input: str):
        intro, body = input.split("{\n", 1)
        self.intro = AnonymousPlaceHolder(r"\Step[<type>]{<progress>}", "parse", intro)
        body = body.strip()
        assert body.endswith("}")
        self.body = body.removesuffix("}")
        # Responsibility to the kids to parse further.
        self.parse_body()

    def parse_body(self):
        raise NotImplementedError(
            f"Cannot parse body for Step type {type(self).__name__}."
        )

    def render(self) -> str:
        """Rendering a step is not a regular render,
        because only _prolog and _epilog special member makes sense
        and it should stay within the command.
        """
        return (
            self.intro.render()
            + "{\n"
            + (
                "\n".join(m.render() for m in self._prolog)
                if hasattr(self, "_prolog")
                else ""
            )
            + self.render_body()
            + "\n"
            + (
                "\n".join(m.render() for m in self._epilog)
                if hasattr(self, "_epilog")
                else ""
            )
            + "}"
        )

    def render_body(self):
        raise NotImplementedError(
            f"Cannot render body for Step type {type(self).__name__}."
        )
