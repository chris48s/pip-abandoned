import argparse
import os

from .lib import search


def cli():
    parser = argparse.ArgumentParser(
        description="Search for abandoned and deprecated python packages"
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to a virtualenv to search",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase output verbosity",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    args = parser.parse_args()

    gh_token = os.environ.get("GH_TOKEN")
    if not (gh_token):
        raise Exception("GH_TOKEN environment variable must be set")

    return search(gh_token, args.path, args.verbose, args.format)
