import json
import logging
import sys
from urllib.parse import urlparse

import requests
from rich.console import Console
from rich.table import Table

if sys.version_info < (3, 10):
    from importlib_metadata import Prepared, distributions
else:
    from importlib.metadata import Prepared, distributions

logging.basicConfig(format="%(levelname)s: %(message)s")
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
            return url
    return None


def get_github_repo_url(distribution):
    urls = []

    urls.append(github_repo_url_or_none(distribution.metadata.get("Home-page")))

    if distribution.metadata.get_all("Project-URL"):
        for classifier in distribution.metadata.get_all("Project-URL"):
            try:
                _, url = classifier.split(", ")
                urls.append(github_repo_url_or_none(url))
            except ValueError:
                pass

    urls = [u for u in urls if u]  # strip Nones
    urls = list(set(urls))  # De-dupe

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
    logger.info(f"Querying GitHub API: {query}")

    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": query},
        headers={"Authorization": f"token {gh_token}"},
    )
    resp.raise_for_status()
    body = resp.json()
    logger.info(f"Response from GitHub API: {json.dumps(body, indent=2)}")

    if body.get("errors"):
        logger.warning(
            f"Encountered errors calling GitHub API: {json.dumps(body['errors'], indent=2)}"
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
    classifiers = distribution.metadata.get_all("Classifier") or []
    return "Development Status :: 7 - Inactive" in classifiers


def output_archived_table(packages):
    table = Table(show_header=True)

    table.add_column("Package")
    table.add_column("Repo")

    for package, repo in packages:
        table.add_row(package.name, repo)

    console.print(table)


def output_inactive_table(packages):
    table = Table(show_header=True)

    table.add_column("Package")

    for package in packages:
        table.add_row(package.name)

    console.print(table)


def search(gh_token, path, verbosity):
    set_log_level(verbosity)

    dists = list(distributions(path=[path]))
    if len(dists) == 0:
        raise Exception(f"Couldn't find any packages in {path}")

    inactive_packages = [dist for dist in dists if is_inactive(dist)]

    dist_urls = []
    for distribution in dists:
        url = get_github_repo_url(distribution)
        if url:
            dist_urls.append((distribution, url))

    if len(dist_urls) > 0:
        query = get_graphql_query(dist_urls)
        archived_packages = get_archived_packages(
            dist_urls, query_github_api(gh_token, query)
        )
    else:
        archived_packages = []

    if len(inactive_packages) == 0:
        console.print(
            "No packages with the trove classifier 'Development Status :: 7 - Inactive' were found",
            style="bold",
        )
    else:
        console.print(
            "Packages with the trove classifier 'Development Status :: 7 - Inactive' were found:",
            style="bold",
        )
        output_inactive_table(inactive_packages)

    if len(archived_packages) == 0:
        console.print(
            "No packages associated with archived GitHub repos were found", style="bold"
        )
    else:
        console.print(
            "Packages associated with archived GitHub repos were found:", style="bold"
        )
        output_archived_table(archived_packages)

    if len(inactive_packages) == 0 and len(archived_packages) == 0:
        return 0
    return 1
