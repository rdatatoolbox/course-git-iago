"""Modifiers concerned with individual slides and their very concrete content.
"""

from modifiers import MakePlaceHolder, TextModifier


class Step(TextModifier):
    """Special abstract parent of slide bodies,
    whose individual slides inherit of.
    Useful a meta-list of children so we can dynamically pick the right type
    by matching document information with their type name.
    """

    pass


# Common commands.
CommandModifier, Command = MakePlaceHolder(
    "Command",
    r"\Command[<anchor>]{<loc>}{<text>}",
    anchor="center",
)
HighlightSquareModifier, HighlightSquare = MakePlaceHolder(
    "HighlightSquare",
    r"\HighlightSquare[<padding>]{<lower>}{<upper>}",
    padding="5",
)
HighlightShadeModifier, HighlightShade = MakePlaceHolder(
    "HighlightShade",
    r"\HighlightShade[<padding>]{<node>}",
    padding="5",
)
IntensiveCoordinatesModifier, IntensiveCoordinates = MakePlaceHolder(
    "IntensiveCoordinates",
    r"\IntensiveCoordinates{<node>}{<name>}{<x>,<y>}",
)
