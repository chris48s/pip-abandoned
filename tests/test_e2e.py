import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from pip_abandoned.cli import get_parser
from pip_abandoned.lib import create_temp_virtualenv

"""
Tests in this file call out to real services (PyPI, GitHub) without mocking
This means:
- They require a GitHub token to run
- They could be slow or flaky
"""


def get_requirements_fixture(name):
    return Path(".") / "tests" / "fixture_data" / name


def test_help():
    result = subprocess.run(["pip-abandoned", "--help"], capture_output=True)
    assert result.returncode == 0
    assert result.stdout == get_parser().format_help().replace(
        "pytest", "pip-abandoned"
    ).encode("utf-8")


def test_version():
    result = subprocess.run(["pip-abandoned", "--version"], capture_output=True)
    assert result.returncode == 0
    assert re.match(r"pip-abandoned \d+.\d+.\d+", result.stdout.decode("utf-8").strip())


def test_search_virtualenv_path_pass():
    with TemporaryDirectory() as tempdir:
        site_packages = create_temp_virtualenv(tempdir)
        result = subprocess.run(
            ["pip-abandoned", "search", site_packages], capture_output=True
        )
        assert result.returncode == 0


def test_search_virtualenv_path_fail():
    with TemporaryDirectory() as tempdir:
        site_packages = create_temp_virtualenv(tempdir)

        # install a known abandoned package into the env
        subprocess.run(
            [Path(tempdir) / "bin" / "pip", "install", "commonmark"],
            capture_output=True,
        )

        result = subprocess.run(
            ["pip-abandoned", "search", site_packages], capture_output=True
        )
        assert (
            b"Packages associated with archived GitHub repos were found:"
            in result.stdout
        )
        assert result.returncode == 9


def test_search_requirements_files_pass():
    result = subprocess.run(
        ["pip-abandoned", "search", "-r", get_requirements_fixture("reqs-pass.txt")],
        capture_output=True,
    )
    assert result.returncode == 0


def test_search_requirements_files_fail():
    result = subprocess.run(
        ["pip-abandoned", "search", "-r", get_requirements_fixture("reqs-fail.txt")],
        capture_output=True,
    )
    assert (
        b"Packages associated with archived GitHub repos were found:" in result.stdout
    )
    assert result.returncode == 9


def test_search_requirements_files_multiple_files():
    result = subprocess.run(
        [
            "pip-abandoned",
            "search",
            "-r",
            get_requirements_fixture("reqs-pass.txt"),
            "-r",
            get_requirements_fixture("reqs-fail.txt"),
            "-vv",
        ],
        capture_output=True,
    )
    assert b"django" in result.stderr
    assert b"commonmark" in result.stderr
