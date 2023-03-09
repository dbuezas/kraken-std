from __future__ import annotations

from pathlib import Path
from typing import Sequence

from kraken.core.api import Project, Property, TaskStatus
from kraken.core.lib.render_file_task import RenderFileTask
from kraken.core.lib.check_file_contents_task import as_bytes

from ..gitignore import GitignoreFile


# TODO(david-luke): ch2. The apply fn should save a copy of the replaced file .gitignore.old


class GitignoreSyncTask(RenderFileTask):
    """This task ensures that a given set of entries are present in a `.gitignore` file.

    The :attr:`header` property can be set to place the paths below a particular comment in the `.gitignore` file. If
    there is no comment with the given text, it and the paths will be appended to the end of the file. When no header
    is specified, only missing paths will be added to beginning of the `.gitignore` file.

    If :attr:`sort` is enabled, the `.gitignore` file will be sorted (keeping paths grouped under their comments).

    It's common to group this task under the default `fmt` group, as it is similar to formatting a `.gitignore` file.
    """

    file: Property[Path]
    sort_paths: Property[bool] = Property.config(default=True)
    sort_groups: Property[bool] = Property.config(default=False)
    tokens: Property[Sequence[str]]

    def __init__(self, name: str, project: Project) -> None:
        super().__init__(name, project)
        self.file.setcallable(lambda: self.project.directory / ".gitignore")
        self.content.setcallable(lambda: self.generate_file_contents(self.file.get()))

    def prepare(self) -> TaskStatus | None:
        try:
            return super().prepare()
        except AssertionError as assert_error:
            return TaskStatus.failed(f"Could not generate to the gitignore file: {assert_error}")

    def execute(self) -> TaskStatus:
        try:
            file = self.file.get()
            if file.exists():
                existing_content = file.read_bytes()
                new_content = as_bytes(self.content.get(), self.encoding.get())
                if existing_content != new_content:
                    backup_file = self.project.directory / ".gitignore.old"
                    backup_file.write_bytes(existing_content)

            return super().execute()
        except AssertionError as assert_error:
            return TaskStatus.failed(f"Could not generate to the gitignore file: {assert_error}")

    def generate_file_contents(self, file: Path) -> str | bytes:
        if file.exists():
            gitignore = GitignoreFile.parse(file)
        else:
            gitignore = GitignoreFile([])
        gitignore.refresh_generated_content(tokens=self.tokens.get())
        gitignore.refresh_generated_content_hash()
        gitignore.sort_gitignore(self.sort_paths.get(), self.sort_groups.get())
        return gitignore.render()
