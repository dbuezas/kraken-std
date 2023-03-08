from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence

from kraken.core.api import Project, Property
from kraken.core.lib.render_file_task import RenderFileTask

from ..gitignore import GitignoreFile, parse_gitignore

# TODO(david-luke): ch2. The apply fn should save a copy of the replaced file .gitignore.old


class GitignoreCheckTask(RenderFileTask):
    """This task ensures that a given set of entries are present in a `.gitignore` file.

    The :attr:`header` property can be set to place the paths below a particular comment in the `.gitignore` file. If
    there is no comment with the given text, it and the paths will be appended to the end of the file. When no header
    is specified, only missing paths will be added to beginning of the `.gitignore` file.

    If :attr:`sort` is enabled, the `.gitignore` file will be sorted (keeping paths grouped under their comments).

    It's common to group this task under the default `fmt` group, as it is similar to formatting a `.gitignore` file.
    """

    file: Property[Path]
    # TODO(david-luke): ch2 Add a `tokens` parameter to the GitignoreSyncTask constructor (with the standard list as default paramter)

    def __init__(self, name: str, project: Project) -> None:
        super().__init__(name, project)
