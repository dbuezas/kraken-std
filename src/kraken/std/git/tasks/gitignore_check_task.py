from __future__ import annotations
from ..gitignore import GitignoreFile, parse_gitignore

from pathlib import Path
from typing import Dict, List, Optional, Sequence
from kraken.core import Project, Property, Supplier, Task, TaskStatus
from kraken.core.api import Project, Property
from kraken.core.lib.render_file_task import RenderFileTask
from termcolor import colored

from kraken.common.path import try_relative_to

GITIGNORE_TASK_NAME = 'gitinogre FIX ME'  # TODO(david): share this with __init__.py


def as_bytes(v: str | bytes, encoding: str) -> bytes:
    return v.encode(encoding) if isinstance(v, str) else v


# TODO(david-luke): ch2. The apply fn should save a copy of the replaced file .gitignore.old


class GitignoreCheckTask(Task):
    """
    """

    file: Property[Path]
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
        if not parse_gitignore(file).validate_tokens():
            return TaskStatus.failed(f'file "{file_fmt}" is not up to date{message_suffix}')
        if not parse_gitignore(file).validate_generated_content_hash():
            return TaskStatus.failed(f'guarded section of file "{file_fmt}" was modified{message_suffix}')

        return TaskStatus.succeeded(f'file "{file_fmt}" is up to date')
