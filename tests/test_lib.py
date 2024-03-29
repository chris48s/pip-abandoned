import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import responses
from rich.console import Console

from pip_abandoned import lib

if sys.version_info < (3, 10):
    from importlib_metadata import Distribution
else:
    from importlib.metadata import Distribution

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
def mock_distributions_readme():
    with patch("pip_abandoned.lib.distributions") as mock:
        mock.return_value = [get_dist_fixture("readme-1.0.0.dist-info")]
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
def mock_all_errors():
    with patch("pip_abandoned.lib.distributions") as mock:
        mock.return_value = [
            get_dist_fixture("inactive-1.0.0.dist-info"),
            get_dist_fixture("home-page-1.0.0.dist-info"),
            get_dist_fixture("readme-1.0.0.dist-info"),
        ]
        yield mock


class TestSearchVirtualenv:
    def test_no_packages(self, mock_distributions_no_packages):
        with pytest.raises(Exception) as exc:
            lib.search_virtualenv_path("fake_token", "/fake/path", 0)
        assert "Couldn't find any packages in /fake/path" in str(exc)

    def test_inactive(self, mock_distributions_inactive):
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search_virtualenv_path("fake_token", "/fake/path", 0)
            stdout = buf.getvalue()

        assert (
            "Packages with the trove classifier 'Development Status :: 7 - Inactive' were found"
            in stdout
        )
        assert "No packages with a [maintained|no] badge were found" in stdout
        assert "No packages associated with archived GitHub repos were found" in stdout
        assert exit_code == 9

    def test_unmaintained_badge(self, mock_distributions_readme):
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search_virtualenv_path("fake_token", "/fake/path", 0)
            stdout = buf.getvalue()

        assert (
            "No packages with the trove classifier 'Development Status :: 7 - Inactive' were found"
            in stdout
        )
        assert "Packages with a [maintained|no] badge were found" in stdout
        assert "No packages associated with archived GitHub repos were found" in stdout
        assert exit_code == 9

    @responses.activate
    def test_home_page_archived(self, mock_distributions_homepage):
        responses.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={"data": {"_home_page": {"isArchived": True}}},
            status=200,
        )
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search_virtualenv_path("fake_token", "/fake/path", 0)
            stdout = buf.getvalue()

        assert (
            "No packages with the trove classifier 'Development Status :: 7 - Inactive' were found"
            in stdout
        )
        assert "No packages with a [maintained|no] badge were found" in stdout
        assert "Packages associated with archived GitHub repos were found:" in stdout
        assert exit_code == 9

    @responses.activate
    def test_home_page_not_archived(self, mock_distributions_homepage):
        responses.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={"data": {"_home_page": {"isArchived": False}}},
            status=200,
        )
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search_virtualenv_path("fake_token", "/fake/path", 0)
            stdout = buf.getvalue()

        assert (
            "No packages with the trove classifier 'Development Status :: 7 - Inactive' were found"
            in stdout
        )
        assert "No packages with a [maintained|no] badge were found" in stdout
        assert "No packages associated with archived GitHub repos were found" in stdout
        assert exit_code == 0

    @responses.activate
    def test_project_urls_archived(self, mock_distributions_project_urls):
        responses.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={"data": {"_project_urls": {"isArchived": True}}},
            status=200,
        )
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search_virtualenv_path("fake_token", "/fake/path", 0)
            stdout = buf.getvalue()

        assert (
            "No packages with the trove classifier 'Development Status :: 7 - Inactive' were found"
            in stdout
        )
        assert "No packages with a [maintained|no] badge were found" in stdout
        assert "Packages associated with archived GitHub repos were found:" in stdout
        assert exit_code == 9

    @responses.activate
    def test_project_urls_not_archived(self, mock_distributions_project_urls):
        responses.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={"data": {"_project_urls": {"isArchived": False}}},
            status=200,
        )
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search_virtualenv_path("fake_token", "/fake/path", 0)
            stdout = buf.getvalue()

        assert (
            "No packages with the trove classifier 'Development Status :: 7 - Inactive' were found"
            in stdout
        )
        assert "No packages with a [maintained|no] badge were found" in stdout
        assert "No packages associated with archived GitHub repos were found" in stdout
        assert exit_code == 0

    @responses.activate
    def test_all_errors(self, mock_all_errors):
        responses.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={"data": {"_home_page": {"isArchived": True}}},
            status=200,
        )
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search_virtualenv_path("fake_token", "/fake/path", 0)
            stdout = buf.getvalue()

        assert (
            "Packages with the trove classifier 'Development Status :: 7 - Inactive' were found"
            in stdout
        )
        assert "Packages with a [maintained|no] badge were found" in stdout
        assert "Packages associated with archived GitHub repos were found:" in stdout
        assert exit_code == 9

    @responses.activate
    def test_json_output(self, mock_all_errors):
        responses.add(
            responses.POST,
            "https://api.github.com/graphql",
            json={"data": {"_home_page": {"isArchived": True}}},
            status=200,
        )
        with StringIO() as buf, redirect_stdout(buf):
            exit_code = lib.search_virtualenv_path(
                "fake_token", "/fake/path", 0, "json"
            )
            stdout = buf.getvalue()

        assert json.loads(stdout) == {
            "inactive": ["inactive"],
            "unmaintained": ["readme"],
            "archived": ["home-page"],
        }
        assert exit_code == 9


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


