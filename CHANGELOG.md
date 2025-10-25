# Changelog

## 📦 0.5.0

* Drop compatibility with python <3.10
* Tested on python 3.14

## 📦 0.4.1

* Bugfix: Ensure GraphQL aliases are valid
* Query GitHub API in batches of 200 repos at a time

## 📦 0.4.0

* Add ability to search a requirements file.
  It is now possible to invoke `pip-abandoned search -r requirements.txt`

## 📦 0.3.2

* Tested on python 3.12

## 📦 0.3.0

* **Breaking:** Add sub-commands.
  This changes the search command from `pip-abandoned <path>` to `pip-abandoned search <path>`
* **Breaking:** The exit code if one or more abandoned packages are found is now `9`
* Add `set-token` command, allowing GitHub token to be stored in the system keyring
* Add `--version` flag

## 📦 0.2.0

* Search for packages with a `[maintained|no]` badge in the README
* Add JSON output via `--format json`
* Improve code for normalizing minor variations of the same GitHub repo URL

## 📦 0.1.0

* First release
