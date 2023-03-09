""" Tools for Git versioned projects. """

from __future__ import annotations

from typing import Optional, Sequence, cast

from kraken.core.api import Project

from .tasks.const import GITIGNORE_TASK_NAME, DEFAULT_GITIGNORE_TOKENS
from .tasks.gitignore_sync_task import GitignoreSyncTask
from .tasks.gitignore_check_task import GitignoreCheckTask
from .version import GitVersion, git_describe

__all__ = ["git_describe", "GitVersion", "GitignoreSyncTask", "gitignore"]


def gitignore(
    trash1,
    trash2,
    # TODO(david-luke): Resolve MR questions below
    # Old functionality of passing paths to the gitignore is partially but not fully superseded by gitignore.io (missing some entries like /build for kraken or .python-version for python)
    # Two arguments above are there to avoid kraken-hs errors (breaking changes) for now. 
    # Need feedback on possible solutions:
    #   - Add old functionality to add custom entries into the gitignore from mulitple task calls
    #       or 
    #   - Option to pass all missed hardcoded entries  in single task call (from autoconf)
    # 
    # Need Feedback on how to handle (if we should) multiple invocations of the task with different token lists:
    #   - Overwrite tokens each time
    #       or
    #   - Accumulate tokens over multiple calls
    #       or
    #   - Remove token parameter option from task invocation completely

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
