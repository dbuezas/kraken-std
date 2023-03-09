from __future__ import annotations
from ..gitignore import GITIGNORE_TASK_NAME, DEFAULT_GITIGNORE_TOKENS, GitignoreFile

from pathlib import Path
from typing import Sequence
from kraken.core import Project, Property, Task, TaskStatus
from kraken.core.api import Project, Property
from termcolor import colored

from kraken.common.path import try_relative_to


def as_bytes(v: str | bytes, encoding: str) -> bytes:
    return v.encode(encoding) if isinstance(v, str) else v


# TODO(david-luke): ch2. The apply fn should save a copy of the replaced file .gitignore.old


class GitignoreCheckTask(Task):
    """ """

    file: Property[Path]
    tokens: Property[Sequence[str]] = Property.config(default=DEFAULT_GITIGNORE_TOKENS)
    # TODO(david-luke): ch2 Add a `tokens` parameter to the GitignoreSyncTask constructor (with the standard list as default paramter)

    def __init__(self, name: str, project: Project) -> None:
        super().__init__(name, project)
        self.file.setcallable(lambda: self.project.directory / ".gitignore")

    def execute(self) -> TaskStatus | None:
        file = try_relative_to(self.file.get())
        file_fmt = colored(str(file), "yellow", attrs=["bold"])

        uptask = colored(GITIGNORE_TASK_NAME, "blue", attrs=["bold"])
        message_suffix = f", run {uptask} to generate it"

        if not file.exists():
            return TaskStatus.failed(f'file "{file_fmt}" does not exist{message_suffix}')
        if not file.is_file():
            return TaskStatus.failed(f'"{file}" is not a file')
        gitignore = GitignoreFile.parse_file(file)
        if not gitignore.check_generated_content_tokens(tokens=self.tokens.get()):
            return TaskStatus.failed(
                f'file "{file_fmt}" does not include latest set of generated entries from gitignore.io{message_suffix}'
            )
        if not gitignore.check_generated_content_hash():
            return TaskStatus.failed(f'generated section of file "{file_fmt}" was modified{message_suffix}')

        return TaskStatus.up_to_date(f'file "{file_fmt}" is up to date')
