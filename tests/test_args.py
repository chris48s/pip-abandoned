import pytest

from pip_abandoned.cli import get_parser


def test_virtualenv_path():
    parser = get_parser()
    args = parser.parse_args(["search", "foo/bar"])
    assert str(args.path) == "foo/bar"
    assert args.requirements is None


def test_one_requirements_file():
    parser = get_parser()
    file_ = "./tests/fixture_data/reqs-pass.txt"
    args = parser.parse_args(["search", "-r", file_])
    assert [r.name for r in args.requirements] == [file_]
    assert args.path is None


def test_multiple_requirements_files():
    parser = get_parser()
    file1 = "./tests/fixture_data/reqs-pass.txt"
    file2 = "./tests/fixture_data/reqs-fail.txt"
    args = parser.parse_args(["search", "-r", file1, "-r", file2])
    assert [r.name for r in args.requirements] == [file1, file2]
    assert args.path is None


def test_invalid_combination():
    parser = get_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["search", "-r", "./tests/fixture_data/reqs-pass.txt", "foo/bar"]
        )
