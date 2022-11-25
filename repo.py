"""Craft and edit a simple repo.
"""

from typing import Callable, Iterable, List, cast

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


class Repo(TextModifier):
    """One chain of commits, arranged from the bottom up.
    Be careful that the first one needs be anchored,
    and the others are located wrt to it.
    Also, use labels to point to commits like `HEAD`, `main` and `remote/main`.
    The logical state of the repo here is only concern with topology:
        - the commits chain
        - for every commit, the list of pointers on it.
        - the status of HEAD (attached to a branch, detached)
        - ..
    Only when rendering is the above information translated into exact positionning etc.
    """

    def __init__(self, input: str):
        """Assume it's parsed *empty*."""
        intro, rest = input.split("{}", 1)
        self.intro = AnonymousPlaceHolder(
            r"\Repo[<anchor>][<name>][<type>][<opacity>]{<location>}", "parse", intro
        )
        assert rest == "{}"

        # A list of pointers to every commit (same size). All owned except for HEAD.
        self.commits = Commits.new()
        self.labels: List[List[PlaceHolder]] = []  # No HEAD in there if attached.

        # The currently checked out commit (none in initial state).
        self.head = Head.new("", "", "")
        self.current: PlaceHolder = HighlightCommit("").off()

        # The currently checked out branch, if any. There must be one if repo is empty.
        self.branch: PlaceHolder | None = Branch.new(f"", "0:0", "noarrow", "main")

        self.checkout_branch(self.branch.name)

        # Highlighting.
        self.hi_square = HighlightSquare.new("", "").off()  # Filled on render.

        # Lower to see just the commits.
        self._render_labels = True

    @property
    def name(self):
        return self.intro.name

    @property
    def detached(self):
        return self.branch is None

    @render_method
    def render(self) -> str:

        self.pre_render()

        return (
            self.intro.render()
            + "{\n"
            + self.commits.render()
            + "}{\n"
            + "\n".join(
                m.render()
                for m in (
                    (
                        ([self.branch] if self.branch else [])
                        + [l for labs in self.labels for l in labs]
                        + ([] if self.detached else [self.head])
                        + [self.current]
                    )
                    if self._render_labels
                    else ([self.current])
                )
            )
            + "}\n"
            + self.hi_square.render()
        )

    def pre_render(self):
        """Fill out every positionning etc. information based on the state,
        before rendering.
        """

        head = self.head

        def head_left_to_branch(branch: PlaceHolder, last_commit=False):
            head.ref = branch.name + ".base west"
            head.anchor = "base east"
            head.offset = "11" if last_commit else "21"
            head.start = "2"

        # Work out all rendering details based on current repo status.
        if not self.commits.list:
            # Empty repo, cheat with the only branch here.
            assert (branch := self.branch)
            branch.ref = self.name
            head_left_to_branch(self.branch)

        # Now, position every label correctly
        # depending on how many they are on every commit
        # and whether it's the last commit.
        for (i_commit, (commit, labels)) in enumerate(zip(self.commits, self.labels)):
            last_commit = i_commit == len(self.labels) - 1
            if not labels:
                continue

            # The currently checked out branch should be positionned first.
            if self.branch in labels:
                labels.remove(self.branch)
                labels.insert(0, self.branch)

            def point_to_commit(branch: PlaceHolder):
                branch.ref = commit.hash
                branch.anchor = "south west"
                # Fine-tweak against 'main' here
                # because adjustement actually depends on content.
                if last_commit:
                    branch.offset = "45:13"
                    branch.start = "-.5, 0" if branch.name == "main" else "-.8, 0"
                else:
                    branch.offset = "20:13" if branch.name == "main" else "17:11"
                    branch.start = "-.9, 0"

            previous_name = "<uninit>"
            for (i_label, label) in enumerate(labels):
                if self.branch is (branch := label):
                    # The checked out branch is positioned first.
                    assert i_label == 0
                    point_to_commit(branch)
                    previous_name = branch.name
                    # Locate HEAD next to it.
                    if last_commit:
                        head_left_to_branch(branch, last_commit)
                    else:
                        # (to the right of it otherwise it would cross the line)
                        head.ref = branch.name + ".base east"
                        head.anchor = "base west"
                        head.offset = "5"
                        head.start = "2"
                        previous_name = "HEAD"
                elif self.head is label:
                    # This is a detached HEAD state, leave it to the left with an arrow.
                    head.offset = "140:20" if last_commit else "156:20"
                    head.anchor = "center"
                    head.start = ".5,0"
                    previous_name = "HEAD"
                else:
                    # Other, regular branches just stack right.
                    branch = label
                    if previous_name == "<uninit>":
                        point_to_commit(branch)
                    else:
                        branch.ref = previous_name + ".base east"
                        branch.anchor = "base west"
                        branch.offset = "2"
                        branch.start = "noarrow"
                    previous_name = branch.name

        # Highlight.
        if not self.commits.list:
            self.hi_square.lower = "HEAD.south west"
            self.hi_square.upper = "main.north east"
            self.hi_square.padding = "2"
            self.current.off()
        else:
            self.hi_square.lower = rf"$({self.name}.south west) + (3*\eps, 3*\eps)$"
            self.hi_square.upper = rf"{self.name}.east |- main.north"
            self.hi_square.padding = "5"
            self.current.on().hash = self.branch.ref if self.branch else self.head.ref

    def move_branch(self, name: str, hash: str) -> "Repo":
        # Essentially relocating it to the correct list of labels.
        branch = self[name]
        for (commit, labels) in zip(self.commits, self.labels):
            if commit.hash == hash:
                if branch not in labels:
                    labels.append(branch)
            else:
                try:
                    labels.remove(branch)
                except ValueError:
                    pass
        return self

    def checkout_detached(self, hash: str) -> "Repo":
        self.branch = None
        # Add HEAD to the labels.
        head = self.head
        for (commit, labels) in zip(self.commits, self.labels):
            if commit.hash == hash:
                if not head in labels:
                    labels.append(head)
            else:
                try:
                    labels.remove(head)
                except ValueError:
                    pass
        head.ref = hash
        return self

    def checkout_branch(self, name: str) -> "Repo":
        # Boils down to just removing "HEAD" from the labels.
        branch = self[name]
        self.branch = branch
        for labels in self.labels:
            try:
                labels.remove(self.head)
            except ValueError:
                pass
        self.head.ref = branch.name
        return self

    def remote_to_branch(self, name: str) -> "Repo":
        # Relocate remote.
        remote = self[name]
        branch = self[name.split("/")[1]]
        for labels in self.labels:
            if branch in labels:
                if not remote in labels:
                    labels.append(remote)
            else:
                try:
                    labels.remove(remote)
                except ValueError:
                    pass
        return self

    def add_commit(
        self,
        *args,
        # Specify the branch is supposed to move along, defaulting to self.branch.
        # Use empty string to not move any branch.
        _branch: str | None = None,
        **kwargs,
    ) -> PlaceHolder:  # Commit
        if len(args) == 1 and not kwargs:
            commit = args[0]
            commit = self.commits.append(commit)
        else:
            commit = self.commits.append(*args, **kwargs)
        hash = commit.hash

        self.labels.append([])

        # Interpret the branch to be moved along.
        if _branch is None:
            branch = self.branch
        elif not _branch:
            branch = None
        else:
            branch = self[_branch]

        if branch:
            self.move_branch(branch.name, hash)

        return commit

    def __getitem__(self, name: str) -> PlaceHolder:
        """Retrieve any kind of content within the repo."""
        # Special names
        if name == "HEAD":
            return self.head
        if self.branch and name == self.branch.name:
            return self.branch
        if name == "current":
            return self.current
        for (commit, labels) in zip(self.commits, self.labels):
            if commit.hash == name:
                return commit
            for label in labels:
                if type(label) is HeadModifier:
                    continue
                if label.name == name:
                    return label
        raise KeyError(f"Could not find reference {repr(name)} in repo.")

    def add_remote_branch(
        self,
        remote_branch: str,
        hash: str | None = None,  # Default to current such local branch.
    ) -> PlaceHolder:  # RemoteBranch
        assert not any(
            l.name == remote_branch for labels in self.labels for l in labels
        )
        rbranch = RemoteBranch.new(f"", "", "", remote_branch)
        if hash is None:
            # Find local branch with this name and append there.
            _, branchname = remote_branch.split("/")
            local = self[branchname]
            for labels in self.labels:
                if local in labels:
                    labels.append(rbranch)
                    return rbranch
        # Otherwise find commit with this ref:
        for (commit, labels) in zip(self.commits, self.labels):
            if commit.hash == hash:
                labels.append(rbranch)
                return rbranch
        raise ValueError(
            f"Could not find hash commit {repr(hash)} "
            f"to set remote branch {repr(remote_branch)} on."
        )

    def highlight(self, name: str | bool = True, on=True) -> "Repo":
        """Highlight the given label, or the whole repo if none is given.
        repo.highlight()
        repo.highlight(False)
        repo.highlight('main', True)
        """
        if type(name) is bool:
            on = name
            self.hi_square.on(on)
            return self
        label = self[name]
        label.style = "hi" if on else ""
        return self

    def hi_on(self, label: str | None = None) -> "Repo":
        """Simplified version so we can just:
        repo.hi_on()
        repo.hi_on('main')
        """
        if label is None:
            return self.highlight(True)
        return self.highlight(label, True)

    def hi_off(self, label: str | None = None) -> "Repo":
        """Simplified version so we can just:
        repo.hi_off()
        repo.hi_off('main')
        """
        if label is None:
            return self.highlight(False)
        return self.highlight(label, False)

    def populate(self, repo: "Repo") -> "Repo":
        """Import all commits from another repo."""
        for commit in repo.commits:
            self.add_commit(commit.copy())
        return self

    def clear(self) -> "Repo":
        assert self.branch  # Otherwise there would be no branch left.
        self.commits.clear()
        self.labels.clear()
        return self

    def iter(self, start=1, end: int | None = None) -> Iterable[PlaceHolder]:  # Commit
        """Iterate on requested commits, counting from 1, end included, -1 is end."""
        start -= 1
        if end is None:
            end = start + 1
        elif end == -1:
            end = len(self.commits)
        yield from self.commits.list[start:end]

    @staticmethod
    def fade_commit(c: PlaceHolder) -> PlaceHolder:  # Commit
        kws = set(c.type.split())
        kws.add("fade")
        c.type = " ".join(kws)
        return c

    @staticmethod
    def unfade_commit(c: PlaceHolder) -> PlaceHolder:  # Commit
        c.type = " ".join(set(c.type.split()) - {"fade"})
        return c

    def alter_commits(
        self,
        alter: Callable,
        start: int | List[str] = 1,
        end: int | None = None,
    ):
        """Apply one function to a range of commits, given by either integers or hashes."""
        if type(start) is int:
            for commit in self.iter(start, end):
                alter(commit)
        else:
            hashes = cast(List[str], start)
            for commit in self.commits:
                if commit.hash in hashes:
                    alter(commit)

    def fade_commits(self, *args, **kwargs):
        self.alter_commits(self.fade_commit, *args, **kwargs)

    def unfade_commits(self, *args, **kwargs):
        self.alter_commits(self.unfade_commit, *args, **kwargs)

    def trim(self, n: int) -> "Repo":
        """Remove the first n commits (and associated branches) to make room."""
        for _ in range(n):
            self.commits.list.pop(0)
            labels = self.labels.pop(0)
            assert (
                self.branch not in labels
            )  # Don't trim the branch checked out though.
        return self
