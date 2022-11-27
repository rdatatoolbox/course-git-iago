"""Slide to explain diffs, conflict and markers.
"""

from textwrap import dedent
from typing import cast

from diffs import DiffedFile
from document import Slide
from modifiers import (
    AnonymousPlaceHolder,
    Constant,
    ConstantBuilder,
    Regex,
    TextModifier,
    render_method,
)
from steps import Step


class Arrow(TextModifier):
    """Raw modifier with no parse ability."""

    origin: str
    destination: str
    start_slide: str
    end_slide: str
    start_offset: str
    end_offset: str
    opacity: str
    bend: str

    def __init__(self, *args):
        kwargs = {  # Predefined arguments order.
            k: str(v)
            for k, v in zip("origin start_slide destination end_slide".split(), args)
        }
        pooled = "".join(kwargs.values())
        offset = "3" if "north" in pooled else "-3"
        options = dict(
            start_offset=offset,
            end_offset=offset,
            bend="30",
            opacity="0.5",
            side="left" if "left" in pooled else "right",
        )
        options.update(**kwargs)
        self.__dict__ = options

    @render_method
    def render(self) -> str:
        return dedent(
            "\n"
            + r"""
                \coordinate (s) at ($({origin} west)!{start_slide}!({origin} east)$);
                \coordinate[above={start_offset} of s] (s);
                \coordinate (e) at ($({destination} west)!{end_slide}!({destination} east)$);
                \coordinate[above={end_offset} of e] (e);
                \begin{{scope}}[transparency group, opacity={opacity}]
                  \draw[-Stealth, line width=10, Brown2] (s) to[bend {side}={bend}] (e);
                \end{{scope}}
                """.format(
                **self.__dict__
            )
        )


class ConflictsStep(Step):
    def parse_body(self):
        input = self.body
        chunks = input.split("\n\n")
        it = iter(chunks)
        self.coordinates = Constant(next(it))
        zone = (r"\\path.*\[fill=(.*?),.*?opacity=(.*?)\].*", "color opacity")
        self.noconflict_zone = Regex(next(it), *zone)
        self.lexical_zone = Regex(next(it), *zone)
        self.semantic_zone = Regex(next(it), *zone)
        self.paragraphs = {
            name: [Constant(l) for l in next(it).split("\n")]
            for name in ("none", "lexical", "semantic", "both")
        }
        self.diff_left = DiffedFile(next(it))
        self.diff_right = DiffedFile(next(it))
        self.diff_merge = DiffedFile(next(it))
        self.message = Regex(
            next(it),
            r"\\AutomaticCoordinates{.*?}{(.*?)}.*?" r"\\node.*{(.*?)};(.*)",
            "location text underline",
            underline=ConstantBuilder,
        )
        try:
            while some := next(it):
                assert not some
        except StopIteration:
            pass

    def render_body(self) -> str:
        return "\n\n".join(
            m.render()
            for m in [
                self.coordinates,
                self.noconflict_zone,
                self.lexical_zone,
                self.semantic_zone,
            ]
            + [
                Constant("\n".join(l.render() for l in lines))
                for lines in self.paragraphs.values()
            ]
            + [
                self.diff_left,
                self.diff_right,
                self.diff_merge,
                self.message,
            ]
        )


