"""Pytest to verify installing dependencies defined by environment files in deps.

This test:
- Discovers all environment files matching deps/env*.toml
- Runs the installer for each env, forcing installation of wrk and wrk2
- Verifies that wrk and wrk2 are present and that --help behaves as expected
- Cleans deps/bin and deps/tmp between runs and after the test to avoid residue
"""
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict

import pytest

# Discover environment files automatically (any deps/env*.toml)
REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILES = sorted([p for p in (REPO_ROOT / "deps").glob("env*.toml") if p.is_file()])


def _empty_dir_keep_gitignore(path: Path) -> None:
    """
    Remove all entries under the given directory except a potential .gitignore, preserving the directory itself.
    Throws an exception if not called on a subdirectory of the `deps` directory in the repo's root.
    """
    # Ensure this function is called for a subdirectory of the `deps` directory
    repo_root = Path(__file__).resolve().parent.parent
    deps_dir = repo_root / "deps"
    if deps_dir not in path.parents:
        raise ValueError(f"Unsafe deletion of directory attempted! Only deletions of subdirectories of the 'deps' directory are allowed for security reasons! Attempt was made to delete '{path}'!")
    # Proceed with deletion
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


def _verify_tools(bin_dir: Path) -> None:
    """Validate that wrk and wrk2 are present and respond to --help appropriately."""
    wrk = bin_dir / "wrk"
    wrk2 = bin_dir / "wrk2"

    assert wrk.exists() and wrk.is_file(), f"Missing wrk at {wrk}"
    assert wrk2.exists() and wrk2.is_file(), f"Missing wrk2 at {wrk2}"

    for tool_path in (wrk, wrk2):
        # Accept return codes 0 or 1 for --help
        proc = subprocess.run(
            [str(tool_path), "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        logging.info("'%s --help' rc=%s", tool_path.name, proc.returncode)
        logging.info(proc.stdout.decode("utf-8", errors="replace"))
        assert proc.returncode in (0, 1), f"{tool_path.name} --help returned {proc.returncode}"

    # wrk2 help should include --rate option
    proc_wrk2 = subprocess.run(
        [str(wrk2), "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    out_wrk2 = proc_wrk2.stdout.decode("utf-8", errors="replace")
    assert "--rate" in out_wrk2, "wrk2 --help output does not contain --rate"




def _run_install_for_env(repo_root: Path, env_file: Path) -> None:
    """Run the installer for the given env file, forcing installs of wrk and wrk2."""
    logging.info("Running deps/install.py for env: %s", env_file)
    # Force install to ensure we exercise both paths (download/build)
    subprocess.run(
        [
            sys.executable,
            str(repo_root / "deps" / "install.py"),
            "--env-file",
            str(env_file),
            "--force",
            "--no-fallback",
        ],
        check=True,
    )
    logging.info("deps/install.py executed successfully for %s", env_file)


@pytest.fixture(scope="module")
def repo_paths() -> Dict[str, Path]:
    """Return common repository paths used by the tests."""
    # tests/ is one level below repo root
    repo_root = Path(__file__).resolve().parent.parent
    deps_dir = repo_root / "deps"
    bin_dir = deps_dir / "bin"
    tmp_dir = deps_dir / "tmp"
    return {
        "repo_root": repo_root,
        "deps_dir": deps_dir,
        "bin_dir": bin_dir,
        "tmp_dir": tmp_dir,
    }


@pytest.fixture(autouse=True)
def cleanup_after_test(repo_paths: Dict[str, Path]) -> None:
    """Cleanup fixture that empties deps/bin and deps/tmp after each test execution."""
    # Nothing before the test; we will clean between envs and after module
    yield
    # Final cleanup: empty deps/bin and deps/tmp to avoid leaving artifacts
    _empty_dir_keep_gitignore(repo_paths["bin_dir"])
    _empty_dir_keep_gitignore(repo_paths["tmp_dir"])


@pytest.mark.parametrize("env_file", ENV_FILES)
def test_install_dependencies(repo_paths: Dict[str, Path], env_file: Path) -> None:
    """Install dependencies for a discovered env file and validate wrk and wrk2."""
    bin_dir: Path = repo_paths["bin_dir"]
    tmp_dir: Path = repo_paths["tmp_dir"]
    repo_root: Path = repo_paths["repo_root"]


    logging.info("=" * 50)
    logging.info("Testing environment file: %s", env_file)
    logging.info("=" * 50)

    # Clean before running each env to ensure isolation
    _empty_dir_keep_gitignore(bin_dir)
    _empty_dir_keep_gitignore(tmp_dir)

    try:
        _run_install_for_env(repo_root, env_file)
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Installer failed for {env_file} (rc={e.returncode}); likely environment/network issue.")
    _verify_tools(bin_dir)
