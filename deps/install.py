#!/usr/bin/env python
"""Installer for Barista dependencies.

This script installs required CLI tools (e.g., wrk, wrk2) either by:
- downloading prebuilt binaries (type="download"), or
- building them from source (type="build").

It reads a TOML environment file (deps/env*.toml), validates presence via
user-provided or built-in checks, and installs into deps/bin.
"""
from __future__ import annotations
from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict
from collections.abc import Callable
import subprocess
import os
import logging
import sys
import io
import tempfile
import shutil
from contextlib import redirect_stdout, redirect_stderr
import platform

INSTALL_DIR = Path(__file__).absolute().parent / "bin" # barista/deps/bin
REPO_ROOT = Path(__file__).absolute().parent.parent    # barista
VENV_DIR = REPO_ROOT / "venv"                          # barista/venv
VENV_BIN = VENV_DIR / "bin"                            # barista/venv/bin
TMP_DIR = Path(__file__).absolute().parent / "tmp"     # barista/deps/tmp
ENV = os.environ.copy()
ENV["PATH"] = f"{VENV_BIN}:{INSTALL_DIR}:{ENV['PATH']}"

def _normalize_os(name: str) -> str:
    n = name.lower()
    if n.startswith("linux"):
        return "linux"
    if n.startswith("darwin") or n.startswith("mac"):
        return "darwin"
    if n.startswith("win"):
        return "windows"
    if n.startswith("freebsd"):
        return "freebsd"
    return n

def _normalize_arch(name: str) -> str:
    n = name.lower()
    if n in ("x86_64", "amd64"):
        return "amd64"
    if n in ("aarch64", "arm64"):
        return "aarch64"
    # keep common others as-is
    return n

def get_current_os_arch() -> tuple[str, str]:
    """Return normalized (os, arch) for compatibility checks."""
    return _normalize_os(platform.system()), _normalize_arch(platform.machine())

def empty_dir_keep_gitignore(path: Path) -> None:
    """Remove all entries under the given directory except a potential .gitignore, preserving the directory itself."""
    path.mkdir(parents=True, exist_ok=True)
    for p in path.iterdir():
        if p.name == ".gitignore":
            continue
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        else:
            try:
                p.unlink()
            except FileNotFoundError:
                pass

@dataclass(frozen=True)
class Dependency:
    """Abstract dependency definition with health-check and installer hook."""

    name: str
    check_command: List[str]
    check_ret_code: int
    check_output_function: Optional[Callable[[str], bool]]

    def check_and_maybe_install(self, force: bool) -> None:
        """Install the dependency when forced or when the check fails; re-check after install."""
        if force or not self.check_if_installed():
            self.install()
        if not self.check_if_installed():
            raise ImportError(f"Failed to install '{self.name}' tool!")

    def check_if_installed(self) -> bool:
        try:
            proc = subprocess.run(self.check_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV)
        except FileNotFoundError:
            return False
        if proc.returncode != self.check_ret_code:
            return False
        if self.check_output_function is not None and not self.check_output_function(proc.stdout.decode("utf-8")):
            return False
        return True

    def install(self) -> None:
        """Perform the installation of the dependency. Must be implemented by subclasses."""
        raise NotImplementedError

    @staticmethod
    def create_check_output_function(name: str, code: Optional[str]) -> Optional[Callable[[str], bool]]:
        """Create a validation function from a small Python snippet.

        The snippet receives variables:
          - stdout: str (captured stdout from check_command)
          - valid: bool (must be set by the snippet)

        Returns:
            A callable that evaluates the snippet and returns True/False, or None if no snippet provided.
        """
        if not code:
            return None
        def check_output_function(stdout: str) -> bool:
            locals = {"stdout": stdout, "valid": False}
            logger = io.StringIO()
            try:
                with redirect_stdout(logger):
                    with redirect_stderr(logger):
                        exec(code, {}, locals)
                        return locals["valid"]
            except Exception as e:
                logging.error(f"Error running user-defined check function for {name}: {e}")
                return False
        return check_output_function


