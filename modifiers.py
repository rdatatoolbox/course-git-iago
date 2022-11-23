"""Take advantage that we know the raw lexical structure
of every slide we need to animate, so we can parse it easily.
"""

from copy import deepcopy
import re
from typing import Callable, Dict, Generic, List, Self, Set, Tuple, TypeVar, cast


TM = TypeVar("TM", bound="TextModifier")


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
    # Set to append befor/after rendering.
    _prolog: List["TextModifier"]
    _prolog_sep = "\n"
    _epilog: List["TextModifier"]
    _epilog_sep = "\n"
    # Set onto a specific layer.
    _layer: str | None = None

    # This additional, UNPARSED parameter
    # wraps rendering within a tikz transparency group if inferior to 1.
    # Otherwise silent.
    _opacity = 1.0  # Only used in rendering, retro-parsing *may* fail if <1.

    def render(self) -> str:
        raise NotImplementedError(f"Cannot render text for {type(self).__name__}.")

    def copy(self) -> Self:
        return deepcopy(self)

    def on(self, on=True) -> Self:
        """Make rendered."""
        self._rendered = on
        return self

    def off(self, on=False) -> Self:
        """Make unrendered."""
        self._rendered = on
        return self

    def add_prolog(self, m: TM) -> TM:
        try:
            self._prolog.append(m)
        except AttributeError:
            self._prolog = [m]
        return m

    def add_epilog(self, m: TM) -> TM:
        try:
            self._epilog.append(m)
        except AttributeError:
            self._epilog = [m]
        return m

    def remove_from_prolog(self, m: TM) -> TM:
        try:
            self._prolog.remove(m)
        except AttributeError:
            self._prolog = []
        return m

    def remove_from_epilog(self, m: TM) -> TM:
        try:
            self._epilog.remove(m)
        except AttributeError:
            self._epilog = []
        return m

    def bump_epilog(self, m: TM) -> TM:
        """Make this element rendered last, so it's layed over the others."""
        return self.add_epilog(self.remove_from_epilog(m))

    _tab = " "
    _short = False  # Override in children for shorter display.

    def display(self, level=0) -> str:
        """Recursive walk among modifiers members for displaying,
        sort modifiers last.
        """
        level += 1
        tab = TextModifier._tab
        base_indent = level * tab
        name = type(self).__name__
        result = name + "(" + ("" if self._short else "\n")
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


def render_method(render: Callable) -> Callable:
    """Decorate render functions so they take
        _rendered
        _prolog
        _epilog
        _opacity
        _layer
    into account.
    """

    def decorated_render(self, *args, **kwargs) -> str:
        result = ""
        if not self._rendered:
            return result

        if hasattr(self, "_prolog"):
            result += self._prolog_sep.join(m.render() for m in self._prolog)

        if l := self._layer:
            result += r"\begin{pgfonlayer}{" + l + "}"

        if (o := self._opacity) < 1:
            result += r"\begin{scope}[transparency group, opacity=" + str(o) + "]\n"

        result += render(self, *args, **kwargs)

        if o < 1:
            result += r"\end{scope}" + "\n"

        if self._layer:
            result += r"\end{pgfonlayer}"

        if hasattr(self, "_epilog"):
            result += self._epilog_sep.join(m.render() for m in self._epilog)

        return result

    return decorated_render


class Builder(Generic[TM]):
    """Define interface for objects supposed to create particular TextModifiers."""

    built_type = TextModifier

    def parse(self, _: str) -> TM:
        """Construct from parsed input string."""
        raise NotImplementedError(
            f"Cannot parse input to construct {TM.__name__} value."
        )

    def new(self, *_, **__) -> TM:
        """Construct from desired content of the string."""
        raise NotImplementedError(f"Cannot construct {TM.__name__} from data.")


class Constant(TextModifier):
    """Trivial leaf modifier that offers no modification API. Just wraps an immutable string."""

    _short = True

    def __init__(self, input: str):
        self.raw = input

    @render_method
    def render(self) -> str:
        return self.raw

    def display(self, _: int) -> str:
        return f"Constant({repr(self.raw)})"


