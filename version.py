import argparse
import sys

import tomlkit


def get_parser():
    parser = argparse.ArgumentParser(
        description="Manage version in pyproject.toml",
    )
    subparsers = parser.add_subparsers(
        required=True, dest="subcommand", title="subcommands"
    )
    subparsers.add_parser("show", help="Show current version")
    bump = subparsers.add_parser("bump", help="Bump version")
    bump.add_argument("version", help="new version")
    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    with open("./pyproject.toml", "r") as f:
        data = tomlkit.load(f)

    if args.subcommand == "show":
        print(data["project"]["version"])
    elif args.subcommand == "bump":
        data["project"]["version"] = args.version
        with open("./pyproject.toml", "w") as f:
            tomlkit.dump(data, f)
    else:
        parser.print_help()

    sys.exit(0)
