"""Modifiers concerned with individual slides and their very concrete content.
"""

from modifiers import TextModifier, render_method


class Step(TextModifier):
    """Special abstract parent of slide bodies,
    whose individual slides inherit of.
    Useful a meta-list of children so we can dynamically pick the right type
    by matching document information with their type name.
    """

    def __init__(self, input: str):
        prefix = r"\Step{"
        assert input.startswith(prefix)
        input = input.removeprefix(prefix).strip()
        self.progress, input = input.split("}{", 1)
        input = input.strip()
        assert input.endswith("}")
        self.body = input.removesuffix("}")
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
            r"\Step{"
            + self.progress
            + "}{\n"
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
