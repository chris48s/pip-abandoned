# pip-abandoned

[![Run tests](https://github.com/chris48s/pip-abandoned/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/chris48s/pip-abandoned/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/chris48s/pip-abandoned/graph/badge.svg?token=3TSCfIKLiy)](https://codecov.io/gh/chris48s/pip-abandoned)
[![PyPI Version](https://img.shields.io/pypi/v/pip-abandoned.svg)](https://pypi.org/project/pip-abandoned/)
![License](https://img.shields.io/pypi/l/pip-abandoned.svg)
![Python Compatibility](https://img.shields.io/badge/dynamic/json?query=info.requires_python&label=python&url=https%3A%2F%2Fpypi.org%2Fpypi%2Fpip-abandoned%2Fjson)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)



## Installation

I recommend installing `pip-abandoned` with [pipx](https://pypa.github.io/pipx/). This will give you a system-wide install of `pip-abandoned` with its dependencies isolated from any environments you intend to scan.

Alternatively `pip-abandoned` can be installed from PyPI with your package manager of choice: pip, poetry, pipenv, etc.

## Introduction

Some package registries like NPM and Packagist allow a user to mark a package as abandoned or deprecated. This means it is relatively easy to tell if you are relying on a package abandoned by its author. It also allows package managers to consume this metadata to provide a warning at install time. PyPI does not have a mechanism to abandon or deprecate a package. There are some signals we can look at though.

- Many packages are linked to a GitHub repository. If that GitHub repository is archived, this is a strong signal that the package itself is abandoned
- Some packages may use the `Development Status :: 7 - Inactive` trove classifier to indicate the package is not actively maintained
- Some packages may include a ![not maintained](https://img.shields.io/maintenance/no/2023) badge in the project README to indicate the package is not actively maintained

`pip-abandoned` uses these signals to identify potentially abandoned packages in your environment.

## Usage

An example invocation of `pip-abandoned` looks like:

```bash
GH_TOKEN=ghp_abc123 pip-abandoned /home/alice/.virtualenvs/myproject/lib/python3.10/site-packages
```

There are two things we need to supply:

- A path to a python (virtual) environment to search. This is passed as a positional parameter.
- A GitHub API token. This is set using an environment variable called `GH_TOKEN`. We need to provide this because `pip-abandoned` used the GitHub GraphQL API to efficiently query many repos at once. The advantage of this is that it is fast. The tradeoff is that authentication is required. A PAT with read-only access to public repos will be sufficient for most cases.

## Inspiration

`pip-abandoned` takes inspiration from [pip-audit](https://github.com/pypa/pip-audit), another great project.
