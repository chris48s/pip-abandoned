import argparse
import textwrap
from pathlib import Path

from . import lib
from .__version__ import __version__


def get_parser():
    parser = argparse.ArgumentParser(
        description="Search for abandoned and deprecated python packages",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    subparsers = parser.add_subparsers(
        required=True, dest="subcommand", title="subcommands"
    )

    search = subparsers.add_parser(
        "search",
        help="Search for abandoned and deprecated python packages",
        epilog=textwrap.dedent(
            """\
            Examples:
            pip-abandoned search myproject/lib/python3.10/site-packages
            pip-abandoned search -r requirements.txt
        """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    dep_source_args = search.add_mutually_exclusive_group()
    dep_source_args.add_argument(
        "path",
        type=Path,
        nargs="?",
        help="Path to a virtualenv to search",
    )
    dep_source_args.add_argument(
        "-r",
        "--requirement",
        type=argparse.FileType("r"),
        metavar="REQUIREMENT",
        action="append",
        dest="requirements",
        help="Install packages from the given requirements file into a temporary virtualenv. Then search that virtualenv. This option can be used multiple times.",
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

    return parser


def cli():
    parser = get_parser()

    args = parser.parse_args()

    if args.subcommand == "search" and args.path:
        return lib.search_virtualenv_path(
            lib.get_token(), args.path, args.verbose, args.format
        )
    elif args.subcommand == "search" and args.requirements:
        return lib.search_requirements_files(
            lib.get_token(),
            [Path(req.name) for req in args.requirements],
            args.verbose,
            args.format,
        )
    elif args.subcommand == "set-token":
        return lib.set_token()
    else:
        parser.print_help()
        return 0
