import sys

from .__version__ import __version__  # noqa: F401
from .cli import cli


def main():
    sys.exit(cli())


if __name__ == "__main__":
    main()