@dataclass(frozen=True)
class DownloadableDependency(Dependency):
    """Dependency that downloads a prebuilt archive and extracts the binary into INSTALL_DIR."""

    archive_name: str
    downloads_repo: str
    install_dir: Path

    def install(self) -> None:
        """Download and extract the binary archive into INSTALL_DIR."""
        cmd = f"curl -L {self.downloads_repo}/{self.name}/{self.archive_name} | tar -xz -C {self.install_dir} --wildcards --strip-components=1 */{self.name}"
        logging.info(f"Installing '{self.name}' tool with command: '{cmd}'")
        subprocess.run(cmd, shell=True)

    @staticmethod
    def from_dict(dependency: Dict) -> DownloadableDependency:
        """Create a DownloadableDependency from a TOML-provided dictionary."""
        name = dependency["name"]
        return DownloadableDependency(
            name=name,
            check_command=dependency["check_command"],
            check_ret_code=dependency["check_ret_code"],
            check_output_function=Dependency.create_check_output_function(name, dependency.get("check_output_function")),
            archive_name=dependency["archive_name"],
            downloads_repo=dependency["repo"],
            install_dir=INSTALL_DIR
        )


@dataclass(frozen=True)
class BuildableDependency(Dependency):
    """Dependency that is built from source via a sequence of shell commands."""

    build_cmds: List[str]
    artifact_name: str
    dest_name: str
    git_ref: Optional[str] = None

    def install(self) -> None:
        """Execute build_cmds in a temporary workdir, then copy the built artifact into INSTALL_DIR."""
        logging.info(f"Installing '{self.name}' by building from source.")
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        temp_dir = Path(tempfile.mkdtemp(prefix=f"{self.name}-", dir=TMP_DIR))
        success = False
        try:
            for cmd in self.build_cmds:
                logging.info(f"Running command (cwd={temp_dir}): {cmd}")
                result = subprocess.run(cmd, shell=True, cwd=temp_dir, env=ENV)
                if result.returncode != 0:
                    raise RuntimeError(f"Build command failed for {self.name}: {cmd}")
            src = temp_dir / self.artifact_name
            dest = INSTALL_DIR / self.dest_name
            logging.info(f"Copying built artifact '{src}' to '{dest}'.")
            if not src.exists():
                raise FileNotFoundError(f"Built artifact not found for {self.name}: {src}")
            shutil.copy2(src, dest)
            dest.chmod(0o755)
            success = True
        finally:
            # Preserve build directory on failure for diagnostics; remove on success unless overridden.
            if success and "BARISTA_KEEP_BUILD_DIRS" not in os.environ:
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
            else:
                logging.info(f"Build directory preserved at {temp_dir}")

    @staticmethod
    def from_dict(dependency: Dict) -> 'BuildableDependency':
        """Create a BuildableDependency from a TOML-provided dictionary."""
        name = dependency["name"]
        return BuildableDependency(
            name=name,
            check_command=dependency["check_command"],
            check_ret_code=dependency["check_ret_code"],
            check_output_function=Dependency.create_check_output_function(name, dependency.get("check_output_function")),
            build_cmds=dependency.get("build_cmds"),
            artifact_name=dependency.get("artifact_name"),
            dest_name=dependency.get("dest_name", name),
            git_ref=dependency.get("git_ref")
        )


def read_toml_file(toml_file_path: Path) -> Dict:
    # tomllib was included in python standard library with version 3.11
    try:
        import tomllib
        with open(toml_file_path, mode="rb") as f:
            return tomllib.load(f)
    except ImportError:
        pass

    # fallback to 'toml' library if tomllib is not present
    try:
        import toml
        with open(toml_file_path, mode="rt") as f:
            return toml.loads(f.read())
    except ImportError:
        logging.error(f"Could not read the {toml_file_path} toml file because there is no toml parser installed. Use python3.11+ or install `toml` with pip.")
        raise


def read_dependencies_from_env_file(env_file_path: Path) -> Dict[str, Dependency]:
    """Parse an environment TOML file and build a mapping of dependency name -> Dependency instance."""
    env_data = read_toml_file(env_file_path)
    dependencies = {}
    for dependency in env_data.get("dependencies", []):
        dep_type = dependency["type"]
        name = dependency["name"]
        if dep_type == "download":
            dependencies[name] = DownloadableDependency.from_dict(dependency)
        elif dep_type == "build":
            dependencies[name] = BuildableDependency.from_dict(dependency)
        else:
            raise ValueError(f"Unknown dependency of type '{dep_type}' encountered!")
    return dependencies


