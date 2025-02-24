from __future__ import annotations

import os
import shlex
import subprocess as sp
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from kraken.core.api import Project, Property, Task, TaskStatus

from kraken.std.cargo.manifest import ArtifactKind, CargoMetadata
from kraken.std.descriptors.resource import BinaryArtifact, LibraryArtifact


@dataclass
class CargoBinaryArtifact(BinaryArtifact):
    pass


@dataclass
class CargoLibraryArtifact(LibraryArtifact):
    pass


class CargoBuildTask(Task):
    """This task runs `cargo build` using the specified parameters. It will respect the authentication
    credentials configured in :attr:`CargoProjectSettings.auth`."""

    #: The build target (debug or release). If this is anything else, the :attr:`out_binaries` will be set
    #: to an empty list instead of parsed from the Cargo manifest.
    target: Property[str]

    #: Additional arguments to pass to the Cargo command-line.
    additional_args: Property[List[str]] = Property.default_factory(list)

    #: Whether to build incrementally or not.
    incremental: Property[Optional[bool]] = Property.default(None)

    #: Environment variables for the Cargo command.
    env: Property[Dict[str, str]] = Property.default_factory(dict)

    #: Number of times to retry before failing this job
    retry_attempts: Property[int] = Property.default(0)

    #: An output property for the Cargo binaries that are being produced by this build.
    out_binaries: Property[List[CargoBinaryArtifact]] = Property.output()

    #: An output property for the Cargo libraries that are being produced by this build.
    out_libraries: Property[List[CargoLibraryArtifact]] = Property.output()

    def __init__(self, name: str, project: Project) -> None:
        super().__init__(name, project)

    def get_description(self) -> str | None:
        command = self.get_cargo_command({})
        self.make_safe(command, {})
        return f"Run `{' '.join(command)}`."

    def get_cargo_command_additional_flags(self) -> List[str]:
        return shlex.split(os.environ.get("KRAKEN_CARGO_BUILD_FLAGS", ""))

    def get_cargo_command(self, env: Dict[str, str]) -> List[str]:
        incremental = self.incremental.get()
        if incremental is not None:
            env["CARGO_INCREMENTAL"] = "1" if incremental else "0"
        return ["cargo", "build"] + self.additional_args.get()

    def make_safe(self, args: List[str], env: Dict[str, str]) -> None:
        pass

    def execute(self) -> TaskStatus:
        env = self.env.get()
        command = self.get_cargo_command(env) + self.get_cargo_command_additional_flags()

        safe_command = command[:]
        safe_env = env.copy()
        self.make_safe(safe_command, safe_env)
        self.logger.info("%s [env: %s]", safe_command, safe_env)

        out_binaries = []
        out_libraries = []
        if self.target.get_or(None) in ("debug", "release"):
            # Expose the output binaries that are produced by this task.
            # We only expect a binary to be built if the target is debug or release.
            manifest = CargoMetadata.read(self.project.directory)
            target_dir = self.project.directory / os.getenv("CARGO_TARGET_DIR", "target") / self.target.get()
            for artifact in manifest.artifacts:
                # Rust binaries have an extensionless name whereas libraries are prefixed with "lib" and suffixed with
                #
                # - ".rlib" for Rust libraries
                # - ".so" (Linux), ".dylib" (macOS) or ".dll" (Windows) for dynamic Rust and system libraries
                # - ".a" (Linux, macOS) or ".lib" (Windows) for static system libraries
                #
                # We create all options for libraries and check for presence of at least one later.
                if artifact.kind is ArtifactKind.BIN:
                    out_binaries.append(CargoBinaryArtifact(artifact.name, target_dir / artifact.name))
                elif artifact.kind is ArtifactKind.LIB:
                    base_name = f"lib{artifact.name}"
                    for file_extension in ["rlib", "so", "dylib", "dll", "a", "lib"]:
                        filename = ".".join([base_name, file_extension]).replace("-", "_")
                        out_libraries.append(CargoLibraryArtifact(base_name, target_dir / filename))

        self.out_binaries.set(out_binaries)
        self.out_libraries.set(out_libraries)

        total_attempts = self.retry_attempts.get() + 1

        while total_attempts > 0:
            result = sp.call(command, cwd=self.project.directory, env={**os.environ, **env})

            if result == 0:
                # Check that binaries which were due have been built.
                for out_bin in out_binaries:
                    assert out_bin.path.is_file(), out_bin
                # Check that at least one library has been built if libraries were due.
                assert not out_libraries or any(lib.path.is_file() for lib in out_libraries), out_libraries[0].name
                break
            else:
                total_attempts -= 1
                self.logger.warn("%s failed with result %s", safe_command, result)
                self.logger.warn("There are %s attempts remaining", total_attempts)
                if total_attempts > 0:
                    self.logger.info("Waiting for 10 seconds before retrying..")
                    time.sleep(10)

        return TaskStatus.from_exit_code(safe_command, result)