class _ConstantBuilder(Builder[Constant]):
    """Degenerated singleton producing constant text modifiers."""

    built_type = Constant

    def parse(self, input: str) -> Constant:
        return Constant(input)

    def new(self, input: str) -> Constant:
        return Constant(input)

    def __repr__(self):
        return f"{type(self).__name__}"


ConstantBuilder = _ConstantBuilder()


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
        pattern: str | re.Pattern,
        groups: str,
        **kwargs: Builder,
    ):
        if type(pattern) is str:
            pattern = re.compile(pattern, re.DOTALL)
        pattern = cast(re.Pattern, pattern)
        if not (m := pattern.match(input)):
            raise ValueError(
                f"The given pattern:\n{pattern.pattern}\n"
                f"does not match input:\n{input}\n"
                f"in Regex type {type(self).__name__}."
            )
        self._match = m  # Members with no trailing '_' are group values.
        for i, name in enumerate(groups.strip().split()):
            group = cast(str, m.group(i + 1))
            if name in kwargs:
                group = cast(TextModifier, kwargs[name].parse(group))
            self.__dict__[name] = group

    @render_method
    def render(self) -> str:
        result = ""
        m = self._match
        original = m.string
        c = 0
        i = 0
        try:
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
        except:
            raise ValueError(
                f"{type(self).__name__}: "
                f"could not render the following match:\n  {m.string}\n"
                + "with the following groups:\n  {}".format(
                    "\n  ".join(
                        f"{k}: {type(v).__name__}"
                        for k, v in self.__dict__.items()
                        if not k.startswith("_")
                    )
                )
            )
        return result + original[c:]

    # Reassure pyright with artificial __[gs]etattr__ methods.
    def __getattr__(self, name: str) -> str | TextModifier:
        if name.startswith("__") and name.endswith("__"):  # keep python internals safe
            return self.__getattribute__(name)
        try:
            return self.__dict__[name]
        except KeyError as e:
            raise AttributeError(str(e))

    def __setattr__(self, name: str, value: str | TextModifier):
        self.__dict__[name] = value


class PlaceHolder(Regex):
    """Trivial Regex object with simple placeholders,
    with simplified API and constructible from simple patterns with special <>.
    """

    # Members can only be plain strings.
    def __getattr__(self, *args, **kwargs) -> str:
        return cast(str, super().__getattr__(*args, **kwargs))

    def __setattr__(self, name: str, value: str):
        super().__setattr__(name, value)


PH = TypeVar("PH", bound=PlaceHolder)


class PlaceHolderBuilder(Builder[PH]):
    """Constructs trivial Regexes objects with simple placeholders
    given a simple literal patterns with <> special marks.
    """

    def __init__(
        self,
        _built_type: type,
        _pattern: str,
        # List members set as positional arguments (otherwise named),
        # default to all members positional except options.
        _positionals: None | str = None,
        # Give named members default values and/or types.
        **options: str | type | Tuple[str, type],
    ):
        self.built_type = _built_type
        self.options = options
        self.pattern = _pattern
        if _positionals is None:
            auto_pos = True
            pos: Set[str] = set()
        else:
            auto_pos = False
            pos = set(_positionals.strip().split())

        # Construct 'regex' for Regex.__init__() (fed into re.compile)
        # and 'model' for Regex.new() (fed into str.format()).
        py_escape = lambda s: s.replace("{", "{{").replace("}", "}}")
        chunks = _pattern.strip().split("<")
        head = chunks.pop(0)
        regex = re.escape(head)
        model = cast(str, py_escape(head))
        placeholders: List[str] = []
        types: Dict[str, type] = {}
        re.compile("a\nb").match("a\nb")
        for c in chunks:
            ph, literal = c.split(">", 1)
            regex += r"(.*?)"
            model += (
                "{}"
                if (ph in pos) or (auto_pos and (ph not in options))
                else f"{{{ph}}}"
            )
            if ph in options:
                v = options[ph]
                if type(v) is tuple:
                    v, t = v
                    types[ph] = t
                    options[ph] = v
                elif type(v) is type:
                    options[ph] = v
            placeholders.append(ph)
            regex += re.escape(literal)
            model += cast(str, py_escape(literal))
        self.placeholders = placeholders
        self.regex = regex + r"$"
        self.model = model
        self.types = types

    def parse(self, input: str) -> PH:
        groups = " ".join(self.placeholders)
        return self.built_type(
            input.strip(),
            self.regex,
            groups,
            **self.types,
        )

    def new(self, *args, **kwargs) -> PH:
        kw = self.options.copy()
        kw.update(kwargs)
        return self.parse(self.model.format(*args, **kw))

    def __call__(self, *args, **kwargs) -> PH:
        """Direct calls mean 'new'."""
        return self.new(*args, **kwargs)

    def __repr__(self):
        return f"{type(self).__name__}[{self.built_type.__name__}]"