def read_env_file(env_file_path: Path) -> tuple[Dict[str, Dependency], Optional[Path], Optional[list[str]], Optional[list[str]]]:
    """Read the env file and return (dependencies, fallback_path, supported_os, supported_arch).

    Args:
        env_file_path: Absolute path to the TOML environment file.

    Returns:
        A tuple containing:
          - dict mapping dependency name to Dependency instance
          - Optional absolute Path to a fallback env file, if defined
          - Optional list of supported OS names
          - Optional list of supported arch names
    """
    env_data = read_toml_file(env_file_path)

    fallback_path: Optional[Path] = None
    fallback_rel = env_data.get("fallback_env")
    if fallback_rel:
        # Treat fallback path as relative to repo root
        fallback_path = (REPO_ROOT / fallback_rel).resolve()

    supported_os = env_data.get("supported_os")
    supported_arch = env_data.get("supported_arch")
    # Normalize lists if present
    if supported_os is not None:
        supported_os = [_normalize_os(str(x)) for x in supported_os]
    if supported_arch is not None:
        supported_arch = [_normalize_arch(str(x)) for x in supported_arch]

    deps: Dict[str, Dependency] = {}
    for dependency in env_data.get("dependencies", []):
        dep_type = dependency["type"]
        name = dependency["name"]
        if dep_type == "download":
            deps[name] = DownloadableDependency.from_dict(dependency)
        elif dep_type == "build":
            deps[name] = BuildableDependency.from_dict(dependency)
        else:
            raise ValueError(f"Unknown dependency of type '{dep_type}' encountered in {env_file_path}!")
    return deps, fallback_path, supported_os, supported_arch


def main() -> None:
    """CLI entry point for installing project dependencies."""
    parser = ArgumentParser(prog="install", description="Installs missing (or all if forced) dependencies of the 'barista' project.")
    parser.add_argument("--force", action="store_true", help="Force the installation of dependencies regardless of whether or not they are already installed. Cleans the installation (deps/bin) directory.")
    parser.add_argument("--env-file", default="deps/env.toml", help="Path to environment TOML file.")
    parser.add_argument("--no-fallback", action="store_true", help="Disable using fallback environments.")
    args = vars(parser.parse_args())

    env_file = Path(args["env_file"])
    force = args["force"]
    if not env_file.is_absolute():
        env_file = (REPO_ROOT / env_file).resolve()

    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream= sys.stdout
    )

    if force:
        empty_dir_keep_gitignore(INSTALL_DIR)

    visited: set[Path] = set()
    current_env: Path = env_file
    while True:
        if current_env in visited:
            raise RuntimeError(f"Fallback loop detected; env '{current_env}' has already been used: {visited}")
        visited.add(current_env)

        dependencies, fallback_path, supported_os, supported_arch = read_env_file(current_env)
        try:
            # Compatibility check
            cur_os, cur_arch = get_current_os_arch()
            compatible = True
            if supported_os is not None and cur_os not in supported_os:
                compatible = False
            if supported_arch is not None and cur_arch not in supported_arch:
                compatible = False
            if not compatible:
                raise Exception(f"Environment '{current_env}' not compatible with current system (os={cur_os}, arch={cur_arch}).")

            # Dependency installation
            for dependency in dependencies.values():
                dependency.check_and_maybe_install(force)
            break
        except Exception as e:
            if args.get("no_fallback", False):
                raise
            if not fallback_path or fallback_path in visited:
                raise
            if not compatible:
                logging.warning(f"Environment '{current_env}' not compatible with current system (os={cur_os}, arch={cur_arch}). Trying fallback '{fallback_path}'.")
            else:
                logging.warning(f"Install failed using env '{current_env}': {e}. Trying fallback env '{fallback_path}'.")
            current_env = fallback_path

    logging.info("=================================================================")
    logging.info("Finished installing Barista's dependencies!")
    logging.info("=================================================================")


if __name__ == "__main__":
    main()
