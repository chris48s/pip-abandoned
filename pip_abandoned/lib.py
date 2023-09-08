import json
import logging
import sys
from urllib.parse import urlparse, urlunparse

import requests
from rich import print_json
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

if sys.version_info < (3, 10):
    from importlib_metadata import Prepared, distributions
else:
    from importlib.metadata import Prepared, distributions

logging.basicConfig(
    format="%(message)s",
    handlers=[RichHandler(show_time=False, console=Console(stderr=True))],
)
logger = logging.getLogger(__name__)

console = Console()


def set_log_level(verbosity):
    if verbosity == 0:
        logger.setLevel(logging.ERROR)
    elif verbosity == 1:
        logger.setLevel(logging.WARNING)
    elif verbosity == 2:
        logger.setLevel(logging.INFO)
    elif verbosity >= 3:
        logger.setLevel(logging.DEBUG)


def github_repo_url_or_none(url):
    if url:
        parsed_url = urlparse(url)
        path_parts = [part for part in parsed_url.path.split("/") if part]
        if parsed_url.netloc == "github.com" and len(path_parts) == 2:
            return strip_suffixes(
                urlunparse(
                    (
                        parsed_url.scheme,
                        parsed_url.netloc,
                        parsed_url.path,
                        parsed_url.params,
                        parsed_url.query,
                        "",  # strip fragment (e.g: #readme) if present
                    )
                )
            )
    return None


def strip_suffixes(url):
    if url.endswith(".git"):
        return url[:-4]
    if url.endswith("/"):
        return url[:-1]
    return url


def get_github_repo_url(distribution):
    urls = set()

    if home_page := github_repo_url_or_none(distribution.metadata.get("Home-page")):
        urls.add(home_page)

    if distribution.metadata.get_all("Project-URL"):
        for classifier in distribution.metadata.get_all("Project-URL"):
            try:
                _, url = classifier.split(", ")
                if project_url := github_repo_url_or_none(url):
                    urls.add(project_url)
            except ValueError:
                pass

    urls = list(urls)

    if len(urls) > 1:
        logger.warning(
            f"Found multiple candidate GitHub repo URLs for package {distribution.metadata.get('name')}: {', '.join(urls)}. Skipping"
        )
    if len(urls) == 1:
        return urls[0]
    return None


def get_graphql_query(dist_urls):
    query = "query {\n"
    for dist, repo in dist_urls:
        owner, name = [part for part in urlparse(repo).path.split("/") if part]
        slug = Prepared.normalize(dist.name)
        query += (
            f'  {slug}: repository(owner: "{owner}", name: "{name}") {{ isArchived }}\n'
        )
    query += "}"
    return query


def query_github_api(gh_token, query):
    logger.info(f"Querying GitHub API:\n{query}")

    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": query},
        headers={"Authorization": f"token {gh_token}"},
    )
    resp.raise_for_status()
    body = resp.json()
    logger.info(f"Response from GitHub API:\n{json.dumps(body, indent=2)}")

    if body.get("errors"):
        logger.warning(
            f"Encountered errors calling GitHub API:\n{json.dumps(body['errors'], indent=2)}"
        )

    return body["data"]


def get_archived_packages(dist_urls, api_data):
    archived_packages_normalized_names = [
        k for k, v in api_data.items() if v and v.get("isArchived")
    ]

    return [
        (dist, repo)
        for dist, repo in dist_urls
        if Prepared.normalize(dist.name) in archived_packages_normalized_names
    ]


def is_inactive(distribution):
    classifiers = distribution.metadata.get_all("Classifier", [])
    return "Development Status :: 7 - Inactive" in classifiers


def has_maintained_no_badge(distribution):
    description = distribution.metadata.get("Description", "")
    return "//img.shields.io/maintenance/no" in description


def output_package_repo_table(packages):
    table = Table(show_header=True)

    table.add_column("Package")
    table.add_column("Repo")

    for package, repo in packages:
        table.add_row(package.name, repo)

    console.print(table)


def output_package_table(packages):
    table = Table(show_header=True)

    table.add_column("Package")

    for package in packages:
        table.add_row(package.name)

    console.print(table)


def output_console(inactive, unmaintained, archived):
    console.print("\n")
    if len(inactive) == 0:
        console.print(
            "[green]✔[/] No packages with the trove classifier [bold white]'Development Status :: 7 - Inactive'[/] were found"
        )
    else:
        console.print(
            "[red]✖[/] Packages with the trove classifier [bold white]'Development Status :: 7 - Inactive'[/] were found:"
        )
        output_package_table(inactive)
    console.print("\n")

    if len(unmaintained) == 0:
        console.print(
            "[green]✔[/] No packages with a [white on black bold]\x5Bmaintained[/]|[white on red bold]no][/] badge were found"
        )
    else:
        console.print(
            "[red]✖[/] Packages with a [white on black bold]\x5Bmaintained[/]|[white on red bold]no][/] badge were found:"
        )
        output_package_table(unmaintained)
    console.print("\n")

    if len(archived) == 0:
        console.print(
            "[green]✔[/] No packages associated with archived GitHub repos were found"
        )
    else:
        console.print(
            "[red]✖[/] Packages associated with archived GitHub repos were found:"
        )
        output_package_repo_table(archived)
    console.print("\n")


def output_json(inactive, unmaintained, archived):
    print_json(
        data={
            "inactive": [p.name for p in inactive],
            "unmaintained": [p.name for p in unmaintained],
            "archived": [p.name for p, _ in archived],
        }
    )


def search(gh_token, path, verbosity, format_="text"):
    set_log_level(verbosity)

    dists = list(distributions(path=[path]))
    if len(dists) == 0:
        raise Exception(f"Couldn't find any packages in {path}")

    inactive_packages = [dist for dist in dists if is_inactive(dist)]
    unmaintained_packages = [dist for dist in dists if has_maintained_no_badge(dist)]

    dist_urls = []
    for distribution in dists:
        url = get_github_repo_url(distribution)
        if url:
            dist_urls.append((distribution, url))

    archived_packages = []
    if len(dist_urls) > 0:
        query = get_graphql_query(dist_urls)
        archived_packages = get_archived_packages(
            dist_urls, query_github_api(gh_token, query)
        )

    if format_ == "json":
        output_json(inactive_packages, unmaintained_packages, archived_packages)
    else:
        output_console(inactive_packages, unmaintained_packages, archived_packages)

    if (
        len(inactive_packages) == 0
        and len(unmaintained_packages) == 0
        and len(archived_packages) == 0
    ):
        return 0
    return 1
