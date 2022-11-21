"""Craft and edit a simple repo.
"""

from document import FindPlaceHolder, HighlightSquare
from modifiers import (
    AnonymousPlaceHolder,
    Builder,
    ListBuilder,
    MakePlaceHolder,
    PlaceHolder,
    TextModifier,
    render_method,
)


class Repo(TextModifier):
    """One chain of commits, arranged from the bottom up.
    Be careful that the first one needs be anchored,
    and the others are located wrt to it.
    Also, use labels to point to commits like `HEAD` and `main`.
    """

    def __init__(self, input: str, offset: str):
        """Assume it's parsed *empty*."""
        intro, rest = input.split("{}", 1)
        self.intro = AnonymousPlaceHolder(
            r"\Repo[<anchor>][<name>][<type>][<opacity>]{<loc>}", "parse", intro
        )
        assert rest == "{}"
        reponame = self.intro.name
        self.commits = Commits.new()
        self.head = Head.new("", "", "")
        self.branch: PlaceHolder | None = Branch.new(
            f"$({reponame}) + ({offset})$", "0:0", "noarrow", "main"
        )
        self.branches = [self.branch]
        self.current: PlaceHolder = HighlightCommit(reponame).off()
        self.hi_square = HighlightSquare.new("HEAD.south west", "main.north east").off()
        self.checkout_branch("main")

    @render_method
    def render(self) -> str:
        return (
            self.intro.render()
            + "{\n"
            + self.commits.render()
            + "\n"
            + "}{\n"
            + "\n".join(
                m.render()
                for m in self.branches + [self.head, self.current, self.hi_square]
            )
            + "}\n"
        )

    @property
    def latest_hash(self) -> str | None:
        return self.commits.list[-1].hash if self.commits.list else None

    def add_commit(
        self,
        *args,
        **kwargs,
    ) -> PlaceHolder:  # Commit
        if len(args) == 1 and not kwargs:
            commit = args[0]
            commit = self.commits.append(commit)
        else:
            commit = self.commits.append(*args, **kwargs)
        hash = commit.hash
        self.current.ref = hash
        if branch := self.branch:
            old_ref = branch.ref
            self.move_branch(branch.name, hash)
            # Associated remote branches stay here.
            for b in self.branches:
                if b.name.endswith("/" + branch.name) and branch.name in b.ref:
                    self.move_branch(b.name, old_ref)
                    break
        if len(self.commits) == 1:
            # First commit! Highlight it.
            self.current.on()
            # Update square.
            self.hi_square.lower = r"$(repo.south west) + (3*\eps, 3*\eps)$"
            self.hi_square.upper = "repo.east |- main.north"
        return commit

    def move_branch(self, name: str, hash: str) -> "Repo":
        branch = self[name]
        branch.anchor = "base west"
        branch.ref = hash
        if hash == self.latest_hash:
            branch.offset = "55:13"
            branch.start = "-.5, 0"
        else:
            branch.offset = "31:13"
            branch.start = "-.9, 0"
        return self

    def __getitem__(self, name: str) -> PlaceHolder:
        """Retrieve any kind of content within the repo."""
        res = None
        # Special names
        if name == "HEAD":
            res = self.head
        elif name == "current":
            res = self.current
        else:
            for b in self.branches:
                if b.name == name:
                    res = b
                    break
        if not res:
            raise KeyError(f"Could not find reference {repr(name)} in repo.")
        return res

    def checkout_branch(self, name: str) -> "Repo":
        head = self.head
        branch = self[name]
        head.ref = f"{branch.name}.base west"
        head.anchor = "base east"
        head.offset = "11"
        head.start = "2"
        self.current.ref = branch.ref
        return self

    def checkout_detached(
        self,
        hash: str,
    ) -> "Repo":
        self.branch = None
        head = self.head
        head.ref = hash
        head.offset = "156:20"
        head.anchor = "center"
        head.start = ".5,0"
        self.current.ref = hash
        return self

    def add_remote_branch(
        self,
        remote_branch: str,
        ref: str | None = None,
    ) -> PlaceHolder:  # RemoteBranch
        remote, branch = remote_branch.split("/")
        if ref is None:
            ref = branch
            rbranch = RemoteBranch.new(f"", "", "", f"{remote}/{branch}")
            self.branches.append(rbranch)
            self.remote_to_branch(remote_branch)
            return rbranch
        raise NotImplementedError(
            f"No remote branch for non-defaut ref yet {repr(ref)}, "
            "Need to distinguish branch case from raw hash case."
        )

    def remote_to_branch(self, name: str) -> "Repo":
        """Update remote to branch location."""
        remote = self[name]
        branch = self[name.split("/")[1]]
        remote.ref = branch.name + ".base east"
        remote.anchor = "base west"
        remote.offset = "2"
        remote.start = "noarrow"
        return self

    def highlight(self, on: bool, name: str | None = None) -> "Repo":
        """Highlight the given label, or the whole repo if none is given."""
        if not name:
            self.hi_square.on(on)
            return self
        label = self[name]
        label.style = "label" + ("-hi" if on else "")
        if on:
            label.on()
        return self

    def populate(self, repo: "Repo") -> "Repo":
        """Import all commits from another repo."""
        for commit in repo.commits:
            self.add_commit(commit.copy())
        return self


CommitModifier, Commit = MakePlaceHolder("Commit", r"<type>/<hash>/{<message>}")

HeadModifier, Head = FindPlaceHolder("Head")
BranchModifier, Branch = FindPlaceHolder("Branch")
RemoteBranchModifier, RemoteBranch = FindPlaceHolder("RemoteBranch")
HighlightCommitModifier, HighlightCommit = FindPlaceHolder("HighlightCommit")


LocalRepoLabelModifier, LocalRepoLabel = FindPlaceHolder("LocalRepoLabel")
RemoteRepoLabelModifier, RemoteRepoLabel = FindPlaceHolder("RemoteRepoLabel")
RemoteArrowModifier, RemoteArrow = FindPlaceHolder("RemoteArrow")
CommandModifier, Command = FindPlaceHolder("Command")


class _LabelBuilder(Builder[PlaceHolder]):
    """Artificial singleton to automatically parse into correct label
    and create the correct label based on the given arguments.
    """

    def parse(self, input: str) -> PlaceHolder:
        for PHB in (Head, Branch, RemoteBranch, LocalRepoLabel):
            try:
                return PHB.parse(input)
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
