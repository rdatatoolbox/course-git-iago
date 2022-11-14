"""Take advantage that we know the raw lexical structure
of every slide we need to animate, so we can parse it easily.
"""

import re
from typing import Callable, Self, cast


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
    """Common modifier.
    Feed with a regex containing groups and their list of names.
    The names become modifiable members,
    and the input is rendered with the corresponding group modified.
    Provide a few TextModifier types if some members are non-leaves.
    """

    def __init__(
        self,
        input: str,
        pattern: str,
        groups: str,
        **kwargs: type,
    ):
        if not (m := re.compile(pattern, re.DOTALL).match(input)):
            raise ValueError(
                f"The given pattern:\n  {pattern}\ndoes not match input:\n {input}"
            )
        self._match = m  # Members with no trailing '_' are group values.
        for i, name in enumerate(groups.strip().split()):
            group = cast(str, m.group(i + 1))
            if name in kwargs:
                group = cast(TextModifier, kwargs[name](group))
            self.__dict__[name] = group

    def render(self) -> str:
        result = ""
        m = self._match
        original = m.string
        c = 0
        i = 0
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            s, e = m.span(i + 1)
            # Copy all non-grouped parts of original string.
            result += original[c:s]
            # But skip groups and replace with new value instead.
            result += v.render() if isinstance(v, TextModifier) else str(v)
            c = e
            i += 1
        return result + original[c:]

    # Reassure pyright with artificial __[gs]etattr__ methods.
    def __getattr__(self, name: str) -> str | TextModifier:
        return self.__dict__[name]

    def __setattr__(self, name: str, value: str | re.Match):
        self.__dict__[name] = value


class ListOf(TextModifier):
    """Construct a TextModifier type that is just a trivial list of another one,
    with head and tail considered constant if requested.
    """

    separator: str
    type: Callable
    with_head: bool
    with_tail: bool

    def __init__(self, input: str):
        chunks = input.split(self.separator)
        self.head = Constant(chunks.pop(0)) if self.with_head else None
        self.tail = Constant(chunks.pop() if chunks else "") if self.with_tail else None
        self.list = [cast(TextModifier, self.type(c)) for c in chunks]

    def render(self) -> str:
        return self.separator.join(
            m.render() for m in [self.head] + self.list + [self.tail] if m
        )

    def append(self, *args, **kwargs) -> TextModifier:
        new = getattr(self.type, "new")(*args, **kwargs)
        self.list.append(new)
        return new

    def clear(self) -> Self:
        self.list.clear()
        return self


def MakeListOf(tp: Callable, sep=",\n", head=False, tail=False) -> type:
    class NewListOf(ListOf):
        separator = sep
        type = tp
        with_head = head
        with_tail = tail

    NewListOf.__name__ = "ListOf" + tp.__name__
    return NewListOf
