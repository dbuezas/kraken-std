from __future__ import annotations
from ..gitignore import GitignoreFile
from .const import GITIGNORE_TASK_NAME

from pathlib import Path
from typing import Sequence
from kraken.core import Project, Property, Task, TaskStatus
from kraken.core.api import Project, Property
from termcolor import colored

from kraken.common.path import try_relative_to


def as_bytes(v: str | bytes, encoding: str) -> bytes:
    return v.encode(encoding) if isinstance(v, str) else v


class GitignoreCheckTask(Task):
    """ """

    file: Property[Path]
    tokens: Property[Sequence[str]]
    sort_paths: Property[bool] = Property.config(default=True)
    sort_groups: Property[bool] = Property.config(default=False)

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
        gitignore = GitignoreFile.parse(file)
        if not gitignore.check_generated_content_tokens(tokens=self.tokens.get()):
            return TaskStatus.failed(
                f'file "{file_fmt}" does not include latest set of generated entries from gitignore.io{message_suffix}'
            )
        if not gitignore.check_generated_content_hash():
            return TaskStatus.failed(f'generated section of file "{file_fmt}" was modified{message_suffix}')

        unsorted = gitignore.render()

        gitignore.sort_gitignore(self.sort_paths.get(), self.sort_groups.get())
        sorted = gitignore.render()

        if unsorted != sorted:
            return TaskStatus.failed(f'"{file_fmt}" is not sorted{message_suffix}')

        return TaskStatus.up_to_date(f'file "{file_fmt}" is up to date')
