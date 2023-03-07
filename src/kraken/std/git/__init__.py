""" Tools for Git versioned projects. """

from __future__ import annotations

from typing import Optional, Sequence, cast

from kraken.core.api import Project

from .tasks.gitignore_sync_task import GitignoreSyncTask
from .tasks.gitignore_check_task import GitignoreCheckTask
from .version import GitVersion, git_describe

__all__ = ["git_describe", "GitVersion", "GitignoreSyncTask", "gitignore"]

GITIGNORE_TASK_NAME = "gitignore"


def gitignore(
    *,
    project: Project | None = None,
) -> GitignoreSyncTask:
    project = project or Project.current()
    task = cast(Optional[GitignoreSyncTask], project.tasks().get(GITIGNORE_TASK_NAME))
    if task is None:
        task = project.do(GITIGNORE_TASK_NAME, GitignoreSyncTask, group="apply")
        project.do(GITIGNORE_TASK_NAME + ".check", GitignoreCheckTask, group="check")
    return task
