"""Take advantage that we know the raw lexical structure
of every slide we need to animate, so we can parse it easily.
"""

from typing import cast, Self
import re


class TextModifier(object):
    """The text modifier feeds from a structured text
    whose lexical structure is known.
    It parses it into a python object
    exposing various edition methods.
    Then it may be rendered into a modified version of the text.
    Copying it should be always possible by a simple render/parse loop.
    """

    def __init__(self, _: str):
        raise NotImplementedError(f"Cannot parse input text for {type(self).__name__}")

    def render(self) -> str:
        raise NotImplementedError(f"Cannot render text for {type(self).__name__}")

    def copy(self) -> "TextModifier":
        return type(self)(self.render())

    _tab = " "
    _short = False  # Override in children for shorter display.

    def display(self, level=0) -> str:
        """Recursive walk among modifiers members for displaying,
        sort modifiers last.
        """
        level += 1
        tab = TextModifier._tab
        base_indent = level * tab
        result = type(self).__name__ + "(" + ("" if self._short else "\n")
        modifiers = []
        others = []
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            mod = isinstance(v, TextModifier)
            if mod:
                rv = v.display(level + 1)
            elif isinstance(v, list) or isinstance(v, tuple):
                parens = "()" if isinstance(v, tuple) else "[]"
                rv = parens[0] + "\n"
                level += 1
                for i in v:
                    if isinstance(i, TextModifier):
                        ri = i.display(level)
                    else:
                        ri = repr(i)
                    rv += level * tab + ri + ",\n"
                level -= 1
                rv += base_indent + parens[1]
            else:
                rv = repr(v)
            (modifiers if mod else others).append(
                ("" if self._short else base_indent)
                + f"{k}: {rv}"
                + ("" if self._short else ",")
            )
        result += (", " if self._short else "\n").join(others + modifiers)
        base_indent = (level - 1) * TextModifier._tab
        result += ")" if self._short else f"\n{base_indent})"
        return result

    def __repr__(self):
        return self.display(0)


class Constant(TextModifier):
    """Trivial leaf modifier that offers no modification API. Just wraps an immutable string."""

    _short = True

    def __init__(self, input: str):
        self.raw = input

    def render(self) -> str:
        return self.raw

    def display(self, _: int) -> str:
        return f"Constant({repr(self.raw)})"


class Regex(TextModifier):
    """Common leaf modifier.
    Feed with a regex containing groups and their list of names.
    The names become modifiable members,
    and the input is rendered with the corresponding group modified.
    """

    _short = True

    def __init__(self, input: str, pattern: str, groups: str):
        if not (m := re.compile(pattern).match(input)):
            raise ValueError(
                f"The given pattern:\n  {pattern}\ndoes not match input:\n {input}"
            )
        self._match = m  # Members with no trailing '_' are group values.
        for i, name in enumerate(groups.strip().split()):
            self.__dict__[name] = m.group(i + 1)

    def render(self) -> str:
        result = ""
        m = self._match
        original = m.string
        c = 0
        for i, v in enumerate(
            v for k, v in self.__dict__.items() if not k.startswith("_")
        ):
            s, e = m.span(i + 1)
            # Copy all non-grouped parts of original string.
            result += original[c:s]
            # But skip groups and replace with new value instead.
            result += cast(str, v)
            c = e
        return result + original[c:]

    # Reassure pyright with artificial __[gs]etattr__ methods.
    def __getattr__(self, name: str) -> str:
        return self.__dict__[name]

    def __setattr__(self, name: str, value: str | re.Match):
        self.__dict__[name] = value


class Document(TextModifier):
    """Root-level modifier, splitting the whole file into slides to animate,
    but keeping track of preamble and what's between slides for later rendering.
    Actually a sequence of <non-slide> and <slide> chunks.
    """

    _startmark = "% SLIDE"
    _endmark = "% ENDSLIDE"

    def __init__(self, input: str):
        self.non_slides = non_slides = []
        self.slides = slides = []
        chunks = input.split(self._startmark)
        non_slides.append(Constant(chunks.pop(0)))
        for c in chunks:
            s, ns = c.rsplit(self._endmark, 1)
            slides.append(Slide(s))
            non_slides.append(Constant(ns))

    def render(self) -> str:
        ns = iter(self.non_slides)
        s = iter(self.slides)
        result = next(ns).render()
        for (slide, non_slide) in zip(s, ns):
            result += self._startmark + slide.render() + self._endmark
            result += non_slide.render()
        return result


class Content(TextModifier):
    """Special abstract parent of slide bodies,
    whose individual slides inherit of.
    """

    pass


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
        self.steps = [cast(Content, SlideType(body.rstrip()))]

    def render(self) -> str:
        return " {}\n{}{} ".format(
            self.name,
            self.header.raw,
            "\n".join(f"\\Step{{{s.render()}}}" for s in self.steps),
        )


class Introduction(Content):
    """Empty slide for now."""

    def __init__(self, input: str):
        assert not input.strip()

    def render(self) -> str:
        return "\n\n"


class Pizzas(Content):
    """The slide with repo / project folder / file content."""

    def __init__(self, input: str):
        chunks = input.split("\n\n")
        it = iter(chunks)
        next(it)  # Ignore leading_whitespace
        self.filetree = FileTree(next(it))
        self.diffconfig = Constant(next(it))
        self.readme = next(it)
        self.margherita = next(it)
        self.regina = next(it)
        self.repo = next(it)
        try:
            next(it)
            assert False
        except StopIteration:
            pass

    def render(self) -> str:
        return (
            "\n\n"
            + "\n\n".join(
                m.render() if isinstance(m, TextModifier) else m
                for m in (
                    self.filetree,
                    self.diffconfig,
                    self.readme,
                    self.margherita,
                    self.regina,
                    self.repo,
                )
            )
            + "\n\n"
        )


class FileLine(Regex):
    """Parse special line displaying one file in the tree folder."""

    def __init__(self, input: str):
        super().__init__(
            input,
            r"\s*\\.*?mod=(.).*?(|, last)\]{(.*?)}{(.*?)}{(.*?)}",
            "mod last pos name filename",
        )


class FileTree(TextModifier):
    """Within the file tree. Take advantage that we know it exactly.
    Be careful that when hiding one file line,
    the chain of relative positionning needs to be reconnected.
    """

    def __init__(self, input: str):
        # Refer to them as list to easily reconnect the chain.
        self._list = [FileLine(l) for l in input.split("\n")]
        lines = iter(self._list)
        # And also as individual files for random access.
        self.root = next(lines)
        self.git = next(lines)
        self.readme = next(lines)
        self.margherita = next(lines)
        self.regina = next(lines)

    def render(self) -> str:
        return "\n".join(
            m.render()
            for m in (
                self.root,
                self.git,
                self.readme,
                self.margherita,
                self.regina,
            )
        )
