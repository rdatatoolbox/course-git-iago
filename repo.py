"""Craft and edit a simple repo.
"""

from typing import Callable, Dict, Iterable, List, Set, cast

from document import FindPlaceHolder, HighlightSquare
from modifiers import (AnonymousPlaceHolder, Builder, ListBuilder,
                       MakePlaceHolder, PlaceHolder, TextModifier,
                       render_method)

CommitModifier, Commit = MakePlaceHolder("Commit", r"<type>/<hash>/{<message>}")

LabelModifier, Label = FindPlaceHolder("Label")
HighlightCommitModifier, HighlightCommit = FindPlaceHolder("HighlightCommit")

LocalRepoLabelModifier, LocalRepoLabel = FindPlaceHolder("LocalRepoLabel")
RemoteRepoLabelModifier, RemoteRepoLabel = FindPlaceHolder("RemoteRepoLabel")
RemoteArrowModifier, RemoteArrow = FindPlaceHolder("RemoteArrow")
CommandModifier, Command = FindPlaceHolder("Command")


def new_label(name: str) -> PlaceHolder:
    """Automatically configure label style depending on the name,
    and leave positionning information artifically blank for later filling.
    """
    text = name
    args = ("", "0:0", "noarrow", text)
    kwargs = {"name": name}
    if name == "HEAD":
        kwargs["style"] = "=Purple4"
    elif "/" in name:
        # Interpret as remote branch.
        kwargs["style"] = "=Brown2"
    else:
        kwargs["style"] = "=Blue4"
    return Label.new(*args, **kwargs)


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
            r"\Repo[<name>][<alignment>][<opacity>]{<location>}",
            "parse",
            intro,
        )
        assert rest == "{}"

        # A list of pointers to every commit (same size). All owned except for HEAD.
        self.commits = Commits.new()
        self.labels: List[List[PlaceHolder]] = []  # No HEAD in there if attached.

        # The currently checked out commit (none in initial state).
        self.head = new_label("HEAD")
        self.current: PlaceHolder = HighlightCommit("").off()

        # The currently checked out branch, if any. There must be one if repo is empty.
        self.branch: PlaceHolder | None = new_label("main")

        self.checkout_branch(self.branch.name)

        # Highlighting.
        self.hi_square = HighlightSquare.new("", "").off()  # Filled on render.

        # Lower to see just the commits.
        self._render_labels = True

        # Labels in this set are displayed to the left of the chain.
        # HEAD is special-cased here, in particular when pointing at
        # the branch to the right on topmost commit.
        # ASSUMPTION: the branch checked out is not there.
        self.left_labels: Set[str] = set()

        # Locked labels appear with a little icon to their right.
        self.locks: Dict[str, PlaceHolder] = {}  # {branchname: LabelModifier}

    @property
    def name(self):
        return self.intro.name

    @property
    def detached(self):
        return self.branch is None

    @render_method
    def render(self) -> str:

        epilog = self.pre_render()

        return (
            self.intro.render()
            + "{\n"
            + self.commits.render()
            + "}{\n"
            + "\n".join(m.render() for m in epilog)
            + "}\n"
            + self.hi_square.render()
        )

    def pre_render(self) -> List[PlaceHolder]:
        """Fill out every positionning etc. information based on the state,
        before rendering. Constructs the epilog in correct order.
        """

        head = self.head

        # One epilog for each items chain right and left of the commit.
        left_chains = []  # with HEAD for the last commit and left-marked labels.
        right_chains = []  # with HEAD for detached states and non-last commits.

        def set_head_left_of_branch(branch: PlaceHolder, last_commit=False):
            head.ref = branch.name + ".base west"
            head.anchor = "base east"
            head.offset = "11" if last_commit else "21"
            head.start = "2"

        if not self.commits.list:
            # Empty repo, cheat with the only branch here.
            assert (branch := self.branch)
            branch.ref = self.name
            set_head_left_of_branch(self.branch)
            right_chains = [self.branch, self.head]

        # Now, position every label correctly
        # depending on how many they are on every commit
        # and whether it's the last commit.
        # The idea is to fill 'left' and 'right'
        # with the correctly parametrized modifiers,
        # and then only they will be chained to each other.
        two_chains = False  # Raise when there are two open parallel commit chains.
        second_chain = (
            False  # Raise when this leads to the second arrow being locally drawn.
        )
        for (i_commit, (commit, labels)) in enumerate(zip(self.commits, self.labels)):
            last_commit = i_commit == len(self.labels) - 1
            if "Y" in commit.type.split():
                two_chains = True
            if "A" in commit.type.split():
                two_chains = False
                second_chain = False
            if two_chains:
                # Go check further whether there is actually a second commit.
                second_chain = False
                for further_commit in self.commits[i_commit + 1 :]:
                    tp = further_commit.type.split()
                    if any(t in tp for t in ("H", "A")):
                        second_chain = True
                        break
            if not labels:
                continue

            left = []
            right = []

            # Correctly fill up the right/left chains.
            # Work on a copy of all labels and progressively drain it
            # until items are all correctly ordered within the two chains.
            remaining = labels.copy()
            for label in labels:
                # Insert into chains on a per-branch basis
                # to correctly group remotes/lock/head together.
                if label.name != "HEAD" and "/" not in (branch := label).name:
                    if branch.name in self.left_labels:
                        # Insert at the end of the chain unless it's the branch checked out.
                        left.append(branch)
                        remaining.remove(branch)
                        if branch.name in self.locks:
                            left.insert(len(left) - 1, self.locks[branch.name])
                        if self.branch is branch:
                            left.append(self.head)
                        for remote in labels:
                            if remote.name.endswith("/" + branch.name):
                                left.append(remote)
                                remaining.remove(remote)
                    else:
                        # Insert at the end of the chain unless it's the branch checked out.
                        i = 0 if branch is self.branch else len(right)
                        right.insert(i, branch)
                        i += 1
                        remaining.remove(branch)
                        if branch.name in self.locks:
                            right.insert(i, self.locks[branch.name])
                            i += 1
                        if branch is self.branch:
                            if last_commit:
                                # HEAD goes to the left with special positionning
                                left.append(self.head)
                            else:
                                right.insert(i, self.head)
                                i += 1
                        for remote in labels:
                            if remote.name.endswith("/" + branch.name):
                                right.insert(i, remote)
                                i += 1
                                remaining.remove(remote)
            # Remaining items go last into to either chains.
            for label in remaining:
                if label.name in self.left_labels or label.name == "HEAD":
                    left.append(label)
                else:
                    right.append(label)

            # Now precise the exact, literal positionning
            # of every items in the chains.
            for i, item in enumerate(left):  # (iterate from east to west)
                # The first one is positionned wrt current commit.
                if i == 0:
                    if (head := item) is self.head and not self.detached:
                        head.anchor = "base east"
                        head.ref = right[0].name + ".base west"
                        head.offset = "10"
                        head.start = "2"
                    else:
                        item.anchor = "base east"
                        item.offset = "137:10"
                        n = len(item.name)  # to calculate ideal arrow start.
                        item.start = f"{3.7*n}, 4"
                        item.ref = commit.hash
                    continue
                # Subsequent ones are positionned wrt previous item.
                previous = left[i - 1]
                item.ref = previous.name + ".base west"
                item.anchor = "base east"
                # Special-case head, because it's different whether attached.
                if self.head is (head := item):
                    if i == 0:
                        pass  # Already handled.
                    else:
                        if self.detached:  #! NOT UPDATED AFTER COPY-PASTE.
                            head.offset = "156:20"  #!
                            head.anchor = "center"  #!
                            head.start = ".5,0"  #!
                        else:
                            head.offset = "5"
                            head.start = "2"
                else:
                    item.offset = "0" if "-lock" in item.name else "2"
                    item.start = "noarrow"

            for i, item in enumerate(right):
                # The first is positioned wrt current commit.
                if i == 0:
                    branch = item
                    if self.head in right and not self.detached and last_commit:
                        set_head_left_of_branch(item)
                    branch.ref = commit.hash
                    branch.anchor = "base west"
                    if last_commit:
                        branch.offset = "45:13"
                        branch.start = "4.5, 2"
                    else:
                        if second_chain and "I" in commit.type.split():
                            # Shift right a little so it does not cover the arrow.
                            branch.offset = "15.5, 6.5"
                            branch.start = "2, 2"
                        else:
                            branch.offset = "36:11"
                            branch.start = "2, 3.3"
                    continue
                previous = right[i - 1]
                item.ref = previous.name + ".base east"
                item.anchor = "base west"
                # Special-case head, because it's different whether attached.
                if self.head is (head := item):
                    if self.detached:
                        head.offset = "140:20" if last_commit else "156:20"
                        head.anchor = "center"
                        head.start = ".5,0"
                    else:
                        head.offset = "5"
                        head.start = "2"
                else:
                    item.offset = "0" if "-lock" in item.name else "2"
                    item.start = "noarrow"

            left_chains.extend(left)
            right_chains.extend(right)

        # Highlight.
        if not self.commits.list:
            self.current.off()
            self.hi_square.lower = "HEAD.south west"
            self.hi_square.upper = "main.north east"
            self.hi_square.padding = "2"
        else:
            self.current.on().hash = self.branch.ref if self.branch else self.head.ref
            # Square highlight needs identifier of the first commit,
            # and east coordinate of the longest message.
            # TODO: 'main' is not always the northest label north coordinate.
            longest = self.commits[0]
            first = longest.hash
            for commit in self.commits:
                if len(longest.message) < len(commit.message):
                    longest = commit
            longest = longest.hash
            self.hi_square.lower = rf"{first}-hash.south west"
            self.hi_square.upper = rf"{longest}-message.east |- main.north"
            self.hi_square.padding = "3"

        epilog = (right_chains + left_chains) if self._render_labels else []
        epilog.append(self.current)
        return epilog

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
        # Remove "HEAD" from the labels and make it point to the branch.
        branch = self[name]
        self.branch = branch
        self.head.ref = branch.name
        for labels in self.labels:
            try:
                labels.remove(self.head)
            except ValueError:
                pass
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
        i: int | None = None,  # Possibly insert not in last position.
        # Specify the branch is supposed to move along, defaulting to self.branch.
        # Use empty string to not move any branch.
        _branch: str | None = None,
        **kwargs,
    ) -> PlaceHolder:  # Commit
        i = len(self.commits) if i is None else i
        if len(args) == 1 and not kwargs:
            commit = args[0].copy()
            commit = self.commits.insert(i, commit)
        else:
            commit = self.commits.insert(i, *args, **kwargs)
        hash = commit.hash

        self.labels.insert(i, [])

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

    def add_branch(self, name: str, hash: str) -> PlaceHolder:  # Branch
        i, c = 0, None
        for i, c in enumerate(self.commits):
            if c.hash == hash:
                break
        assert c
        branch = new_label(name)
        self.labels[i].append(branch)
        return branch

    def lock_branch(self, name: str) -> PlaceHolder:  # Label
        lock = new_label(name + "-lock")
        self.locks[name] = lock
        return lock

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
        rbranch = new_label(remote_branch)
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

    def highlight(
        self,
        name: str | PlaceHolder | bool = True,
        on=True,
        ring=True,
    ) -> "Repo":
        """Highlight the given label/commit, or the whole repo if none is given.
        repo.highlight()
        repo.highlight(False)
        repo.highlight('main', True)
        """
        if type(name) is bool:
            on = name
            self.hi_square.on(on)
            return self
        label = cast(PlaceHolder, self[name] if type(name) is str else name)
        if isinstance(commit := label, CommitModifier):
            words = set(commit.type.split())
            if on:
                words.add("hi")
            else:
                words -= {"hi"}
            commit.type = " ".join(words)
        else:
            s = label.style
            i = "hi ring=" if ring else "hi="
            o = "="
            if i in s and not on:
                label.style = s.replace(i, o)
            elif i not in s and on:
                label.style = s.replace(o, i)
        return self

    def hi_on(
        self,
        label: str | List[str] | PlaceHolder | None = None,
        ring=True,
    ) -> "Repo":
        """Simplified version so we can just:
        repo.hi_on()
        repo.hi_on('main')
        """
        if isinstance(labels := label, list):
            [self.hi_on(lab) for lab in labels]
            return self
        if label is None:
            return self.highlight(True, ring)
        label = cast(str, label)
        return self.highlight(label, True, ring)

    def hi_off(
        self,
        label: str | List[str] | PlaceHolder | None = None,
        ring=True,
    ) -> "Repo":
        """Simplified version so we can just:
        repo.hi_off()
        repo.hi_off('main')
        """
        if isinstance(labels := label, list):
            [self.hi_off(lab) for lab in labels]
            return self
        if label is None:
            return self.highlight(False, ring)
        label = cast(str, label)
        return self.highlight(label, False, ring)

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

    def fade_commit(self, c: PlaceHolder | str, kw="fade") -> PlaceHolder:  # Commit
        if type(c) is str:
            c = self[c]
        c = cast(PlaceHolder, c)
        kws = set(c.type.split())
        kws.add(kw)
        c.type = " ".join(kws)
        return c

    def unfade_commit(self, c: PlaceHolder | str, kw="fade") -> PlaceHolder:  # Commit
        if type(c) is str:
            c = self[c]
        c = cast(PlaceHolder, c)
        c.type = " ".join(set(c.type.split()) - {kw})
        return c

    def alter_commits(
        self,
        alter: Callable,
        start: int | List[str] | str = 1,
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

    def pop_commit(self, c: int | str) -> PlaceHolder:  # Commit
        """Either index by location or hash."""
        if type(c) is str:
            i = None
            for i, commit in enumerate(self.commits):
                if commit.hash == c:
                    break
            assert i
        elif type(c) is int:
            i = c
        else:
            assert False  # Type error.
        self.labels.pop(i)
        return self.commits.list.pop(i)
