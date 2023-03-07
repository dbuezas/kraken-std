""" Tools for Git versioned projects. """

from __future__ import annotations

from typing import Optional, Sequence, cast

from kraken.core.api import Project

from .tasks.gitignore_sync_task import GitignoreSyncTask
from .version import GitVersion, git_describe

__all__ = ["git_describe", "GitVersion", "GitignoreSyncTask", "gitignore"]

GITIGNORE_TASK_NAME = "gitignore"


def gitignore(
    header: str | None,
    paths: Sequence[str] | str,  # TODO(david-luke): ch1 deprecate
    *,
    project: Project | None = None,
) -> GitignoreSyncTask:
    project = project or Project.current()
    task = cast(Optional[GitignoreSyncTask], project.tasks().get(GITIGNORE_TASK_NAME))
    # TODO(david-luke): ch1 How to singleton
    if task is None:
        task = project.do(GITIGNORE_TASK_NAME, GitignoreSyncTask, group="apply")
        task.create_check()  # TODO(david-luke): ch1 dedicated Task
    task.add_paths(header, [paths] if isinstance(paths, str) else paths)
    return task
