""" Tools for Git versioned projects. """

from __future__ import annotations

from typing import Optional, Sequence, cast

from kraken.core.api import Project

from .gitignore import GITIGNORE_TASK_NAME, DEFAULT_GITIGNORE_TOKENS
from .tasks.gitignore_sync_task import GitignoreSyncTask
from .tasks.gitignore_check_task import GitignoreCheckTask
from .version import GitVersion, git_describe

__all__ = ["git_describe", "GitVersion", "GitignoreSyncTask", "gitignore"]


def gitignore(
    trash1,  # TODO(david): upgrade gitignore callers and remove these lines
    trash2,
    *,
    project: Project | None = None,
    tokens: Sequence[str] = DEFAULT_GITIGNORE_TOKENS,
) -> GitignoreSyncTask:
    project = project or Project.current()
    task = cast(Optional[GitignoreSyncTask], project.tasks().get(GITIGNORE_TASK_NAME))
    if task is None:
        task = project.do(GITIGNORE_TASK_NAME, GitignoreSyncTask, group="apply", tokens=tokens)
        project.do(GITIGNORE_TASK_NAME + ".check", GitignoreCheckTask, group="check", tokens=tokens)
    return task
