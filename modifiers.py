"""Take advantage that we know the raw lexical structure
of every slide we need to animate, so we can parse it easily.
"""

import re
from typing import Self, cast


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

    def copy(self) -> Self:
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
        i = 0
        for k, v in self.__dict__.items():
            if k.startswith('_'):
                continue
            s, e = m.span(i + 1)
            # Copy all non-grouped parts of original string.
            result += original[c:s]
            # But skip groups and replace with new value instead.
            result += cast(str, v)
            c = e
            i += 1
        return result + original[c:]

    # Reassure pyright with artificial __[gs]etattr__ methods.
    def __getattr__(self, name: str) -> str:
        return self.__dict__[name]

    def __setattr__(self, name: str, value: str | re.Match):
        self.__dict__[name] = value
