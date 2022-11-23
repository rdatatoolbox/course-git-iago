"""Craft/edit a simple file tree.
"""

from typing import cast

from document import HighlightSquare
from modifiers import (
    AnonymousPlaceHolder,
    ListBuilder,
    MakePlaceHolder,
    PlaceHolder,
    TextModifier,
    render_method,
)


class FileTree(TextModifier):
    """One chain of files, arranged top-down.
    Be careful that the last one within every folder must be marked with 'last'.
    Keep it simple as subsubfolders and 'step out' are not exactly used/implemented yet.
    """

    def __init__(self, input: str):
        intro, files = input.split("{\n", 1)
        self.intro = AnonymousPlaceHolder(
            r"\FileTree[<anchor>][<name>]{<location>}", "parse", intro
        )
        files = files.rsplit("}", 1)[0]
        self.list = FileTreeLines.parse(files)
        self._sub = False  # Raise when in subfolder.

    @property
    def name(self):
        return self.intro.name

    @render_method
    def render(self) -> str:
        return self.intro.render() + "{\n" + self.list.render() + "}\n"

    def clear(self):
        self.list.clear()
        self._sub = False

    def populate(self, filetree: "FileTree") -> "FileTree":
        """Import/copy all files from another value."""
        self.clear()
        for file in filetree.list:
            self.list.append(file.copy())
        self._sub = filetree._sub
        return self

    def append(
        self,
        filename: str | PlaceHolder,  # FileTreeLine
        # Use only 'file' or 'folder',
        # with possible 'in' additional keyword
        # for the first file stepping in a subfolder chain.
        keywords: str = "file",
        mod: str = "0",
        # Name for the file node, otherwise defaults to uncapitalized filename base.
        name: str | None = None,
    ) -> PlaceHolder:  # FileTreeLine

        if type(filename) is str:
            # Construct an actual file and pass again recursively to the same function.
            words = set(keywords.split())
            allow_list = set("file folder stepin".split())
            if invalid := words - allow_list:
                raise ValueError(
                    f"Invalid keyword in file type: {repr(next(iter(invalid)))}."
                )
            if "file" in words and "folder" in words:
                raise ValueError("Cannot be both 'file' and 'folder' type.")
            if not ("file" in words or "folder" in words):
                words.add("file")

            if name is None:
                if "." in filename:
                    name, ext = (s.lower().strip() for s in filename.rsplit(".", 1))
                    if not name:  # Useful for special names like '.git'.
                        name = ext
                else:
                    name = filename.lower().strip()
                # Avoid tikz special chars and duplicates.
                assert "." not in name
                assert not any(f.name == name for f in self.list)
            file = FileTreeLine.new(" ".join(words), mod, name, filename)
            return self.append(file)

        file = cast(PlaceHolder, filename)  # FileTreeLine
        words = set(file.type.split())
        if "stepin" in words:
            self._sub = True
            words -= {"connect"}
            words.add("last")
        elif self._sub:
            self.remove_from_type(self.list[-1], "last")
            words.add("connect")
            words.add("last")
        else:
            words -= {"connect"}
            words -= {"last"}
        file.type = " ".join(words)
        return self.list.append(file)

    @staticmethod
    def remove_from_type(file: PlaceHolder, keyword: str):
        file.type = " ".join(set(file.type.split()) - {keyword})

    @staticmethod
    def add_to_type(file: PlaceHolder, keyword: str):
        kws = set(file.type.split())
        kws.add(keyword)
        file.type = " ".join(kws)

    def remove(self, file: PlaceHolder):
        """Remove from the chain, taking care of preserving the 'last' keyword."""
        i = self.list.list.index(file)
        removed = self.list.list.pop(i)
        was_last = len(self.list) == i
        if "stepin" in removed.type:
            assert was_last
            self._sub = False
        elif was_last:
            new_last = self.list[-1]
            if self._sub and not "stepin" in new_last.type:
                self.add_to_type(new_last, "last")

    def __getitem__(self, name: str) -> PlaceHolder:  # FileTreeLine
        """Search and retrieve file by name (*not* filename)."""
        for file in self.list:
            if file.name == name:
                return file
        raise KeyError(f"No such file in file tree: {repr(name)}.")

    def all_mod(self, mod: str) -> "FileTree":
        """Set all content to the same mode,
        temporary setting all items to 'last'.
        Reset with mod='0'.
        """
        assert self.list.list
        for i, file in enumerate(self.list):
            file.mod = mod
            if "connect" in file.type or "stepin" in file.type:
                if mod == "0":
                    if i < len(self.list) - 1:
                        self.remove_from_type(file, "last")
                else:
                    self.add_to_type(file, "last")
        return self

    def highlight(self, name, pad=1.2) -> PlaceHolder:  # HighlightSquare
        """Highlight one file in particular."""
        return self.add_epilog(
            HighlightSquare.new(
                f"{name}-icon.south west",
                f"{name}-filename.east |- {name}-icon.north",
                padding=pad,
            )
        )


FileTreeLineModifier, FileTreeLine = MakePlaceHolder(
    "FileTreeLine",
    r"<type>/<mod>/<name>/<filename>",
)
FileTreeLines = ListBuilder(FileTreeLine, ",\n", tail=True)
