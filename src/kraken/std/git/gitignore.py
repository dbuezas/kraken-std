from __future__ import annotations

import enum
import hashlib
import io
from itertools import islice
from os import PathLike
from pathlib import Path
from typing import Iterable, NamedTuple, TextIO, Sequence
import re

import httpx


GITIGNORE_API_URL = "https://www.toptal.com/developers/gitignore/api/"
GENERATED_GUARD_START = "### START-GENERATED-CONTENT [HASH: {hash}]"
GENERATED_GUARD_START_REGEX = "### START-GENERATED-CONTENT \[HASH: (.*)\]"
GENERATED_TOKENS = "### TOKENS: {tokens}"
GENERATED_TOKEN_REGEX = "### TOKENS: (.*)"
GENERATED_GUARD_DESCRIPTION = """\
# -------------------------------------------------------------------------------------------------
# THIS SECTION WAS AUTOMATICALLY GENERATED BY KRAKEN; DO NOT MODIFY OR YOUR CHANGES WILL BE LOST.
# If you need to define custom gitignore rules, add them below
# -------------------------------------------------------------------------------------------------"""
GENERATED_GUARD_END = "### END-GENERATED-CONTENT"


class GitignoreEntryType(enum.Enum):
    COMMENT = enum.auto()
    BLANK = enum.auto()
    PATH = enum.auto()


class GitignoreEntry(NamedTuple):
    type: GitignoreEntryType
    value: str

    def __str__(self) -> str:
        if self.is_comment():
            return f"# {self.value}"
        return self.value

    def is_comment(self) -> bool:
        return self.type == GitignoreEntryType.COMMENT

    def is_blank(self) -> bool:
        return self.type == GitignoreEntryType.BLANK

    def is_path(self) -> bool:
        return self.type == GitignoreEntryType.PATH


