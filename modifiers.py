"""Take advantage that we know the raw lexical structure
of every slide we need to animate, so we can parse it easily.
"""

from copy import deepcopy
import re
from typing import Callable, Self, cast, List


class TextModifier(object):
    """The text modifier feeds from a structured text
    whose lexical structure is known.
    It parses it into a python object
    exposing various edition methods.
    Then it may be rendered into a modified version of the text.
    Some modifiers are not actually created from strings and are only rendered,
    in this case they provide a `new()` static method.
    """

    _rendered = True  # Lower on instances so they render to nothing.
    _epilog: List["TextModifier"]  # Set to append after rendering.

    def __init__(self, _: str):
        raise NotImplementedError(f"Cannot parse input text for {type(self).__name__}.")

    @classmethod
    def new(cls, *_, **__) -> Self:
        raise NotImplementedError(f"Cannot create new {type(cls).__name__}.")

    def render(self) -> str:
        raise NotImplementedError(f"Cannot render text for {type(self).__name__}.")

    def copy(self) -> Self:
        return deepcopy(self)

    def on(self) -> Self:
        """Make rendered."""
        self._rendered = True
        return self

    def off(self) -> Self:
        """Make unrendered."""
        self._rendered = False
        return self

    def add_epilog(self, m: "TextModifier") -> "TextModifier":
        try:
            self._epilog.append(m)
        except AttributeError:
            self._epilog = [m]
        return m

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


def render_function(f: Callable) -> Callable:
    """Decorate render functions so they take `_rendered` and `_epilog` into account."""

    def render(self, *args, **kwargs) -> str:
        if not self._rendered:
            return ""
        result = f(self, *args, **kwargs)
        try:
            result += "".join(m.render() for m in self._epilog)
        except AttributeError:
            pass
        return result

    return render


class Constant(TextModifier):
    """Trivial leaf modifier that offers no modification API. Just wraps an immutable string."""

    _short = True

    def __init__(self, input: str):
        self.raw = input

    @render_function
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
                f"The given pattern:\n  {pattern}\ndoes not match input:\n {input}\n"
                f"in Regex type {type(self).__name__}."
            )
        self._match = m  # Members with no trailing '_' are group values.
        for i, name in enumerate(groups.strip().split()):
            group = cast(str, m.group(i + 1))
            if name in kwargs:
                group = cast(TextModifier, kwargs[name](group))
            self.__dict__[name] = group

    @staticmethod
    def new(pattern: str, **kwargs) -> "Regex":
        """Construct pattern given placeholders in <> tags, all empty by default
        unless otherwise specified in kwargs."""
        chunks = pattern.strip().split("<")
        input = chunks.pop(0)
        regex = re.escape(input)
        placeholders = []
        type_kwargs = {}
        for c in chunks:
            ph, literal = c.split(">", 1)
            regex += r"(.*?)"
            placeholders.append(ph)
            if ph in kwargs:
                if type(v := kwargs[ph]) is type:
                    type_kwargs[ph] = v
                elif type(v) is str:
                    input += v
                else:
                    input += v.render()
            input += literal
            regex += re.escape(literal)
        return Regex(input, regex, " ".join(placeholders), **type_kwargs)

    @render_function
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
        if name.startswith("__") and name.endswith("__"):  # keep python internals safe
            return self.__getattribute__(name)
        try:
            return self.__dict__[name]
        except KeyError as e:
            raise AttributeError(str(e))

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

    @render_function
    def render(self) -> str:
        return self.separator.join(
            r for m in [self.head] + self.list + [self.tail] if m and (r := m.render())
        )

    def append(self, *args, **kwargs) -> TextModifier:
        new = getattr(self.type, "new")(*args, **kwargs)
        self.list.append(new)
        return new

    def clear(self) -> Self:
        self.list.clear()
        return self


def MakeListOf(tp: Callable, sep: str, head=False, tail=False) -> type:
    class NewListOf(ListOf):
        separator = sep
        type = tp
        with_head = head
        with_tail = tail

    NewListOf.__name__ = "ListOf" + tp.__name__
    return NewListOf
