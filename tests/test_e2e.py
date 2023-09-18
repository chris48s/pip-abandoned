import re
import subprocess
import sys
import venv
from pathlib import Path
from tempfile import TemporaryDirectory

from pip_abandoned.cli import get_parser

"""
Tests in this file call out to real services (PyPI, GitHub) without mocking
This means:
- They require a GitHub token to run
- They could be slow or flaky
"""


def get_python_version():
    return f"python{sys.version_info.major}.{sys.version_info.minor}"


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


def test_search_pass():
    with TemporaryDirectory() as tempdir:
        # create a temp virtualenv
        builder = venv.EnvBuilder(
            system_site_packages=False,
            clear=True,
            symlinks=False,
            upgrade=False,
            with_pip=True,
        )
        builder.create(tempdir)

        site_packages = Path(tempdir) / "lib" / get_python_version() / "site-packages"
        result = subprocess.run(
            ["pip-abandoned", "search", site_packages], capture_output=True
        )
        assert result.returncode == 0


def test_search_fail():
    with TemporaryDirectory() as tempdir:
        # create a temp virtualenv
        builder = venv.EnvBuilder(
            system_site_packages=False,
            clear=True,
            symlinks=False,
            upgrade=False,
            with_pip=True,
        )
        builder.create(tempdir)

        # install a known abandoned package into the env
        subprocess.run(
            [Path(tempdir) / "bin" / "pip", "install", "commonmark"],
            capture_output=True,
        )

        site_packages = Path(tempdir) / "lib" / get_python_version() / "site-packages"
        result = subprocess.run(
            ["pip-abandoned", "search", site_packages], capture_output=True
        )
        assert (
            b"Packages associated with archived GitHub repos were found:"
            in result.stdout
        )
        assert result.returncode == 9
