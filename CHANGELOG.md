# Changelog

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
