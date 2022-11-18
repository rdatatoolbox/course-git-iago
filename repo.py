"""Craft and edit a simple repo.
"""

from modifiers import Builder, ListBuilder, ListOf, MakePlaceHolder, PlaceHolder, Regex
from document import FindPlaceHolder


class Repo(Regex):
    """One chain of commits, arranged from the bottom up.
    Be careful that the first one needs be anchored,
    and the others are located wrt to it.
    Also, use labels to point to commits like `HEAD` and `main`.
    """

    commits: ListOf[PlaceHolder]
    labels: ListOf[PlaceHolder]

    def __init__(self, input: str):
        super().__init__(
            input.strip(),
            r"\\Repo\[(.*?)\]{(.*?)}{\n(.*?)}%\n(.*)",
            "anchor pos commits labels",
            commits=Commits,
            labels=Labels,
        )

    def clear(self):
        """Remove all commits and labels."""
        self.commits.clear()
        self.labels.clear()


CommitModifier, Commit = MakePlaceHolder("Commit", r"<type>/<hash>/{<message>}")

HeadModifier, Head = FindPlaceHolder("Head")
BranchModifier, Branch = FindPlaceHolder("Branch")
LocalRepoLabelModifier, LocalRepoLabel = FindPlaceHolder("LocalRepoLabel")
RemoteRepoLabelModifier, RemoteRepoLabel = FindPlaceHolder("RemoteRepoLabel")
RemoteArrowModifier, RemoteArrow = FindPlaceHolder("RemoteArrow")
CommandModifier, Command = FindPlaceHolder("Command")


def hi_label(label: PlaceHolder, on: bool):
    label.style = "label" + ("-hi" if on else "")
    if on:
        label.on()


class _LabelBuilder(Builder[PlaceHolder]):
    """Artificial singleton to automatically parse into correct label
    and create the correct label based on the given arguments.
    """

    def parse(self, input: str) -> PlaceHolder:
        try:
            return Head.parse(input)
        except ValueError:
            pass
        try:
            return Branch.parse(input)
        except ValueError:
            pass
        try:
            return LocalRepoLabel.parse(input)
        except ValueError:
            pass
        return RemoteRepoLabel.parse(input)

    def new(self, *args) -> PlaceHolder:
        """Assuming 'new' is undesired for RepoLabels,
        decide based on number of arguments.
        """
        if len(args) == 3:
            return Head.new(*args)
        else:
            return Branch.new(*args)


LabelBuilder = _LabelBuilder()

Commits = ListBuilder(Commit, ",\n", tail=True)
Labels = ListBuilder(LabelBuilder, "\n")