class GitignoreFile:
    entries: list[GitignoreEntry]
    generated_content: str = None
    generated_content_hash: str = None
    generated_content_tokens: Sequence[str] = None

    def __init__(self, entries: list[GitignoreEntry]):
        self.entries = entries

    def find_comment(self, comment: str) -> int | None:
        return next(
            (i for i, e in enumerate(self.entries) if e.is_comment() and e.value.lstrip("#").strip() == comment), None
        )

    def paths(self, start: int | None = None, stop: int | None = None) -> Iterable[str]:
        return (entry.value for entry in islice(self.entries, start, stop) if entry.is_path())

    def add_comment(self, comment: str, index: int | None = None) -> None:
        entry = GitignoreEntry(GitignoreEntryType.COMMENT, comment)
        self.entries.insert(len(self.entries) if index is None else index, entry)

    def add_blank(self, index: int | None = None) -> None:
        entry = GitignoreEntry(GitignoreEntryType.BLANK, "")
        self.entries.insert(len(self.entries) if index is None else index, entry)

    def add_path(self, path: str, index: int | None = None) -> None:
        entry = GitignoreEntry(GitignoreEntryType.PATH, path)
        self.entries.insert(len(self.entries) if index is None else index, entry)

    def remove_path(self, path: str) -> None:
        removed = 0
        while True:
            index = next((i for i, e in enumerate(self.entries) if e.is_path() and e.value == path), None)
            if index is None:
                break
            del self.entries[index]
            removed += 1
        if removed == 0:
            raise ValueError(f'"{path}" not in GitignoreFile')

    def render(self) -> str:
        guarded_section = [
            GENERATED_GUARD_START.format(hash=self.generated_content_hash),
            self.generated_content,
            GENERATED_GUARD_END,
            "",
        ]
        user_content = map(str, self.entries)
        return "\n".join(guarded_section) + "\n" + "\n".join(user_content) + "\n"

    def refresh_generated_content(self, tokens: Sequence[str]) -> None:
        result = httpx.get(GITIGNORE_API_URL + ",".join(tokens))
        # TODO(david): error handling / nice task status erros
        assert result.status_code == 200
        self.generated_content_tokens = tokens
        self.generated_content = "\n".join(
            [
                GENERATED_GUARD_DESCRIPTION,
                GENERATED_TOKENS.format(tokens=", ".join(self.generated_content_tokens)),
                "",
                # TODO(lukeb): This feels hacky - what if the api returns a different string which we need to deal with
                result.text.replace("\r", ""),
                "# -------------------------------------------------------------------------------------------------",
            ]
        )
        # tldr; Line ending weirdness when writing to disk means hashes don't match

        # It appears that the return text from gitignore.io can include \r\r (currently only around the MacOS Icon section)
        # When these characters are stored on disk in the gitignore they become a single \n character. This means that when
        # the file is recalled and rehashed we get a different value. Example code demonstatring this below:

        # import httpx
        # import hashlib
        # result = httpx.get(
        #     "https://www.toptal.com/developers/gitignore/api/macos,linux,windows,visualstudiocode,vim,emacs,clion,intellij,pycharm,jupyternotebooks,git,gcov,node,yarn,python,rust,react,matlab"
        # )
        # original_str = result.text

        # apply_file_write = open("apply-content.txt", "w")
        # apply_file_write.write(original_str)

        # apply_file_read = open("apply-content.txt", "r")
        # recovered_str = apply_file_read.read()

        # print("Original Hash :", hashlib.sha256(original_str.encode("utf-8")).hexdigest())
        # print("Recovered Hash:", hashlib.sha256(recovered_str.encode("utf-8")).hexdigest())

        # This results in a different hash just from storing and reading from disk. Comparing the raw bytes of the string before
        # and after storage it appears that a single difference between \r\r => \n is repsonsible for the hash mismatch.

        # The hacky solution for now is to manually replace \r\r with \n prior to hashing/storage so that nothing changes between
        # disk write/read. This can be achieved in the exmaple above by replacing the following line

        # original_str = result.text -> original_str = result.text.replace("\r\r", "\n")

        # The hashes should now match between storage states. Is there a better way to catch these cases? What if there are other
        # cases we haven't come across yet?

    def refresh_generated_content_hash(self) -> None:
        self.generated_content_hash = hashlib.sha256(self.generated_content.encode("utf-8")).hexdigest()

    def check_generated_content_tokens(self, tokens: Sequence[str]) -> bool:
        return self.generated_content_tokens == tokens

    def check_generated_content_hash(self) -> bool:
        return self.generated_content_hash == hashlib.sha256(self.generated_content.encode("utf-8")).hexdigest()

    def sort_gitignore(self, sort_paths: bool = True, sort_groups: bool = False) -> GitignoreFile:
        """Sorts the entries in the specified gitignore file, keeping paths under a common comment block grouped.
        Will also get rid of any extra blanks.

        :param gitignore: The input to sort.
        :param sort_paths: Whether to sort paths (default: True).
        :param sort_groups: Whether to sort groups among themselves, not just paths within groups (default: False).
        :return: A new, sorted gitignore file.
        """

        class Group(NamedTuple):
            comments: list[str]
            paths: list[str]

        # List of (comments, paths).
        groups: list[Group] = [Group([], [])]

        for entry in self.entries:
            if entry.is_path():
                groups[-1].paths.append(entry.value)
            elif entry.is_comment():
                # If we already have paths in the current group, we open a new group.
                if groups[-1].paths:
                    groups.append(Group([entry.value], []))
                # Otherwise we append the comment to the group.
                else:
                    groups[-1].comments.append(entry.value)

        if sort_groups:
            groups.sort(key=lambda g: "\n".join(g.comments).lower())

        self.entries = []
        for group in groups:
            if sort_paths:
                group.paths.sort(key=str.lower)
            for comment in group.comments:
                self.add_comment(comment)
            for path in group.paths:
                self.add_path(path)
            self.add_blank()

        if self.entries and self.entries[-1].is_blank():
            self.entries.pop()

    @staticmethod
    def parse(file: TextIO | Path | str) -> GitignoreFile:
        if isinstance(file, str):
            return GitignoreFile.parse(io.StringIO(file))
        elif isinstance(file, PathLike):
            with file.open() as fp:
                return GitignoreFile.parse(fp)

        gitignore = GitignoreFile([])
        inside_guard = False
        generated_content = []
        for line in file:
            line = line.rstrip("\n")  # TODO(david) this creates hash mismatches
            if match := re.match(GENERATED_GUARD_START_REGEX, line):
                gitignore.generated_content_hash = match.group(1)
                inside_guard = True
            elif line == GENERATED_GUARD_END:
                inside_guard = False
                gitignore.generated_content = "\n".join(generated_content)
            elif inside_guard:
                generated_content += [line]
                if token_match := re.match(GENERATED_TOKEN_REGEX, line):
                    gitignore.generated_content_tokens = token_match.group(1).split(", ")
            elif line.startswith("#"):
                gitignore.entries.append(GitignoreEntry(GitignoreEntryType.COMMENT, line[1:].lstrip()))
            elif not line.strip():
                gitignore.entries.append(GitignoreEntry(GitignoreEntryType.BLANK, ""))
            else:
                gitignore.entries.append(GitignoreEntry(GitignoreEntryType.PATH, line))

        return gitignore
