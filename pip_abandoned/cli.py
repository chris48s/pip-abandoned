import argparse

from . import lib
from .__version__ import __version__


def cli():
    parser = argparse.ArgumentParser(
        description="Search for abandoned and deprecated python packages"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    subparsers = parser.add_subparsers(
        required=True, dest="subcommand", title="subcommands"
    )

    search = subparsers.add_parser(
        "search", help="Search for abandoned and deprecated python packages"
    )
    search.add_argument(
        "path",
        type=str,
        help="Path to a virtualenv to search",
    )
    search.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase output verbosity",
    )
    search.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    set_token = subparsers.add_parser(  # noqa: F841
        "set-token", help="Set a GitHub API token"
    )

    args = parser.parse_args()

    if args.subcommand == "search":
        return lib.search(lib.get_token(), args.path, args.verbose, args.format)
    elif args.subcommand == "set-token":
        return lib.set_token()
    else:
        parser.print_help()
        return 0
