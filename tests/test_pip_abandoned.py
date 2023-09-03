from contextlib import redirect_stdout
from importlib.metadata import Distribution
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
import responses
from rich.console import Console

from pip_abandoned import lib

# Disable Rich formatting so we can more easily make assertions about text output
lib.console = Console(force_terminal=True, _environ={"TERM": "dumb"}, soft_wrap=True)


def get_dist_fixture(name):
    return Distribution.at(Path(".") / "tests" / "fixture_data" / name)


@pytest.fixture
def mock_distributions_no_packages():
    with patch("pip_abandoned.lib.distributions") as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_distributions_inactive():
    with patch("pip_abandoned.lib.distributions") as mock:
        mock.return_value = [get_dist_fixture("inactive-1.0.0.dist-info")]
        yield mock


@pytest.fixture
def mock_distributions_homepage():
    with patch("pip_abandoned.lib.distributions") as mock:
        mock.return_value = [get_dist_fixture("home-page-1.0.0.dist-info")]
        yield mock


@pytest.fixture
def mock_distributions_project_urls():
    with patch("pip_abandoned.lib.distributions") as mock:
        mock.return_value = [get_dist_fixture("project-urls-1.0.0.dist-info")]
        yield mock


@pytest.fixture
def mock_distributions_inactive_and_homepage():
    with patch("pip_abandoned.lib.distributions") as mock:
        mock.return_value = [
            get_dist_fixture("inactive-1.0.0.dist-info"),
            get_dist_fixture("home-page-1.0.0.dist-info"),
        ]
        yield mock


class TestSearch:
    def test_no_packages(self, mock_distributions_no_packages):
        with pytest.raises(Exception) as exc:
            lib.search("fake_token", "/fake/path", 0)
        assert "Couldn't find any packages in /fake/path" in str(exc)

    def test_inactive(self, mock_distributions_inactive):
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search("fake_token", "/fake/path", 0)
            stdout = buf.getvalue()
        assert (
            "Packages with the trove classifier 'Development Status :: 7 - Inactive' were found"
            in stdout
        )
        assert "No packages associated with archived GitHub repos were found" in stdout
        assert exit_code == 1

    @responses.activate
    def test_home_page_archived(self, mock_distributions_homepage):
        responses.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={"data": {"home_page": {"isArchived": True}}},
            status=200,
        )
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search("fake_token", "/fake/path", 0)
            stdout = buf.getvalue()
        assert (
            "No packages with the trove classifier 'Development Status :: 7 - Inactive' were found"
            in stdout
        )
        assert "Packages associated with archived GitHub repos were found:" in stdout
        assert exit_code == 1

    @responses.activate
    def test_home_page_not_archived(self, mock_distributions_homepage):
        responses.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={"data": {"home_page": {"isArchived": False}}},
            status=200,
        )
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search("fake_token", "/fake/path", 0)
            stdout = buf.getvalue()
        assert (
            "No packages with the trove classifier 'Development Status :: 7 - Inactive' were found"
            in stdout
        )
        assert "No packages associated with archived GitHub repos were found" in stdout
        assert exit_code == 0

    @responses.activate
    def test_project_urls_archived(self, mock_distributions_project_urls):
        responses.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={"data": {"project_urls": {"isArchived": True}}},
            status=200,
        )
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search("fake_token", "/fake/path", 0)
            stdout = buf.getvalue()
        assert (
            "No packages with the trove classifier 'Development Status :: 7 - Inactive' were found"
            in stdout
        )
        assert "Packages associated with archived GitHub repos were found:" in stdout
        assert exit_code == 1

    @responses.activate
    def test_project_urls_not_archived(self, mock_distributions_project_urls):
        responses.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={"data": {"project_urls_": {"isArchived": False}}},
            status=200,
        )
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search("fake_token", "/fake/path", 0)
            stdout = buf.getvalue()
        assert (
            "No packages with the trove classifier 'Development Status :: 7 - Inactive' were found"
            in stdout
        )
        assert "No packages associated with archived GitHub repos were found" in stdout
        assert exit_code == 0

    @responses.activate
    def test_inactive_and_archived(self, mock_distributions_inactive_and_homepage):
        responses.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={"data": {"home_page": {"isArchived": True}}},
            status=200,
        )
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search("fake_token", "/fake/path", 0)
            stdout = buf.getvalue()
        assert (
            "Packages with the trove classifier 'Development Status :: 7 - Inactive' were found"
            in stdout
        )
        assert "Packages associated with archived GitHub repos were found:" in stdout
        assert exit_code == 1


class TestGetGitHubRepo:
    def test_no_matches(self):
        dist = get_dist_fixture("inactive-1.0.0.dist-info")
        assert lib.get_github_repo_url(dist) is None

    def test_home_page_match(self):
        dist = get_dist_fixture("home-page-1.0.0.dist-info")
        expected = "https://github.com/chris48s/does-not-exist"
        assert lib.get_github_repo_url(dist) == expected

    def test_project_urls_one_match(self):
        dist = get_dist_fixture("project-urls-1.0.0.dist-info")
        expected = "https://github.com/chris48s/does-not-exist"
        assert lib.get_github_repo_url(dist) == expected

    def test_project_urls_multiple_matches(self):
        dist = get_dist_fixture("multiple-matches-1.0.0.dist-info")
        assert lib.get_github_repo_url(dist) is None