class TestGitHubRepoOrNull:
    @pytest.mark.parametrize(
        "url",
        [
            "https://github.com/chris48s/does-not-exist",
            "https://github.com/chris48s/does-not-exist/",
            "https://github.com/chris48s/does-not-exist.git",
            "https://github.com/chris48s/does-not-exist#readme",
            "https://github.com/chris48s/does-not-exist/#readme",
        ],
    )
    def test_valid(self, url):
        assert (
            lib.github_repo_url_or_none(url)
            == "https://github.com/chris48s/does-not-exist"
        )

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com",
            "https://github.com/chris48s/does-not-exist/blob/main/README.md",
            "https://chris48s.github.io/does-not-exist",
        ],
    )
    def test_invalid(self, url):
        assert lib.github_repo_url_or_none(url) is None


class TestGetGraphqlQueries:
    @property
    def dist_urls(self):
        return [
            (
                SimpleNamespace(name="Spoon-Knife1"),
                "https://github.com/octocat/Spoon-Knife1",
            ),
            (
                SimpleNamespace(name="Spoon-Knife2"),
                "https://github.com/octocat/Spoon-Knife2",
            ),
            (
                SimpleNamespace(name="Spoon-Knife3"),
                "https://github.com/octocat/Spoon-Knife3",
            ),
            (
                SimpleNamespace(name="Spoon-Knife4"),
                "https://github.com/octocat/Spoon-Knife4",
            ),
            (
                SimpleNamespace(name="Spoon-Knife5"),
                "https://github.com/octocat/Spoon-Knife5",
            ),
        ]

    def test_get_graphql_queries_multiple_pages(self):
        chunk_size = 2  # 2 repos per query
        queries = lib.get_graphql_queries(self.dist_urls, chunk_size)

        assert len(queries) == 3

        assert "_spoon_knife1" in queries[0]
        assert "_spoon_knife1" not in queries[1]
        assert "_spoon_knife1" not in queries[2]

        assert "_spoon_knife2" in queries[0]
        assert "_spoon_knife2" not in queries[1]
        assert "_spoon_knife2" not in queries[2]

        assert "_spoon_knife3" not in queries[0]
        assert "_spoon_knife3" in queries[1]
        assert "_spoon_knife3" not in queries[2]

        assert "_spoon_knife4" not in queries[0]
        assert "_spoon_knife4" in queries[1]
        assert "_spoon_knife4" not in queries[2]

        assert "_spoon_knife5" not in queries[0]
        assert "_spoon_knife5" not in queries[1]
        assert "_spoon_knife5" in queries[2]

    def test_get_graphql_queries_one_page(self):
        queries = lib.get_graphql_queries(self.dist_urls)

        assert len(queries) == 1

        assert "_spoon_knife1" in queries[0]
        assert "_spoon_knife2" in queries[0]
        assert "_spoon_knife3" in queries[0]
        assert "_spoon_knife4" in queries[0]
        assert "_spoon_knife5" in queries[0]


def test_merge_results():
    input_ = [{"a": 1, "b": 2}, {"c": 3, "d": 4}]
    expected = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": 4,
    }
    assert lib.merge_results(input_) == expected