def MakePlaceHolder(
    _name,
    *args,
    **kwargs,
) -> Tuple[type, PlaceHolderBuilder[PlaceHolder]]:
    """Construct a pair of PlaceHolder subtypes and associated builder.
    To clarify uses of builder, the shortest name goes to it,
    and the other is suffixed with -Modifier.
    """
    SubPH = type(_name + "Modifier", (PlaceHolder,), {})
    SubPHBuilder = PlaceHolderBuilder[SubPH](SubPH, *args, **kwargs)
    return SubPH, SubPHBuilder


def AnonymousPlaceHolder(pattern, _do: str, *args, **kwargs) -> PlaceHolder:
    """Useful for one-liners,
    PlaceHolder objects that will only be parsed/created in one place.
    """
    _, SubPHBuilder = MakePlaceHolder("Anonymous", pattern, _positionals="")
    if _do == "new":
        return SubPHBuilder.new(**kwargs)
    if _do == "parse":
        assert len(args) == 1 and not kwargs
        input = args[0]
        return SubPHBuilder.parse(input)
    raise ValueError(
        f"Not sure what to `_do` with the anonymous placeholder ({repr(_do)})"
    )


class ListOf(Generic[TM], TextModifier):
    """Construct a TextModifier type that is just a trivial list of another one,
    with head and tail considered constant if requested.
    """

    def __init__(
        self,
        list: List[TM],
        builder: Builder[TM],
        separator: str,
        head: Constant | None = None,
        tail: Constant | None = None,
    ):
        self.builder = builder
        self.separator = separator
        self.head = head
        self.list = list
        self.tail = tail

    def append(self, *args, **kwargs) -> TM:
        # Append direct children if needed..
        if len(args) == 1 and not kwargs and isinstance(tm := args[0], TextModifier):
            assert isinstance(tm, self.builder.built_type)
            tm = cast(TM, tm)
            self.list.append(tm)
            return tm
        # .. or create them.
        new = self.builder.new(*args, **kwargs)
        self.list.append(new)
        return new

    def clear(self) -> Self:
        self.list.clear()
        return self

    def __iter__(self):
        for m in self.list:
            yield m

    def __getitem__(self, i):
        return self.list[i]

    @render_method
    def render(self) -> str:
        return self.separator.join(
            m.render() for m in [self.head] + self.list + [self.tail] if m
        )

    def __len__(self) -> int:
        return len(self.list)


class ListBuilder(Builder[ListOf[TM]]):

    built_type = ListOf  # ListOf[TM]

    def __init__(
        self,
        builder: Builder[TM],
        separator: str,
        head=False,
        tail=False,
    ):
        self.builder = builder
        self.separator = separator
        self.with_head = head
        self.with_tail = tail

    def parse(self, input: str) -> ListOf[TM]:
        chunks = input.split(self.separator)
        head = Constant(chunks.pop(0)) if self.with_head else None
        tail = Constant(chunks.pop() if chunks else "") if self.with_tail else None
        list = [self.builder.parse(c) for c in chunks]
        return ListOf[TM](list, self.builder, self.separator, head, tail)

    def new(
        self,
        list: List[TM] | None = None,
        head: Constant | None = None,
        tail: Constant | None = None,
    ) -> ListOf[TM]:
        if list is None:
            list = []
        return ListOf[TM](list, self.builder, self.separator, head, tail)

    def __repr__(self):
        return f"{type(self).__name__}[{self.builder}]({{}})".format(
            ", ".join(f"{k}: {v}" for k, v in self.__dict__)
        )
