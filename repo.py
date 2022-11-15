"""Craft and edit a simple repo.
"""

from modifiers import ListOf, MakeListOf, Regex


class Repo(Regex):
    """One chain of commits, arranged from the bottom up.
    Be careful that the first one needs be anchored,
    and the others are located wrt to it.
    Also, use labels to point to commits like `HEAD` and `main`.
    """

    commits: ListOf
    labels: ListOf

    def __init__(self, input: str):
        super().__init__(
            input,
            r"\s*\\Repo\[(.*?)\]{(.*?)}{\n(.*?)}%(.*)",
            "anchor pos commits labels",
            commits=Commits,
            labels=Labels,
        )

    def clear(self):
        """Remove all commits and labels."""
        self.commits.clear()
        self.labels.clear()


class Commit(Regex):
    """Plain hash number and commit message."""

    _short = True

    def __init__(self, input: str):
        super().__init__(
            input,
            r"\s*(.*?)/{(.*?)}",
            "hash message",
        )

    @staticmethod
    def new(*args) -> "Commit":
        model = r"    {}/{{{}}}".format(*args)
        return Commit(model)


def Label(_, input: str):
    """Either HEAD or a branch label."""
    try:
        return Head(input)
    except ValueError:
        return Branch(input)


# Cheat to make Label.new automatically happen based on number of arguments.
Label.new = lambda *args: Head.new(*args) if len(args) == 3 else Branch.new(*args)


class Head(Regex):

    _short = True

    def __init__(self, input: str):
        super().__init__(
            input,
            r"\s*\\Head{(.*?)}{(.*?)}{(.*?)}",
            "hash offset local",
        )

    @staticmethod
    def new(*args) -> "Head":
        model = (r"  \Head" + "{{{}}}" * 3).format(*args)
        return Head(model)


class Branch(Regex):

    _short = True

    def __init__(self, input: str):
        super().__init__(
            input,
            r"\s*\\Branch\[(.*?)\]{(.*?)}{(.*?)}{(.*?)}{(.*?)}",
            "color hash offset local name",
        )

    @staticmethod
    def new(*args) -> "Branch":
        model = (r"  \Branch[{}]" + "{{{}}}" * 4).format(*args)
        return Branch(model)


Commits = MakeListOf(Commit, sep=",\n", tail=True)
Labels = MakeListOf(Label, sep="\n", head=True)