class ConflictsSlide(Slide):
    def animate(self):

        step = cast(ConflictsStep, self.pop_step())
        STEP = lambda: self.add_step(step)

        zones = (
            noconflict := step.noconflict_zone.off(),
            lexical := step.lexical_zone.off(),
            semantic := step.semantic_zone.off(),
        )
        pars = {k: [l.off() for l in lines] for k, lines in step.paragraphs.items()}
        diffs = (
            left := step.diff_left.clear().off(),
            right := step.diff_right.clear().off(),
            merged := step.diff_merge.clear().off(),
        )
        message = step.message.off()
        underline = cast(Constant, message.underline)
        from_left = step.add_epilog(Arrow("left.north", 0.5, "merge.north", 0)).off()
        from_right = step.add_epilog(Arrow("right.north", 0.5, "merge.north", 1)).off()
        to_left = step.add_epilog(Arrow("merge.south", 0.3, "left.south", 0.7)).off()
        to_right = step.add_epilog(Arrow("merge.south", 0.7, "right.south", 0.3)).off()

        def set_filename(name):
            for diff, v, c in (
                (left, "MY", "Blue5"),
                (right, "THEIR", "Brown4"),
                (merged, "MERGED", "Purple3"),
            ):
                diff.set_filename(
                    rf"{name} \textcolor{{{c}}}{{<{v}\_VERSION>}}",
                    diff.mod,
                )

        def zone_off(name: str = "noconflict"):
            (noconflict, lexical, semantic)  # Just for capture.
            zone = cast(Constant, eval(name))
            zone.off()
            if name == "noconflict":
                keys = [*pars.keys()]
            else:
                keys = [name, "both"]
            [line.off() for key in keys for line in pars[key]]

        def par_on(name: str | None = None):
            if name is None:
                [l.on() for lines in pars.values() for l in lines]
            else:
                [l.on() for l in pars[name]]

        def par_off(name: str | None = None):
            if name is None:
                [l.off() for lines in pars.values() for l in lines]
            else:
                [l.off() for l in pars[name]]

        def noconflict_on():
            noconflict.on()
            [l.on() for l in pars["none"]]

        def reset():
            """Propagate changes from merged to left and right, and reset all to zero."""
            merged.set_mod("0", 1, -1)
            merged.mod = "0"
            left.populate(merged)
            right.populate(merged)

        def from_on():
            from_right.on()
            from_left.on()

        def from_off():
            from_right.off()
            from_left.off()

        def to_on():
            to_right.on()
            to_left.on()

        def to_off():
            to_right.off()
            to_left.off()

        STEP()

        readme = """
            Collect [...] the best pizzas recipes.

            Where to find the pizzas in the project:

            - __Diavola__: `./diavola.md`
            - __Margerita__: `./margerita.md`
            - __Regina__: `./regina.md`
            """

        left.on().insert_lines(readme).mod = "0"
        right.on().insert_lines(readme).mod = "0"
        set_filename("README.md")
        STEP()

        # Identical files.
        message.on().text = "no change"
        STEP()

        message.off()
        noconflict_on()
        STEP()

        merged.on().insert_lines(readme).mod = "0"
        from_on()
        STEP()

        from_off()
        to_on()
        STEP()

        to_off()
        merged.off()
        zone_off()
        STEP()

        # On-sided change.
        siciliana = r"- __Siciliana__: `./siciliana.md`"
        right.insert_lines(siciliana, "+", 8).mod = "m"
        message.on().text = "change on one side"
        STEP()

        message.off()
        noconflict_on()
        STEP()

        merged.on().populate(right)
        from_on()
        STEP()

        merged.mark_lines(8)
        merged.reset()
        from_off()
        STEP()

        to_on()
        reset()
        STEP()

        to_off()
        merged.unmark_all().off()
        reset()
        zone_off()
        STEP()

        # Two-sided changes.
        calzone = r"- __Calzone__: `./calzone.md`"
        marinara = r"- __Marinara__: `./marinara.md`"
        left.insert_lines(calzone, "+", 5).mod = "m"
        right.insert_lines(marinara, "+", 7).mod = "m"
        message.on().text = "change on both sides"
        STEP()

        message.on().text = "disjoint lines"
        STEP()

        message.off()
        noconflict_on()
        STEP()

        merged.on().populate(left).insert_lines(marinara, "+", 8)
        from_on()
        STEP()

        merged.mark_lines([5, 8])
        merged.reset()
        from_off()
        STEP()

        reset()
        to_on()
        STEP()

        to_off()
        merged.unmark_all().off()
        reset()
        zone_off()
        STEP()

        # Two-sided inline.
        message.on().text = "inline changes?"
        underline.off()
        STEP()

        _, _, hi_eat, _ = left.replace_in_line(3, "(find the)", "eat all")
        left.mod = "m"
        STEP()

        _, _, hi_margherita, _ = right.on().replace_in_line(7, r"g()erita", "h")
        right.mod = "m"
        STEP()

        message.on().text = "disjoint lines"
        underline.on()
        STEP()

        message.off()
        noconflict_on()
        merged.on().populate(right)
        merged.replace_in_line(3, "(find the)", "eat all")
        from_on()
        STEP()

        merged.erase_lines(8, 9)
        merged.erase_lines(3, 4)
        merged.insert_lines(hi_eat, 3)
        merged.insert_lines(hi_margherita, 7)
        from_off()
        merged.reset()
        STEP()

        reset()
        to_on()
        STEP()

        merged.off()
        left.off()
        right.off()
        to_off()
        STEP()

        # Lexical conflict!
        lexical.on()
        pars["lexical"][0].on()
        par_off("none")
        STEP()

        custom = """
            # The SURPRISE pizza

            A wonderful suprise of the dev team
            dedicated just to your fancy
            thirst for fortune and originality <3

            __Base:__ sour cream
            __Topping:__
            - Garlic
            - Basil
            - eggplant
            - Hazelnuts
            """
        set_filename("suprise.md")
        merged.clear().insert_lines(custom)
        reset()
        left.on()
        pic = step.add_epilog(
            AnonymousPlaceHolder(
                r"\AutomaticCoordinates{c}{<location>}" + "\n"
                r"\node[anchor=<anchor>] (pizza) at (c)"
                r" {\Pic<which>{<width>}{<height>}};",
                "new",
                which="Surprise",
                location=".85, 0",
                anchor="east",
                width="!",
                height="20cm",
            )
        )
        lexical.off()
        zone_off()
        STEP()

        pic.off()
        noconflict.on()
        lexical.on()
        pars["lexical"][0].on()
        right.on()
        STEP()

        left.replace_in_line(3, "A( wonderful)", "n amazing")
        left.mod = "m"
        STEP()

        _, _, hi_eggplant, _ = right.replace_in_line(11, "(e)gg", "E")
        right.replace_in_line(3, "su()prise", "r")
        right.mod = "m"
        STEP()

        pic.on().which = "Heart"
        pic.location = "below=15 of right.south"
        pic.anchor = "north"
        pic.height = "8cm"
        STEP()

        pic.off()
        STEP()

        message.on().text = "! same lines !"
        STEP()

        message.off()
        c = lexical.color
        lexical.color = "Red1"
        pars["lexical"][1].on()
        pars["lexical"][2].on()
        STEP()

        zone_off("noconflict")
        zone_off("lexical")
        lexical.color = c
        merged.on().populate(right).mod = "c"
        merged.erase_lines(3, 4)
        conflict = """
            <<<<<<< HEAD
            An amazing suprise of the dev team
            =======
            A wonderful surprise of the dev team
            >>>>>>> github/main
            """
        merged.insert_lines(conflict, "c", 3)
        from_on()
        STEP()

        merged.erase_lines(15, 16)
        hi_eggplant.mod = "0"
        merged.insert_lines(hi_eggplant, 15)
        from_off()
        STEP()

        pic.on().which = "OMG"
        pic.height = "8cm"
        pic.location = ".0, -1"
        pic.anchor = "south"
        STEP()

        pic.off()
        STEP()

        message.on().text = "Human, you are in charge now."
        message.location = "0, -.6"
        STEP()

        pic.on().which = "Think"
        pic.anchor = "north"
        pic.height = "10cm"
        pic.location = "below = 10 of left.south"
        think_safe = pic.copy()
        STEP()

        pic.which = "Relief"
        merged.erase_lines(3, 7)
        merged.insert_lines(r"A\dhi{n amazing} su\dhi{r}prise of the dev team", "c", 3)
        relief_safe = pic.copy()
        STEP()

        pic.off()
        reset()
        to_on()
        STEP()

        merged.off()
        to_off()
        message.off()
        merged.unmark_lines([3, 11])
        reset()
        STEP()

        # Semantic conflict!
        noconflict_on()
        semantic.on()
        pars["semantic"][0].on()
        par_off("none")
        STEP()

        safe = left.copy()
        left.replace_in_line(1, "E()", " vegetarian")
        left.mod = "m"
        right.insert_lines("- Bacon", "+", -1)
        right.mod = "m"
        STEP()

        message.on().text = "disjoint lines"
        message.location = ".0, .52"
        STEP()

        lexical.on()
        pars["lexical"][0].on()
        STEP()

        par_off("lexical")
        pars["semantic"][1].on()
        pars["semantic"][2].on()
        message.off()
        c = semantic.color
        semantic.color = "Red1"
        STEP()

        pic.on().which = "Hazard"
        pic.anchor = "center"
        pic.location = "0, .17"
        pic.height = "7cm"
        lexical.off()
        STEP()

        from_on()
        merged.on().clear().populate(right)
        _, _, hi_veg, _ = merged.replace_in_line(1, "E()", " vegetarian")
        pic.off()
        STEP()

        merged.erase_lines(1, 2)
        merged.insert_lines(hi_veg, 1)
        merged.mark_lines(12)
        merged.reset()
        from_off()
        STEP()

        reset()
        to_on()
        STEP()

        to_off()
        merged.off()
        pic.on().which = "Skull"
        pic.location = ".0, .28"
        skull_safe = pic.copy()
        par_off("semantic")
        semantic.off().color = c
        lexical.off()
        zone_off()
        STEP()

        # Reverting conflict.
        merged.populate(safe)
        reset()
        pic.off()
        message.on().text = "So keep this in mind:"
        message.location = "0, 0"
        STEP()

        # Summarize categories.
        noconflict_on()
        message.off()
        STEP()

        lexical.on()
        par_on("lexical")
        STEP()

        semantic.on()
        par_on("semantic")
        STEP()

        par_on("both")
        STEP()

        message.on().text = "QUIZZ!"
        # QUIZZ: NONCONFLICT example
        message.location = "$(lexical)!.5!(semantic)$"
        underline.off()
        par_off()
        STEP()

        message.off()
        left.replace_in_line(5, "(thirst)", "craave")
        right[11].mod = "-"
        left.mod = right.mod = "m"
        STEP()

        par_on("none")
        STEP()

        _, _, hi_crave, _ = merged.on().replace_in_line(5, "(thirst)", "craave")
        merged[12].mod = "-"
        from_on()
        STEP()

        merged.erase_lines(5, 6)
        merged.insert_lines(hi_crave, 5)
        merged.pop(11)
        from_off()
        # TODO: make this an actual feature of Diffs.
        phantom_line = merged.internal_epilog = Constant(
            r"\coordinate[below=2.5 of line-10.base west] (c);" + "\n"
            r"\draw[Blue1, line width=1] (c) -- (c -| line-10.east);"
        )
        STEP()

        reset()
        left.internal_epilog = phantom_line
        right.internal_epilog = phantom_line
        to_on()
        STEP()

        to_off()
        merged.off()
        STEP()

        # QUIZZ: LEXICAL CONFLICT example
        phantom_line.off()
        par_off()
        merged.populate(safe)
        reset()
        left.replace_in_line(7, "(s)our", "S")
        right.replace_in_line(7, "(sour c)ream", "Sour C")
        left.mod = right.mod = "m"
        STEP()

        par_on("lexical")
        STEP()

        from_on()
        conflict = r"""
            <<<<<<< HEAD
            __Base:__ Sour cream
            =======
            __Base:__ Sour Cream
            >>>>>>> github/main
            """
        merged.pop(7)
        merged.on().insert_lines(conflict, "c", 7).mod = "c"
        par_off("lexical")
        STEP()

        from_off()
        pic.__dict__.update(think_safe.__dict__)
        STEP()

        merged.erase_lines(7, 11)
        merged.insert_lines("__Base:__ Sour Cream", 7).mark_lines(7)
        pic.__dict__.update(relief_safe.__dict__)
        STEP()

        to_on()
        reset()
        pic.off()
        STEP()

        merged.off()
        to_off()
        [pars["lexical"][i].on() for i in (0, 1)]
        STEP()

        # QUIZZ: SEMANTIC CONFLICT example
        par_off()
        merged.populate(safe)
        reset()
        right.replace_in_line(3, "team()", ",")
        right.insert_lines("a typical tomato-based pizza, but", "+", 5)
        right.mod = "m"
        STEP()

        par_on("semantic")
        STEP()

        from_on()
        merged.on().populate(right)
        STEP()

        from_off()
        merged.pop(3)
        merged.mark_lines(3, 4).set_mod("0", 3, 4)
        STEP()

        to_on()
        reset()
        STEP()

        merged.off()
        to_off()
        pic.__dict__.update(skull_safe.__dict__)
        pars["semantic"][2].off()
        STEP()

        # QUIZZ: BOTH CONFLICTS example
        pic.off()
        par_off()
        merged.populate(safe)
        reset()
        left.replace_in_line(9, "(G)arlic", "Sweet g")
        right.replace_in_line(9, "Garlic()", ", pepper or anything spicy")
        left.mod = right.mod = "m"
        STEP()

        par_on("both")
        pars["lexical"][0].on()
        pars["semantic"][0].on()
        STEP()

        from_on()
        conflict = r"""
            <<<<<<< HEAD
            - Sweet garlic
            =======
            - Garlic, pepper or anything spicy
            >>>>>>> github/main
            """
        merged.on().pop(9)
        merged.insert_lines(conflict, "c", 9).mod = "c"
        par_off()
        STEP()

        from_off()
        pic.height = "10cm"
        (think := step.add_epilog(pic.copy()).on()).which = "Think"
        think.anchor = "south west"
        think.location = "-.87, -.9"
        STEP()

        # Essentially relating to how humans work together :')
        (shy := step.add_epilog(pic.copy()).on()).which = "DuckShy"
        shy.anchor = "north west"
        shy.location = "-.75, .71"
        (flames := step.add_epilog(pic.copy()).on()).which = "DuckFlames"
        flames.anchor = "north east"
        flames.location = ".99, .91"
        STEP()

        merged.off()
        par_on()
        (relief := step.add_epilog(pic.copy()).on()).which = "Relief"
        relief.anchor = "south east"
        relief.location = ".95, -.9"
        STEP()
