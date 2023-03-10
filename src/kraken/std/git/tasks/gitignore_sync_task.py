from __future__ import annotations

from pathlib import Path
from typing import Sequence

from kraken.core.api import Project, Property, TaskStatus, Task
from kraken.core.lib.check_file_contents_task import as_bytes

from ..gitignore import GitignoreFile, GitignoreException
import logging

logger = logging.getLogger(__name__)


class GitignoreSyncTask(Task):
    # TODO(david): update docs
    """This task ensures that a given set of entries are present in a `.gitignore` file.

    The :attr:`header` property can be set to place the paths below a particular comment in the `.gitignore` file. If
    there is no comment with the given text, it and the paths will be appended to the end of the file. When no header
    is specified, only missing paths will be added to beginning of the `.gitignore` file.

    If :attr:`sort` is enabled, the `.gitignore` file will be sorted (keeping paths grouped under their comments).

    It's common to group this task under the default `fmt` group, as it is similar to formatting a `.gitignore` file.
    """

    sort_paths: Property[bool] = Property.config(default=True)
    sort_groups: Property[bool] = Property.config(default=False)
    tokens: Property[Sequence[str]]
    extra_paths: Property[Sequence[str]]

    def generate_file_contents(self, file: Path) -> str | bytes:
        gitignore = GitignoreFile([])
        if file.exists():
            try:
                gitignore = GitignoreFile.parse(file)
            except:
                logger.warn(f"Malformed gitignore detected - reseting (previous version saved to .gitignore.old)")
        gitignore.refresh_generated_content(tokens=self.tokens.get(), extra_paths=self.extra_paths.get())
        gitignore.refresh_generated_content_hash()
        gitignore.sort_gitignore(self.sort_paths.get(), self.sort_groups.get())
        return gitignore.render()

    def execute(self) -> TaskStatus:
        file = self.project.directory / ".gitignore"
        try:
            content = self.generate_file_contents(file)
            new_str = as_bytes(content, "utf-8")
            if file.exists():
                old_str = file.read_bytes()
                if old_str != new_str:
                    backup_file = self.project.directory / ".gitignore.old"
                    backup_file.write_bytes(old_str)
            file.write_bytes(new_str)

        except GitignoreException as gitignore_exception:
            return TaskStatus.failed(f"Could not generate to the gitignore file: {gitignore_exception}")
