# Dakara Base

<!-- Badges are displayed for the develop branch -->
[![Travis CI Build Status](https://travis-ci.com/DakaraProject/dakara-base.svg?branch=develop)](https://travis-ci.com/DakaraProject/dakara-base)
[![Appveyor Build status](https://ci.appveyor.com/api/projects/status/50fay6bhsgxispcw/branch/develop?svg=true)](https://ci.appveyor.com/project/neraste/dakara-base/branch/develop)
[![Codecov coverage analysis](https://codecov.io/gh/DakaraProject/dakara-base/branch/develop/graph/badge.svg)](https://codecov.io/gh/DakaraProject/dakara-base)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![PyPI version](https://badge.fury.io/py/dakarabase.svg)](https://pypi.python.org/pypi/dakarabase/)
[![PyPI Python versions](https://img.shields.io/pypi/pyversions/dakarabase.svg)](https://pypi.python.org/pypi/dakarabase/)

This project is a collection of tools and helper modules for the Dakara Project.

## Modules available

* `config`: a configuration helper that can load an YAML file and manage loggers;
* `exceptions`: a base class for exceptions;
* `http_client`: an HTTP client dedicated to be used with an API;
* `progress_bar`: a collection of progress bars;
* `safe_workers`: a library to facilitate the manipulation of threads;
* `utils`: other various helpers;
* `websocket_client`: a Websocket client.

## Install

Install the package with:

```sh
pip install dakarabase
```

If you have downloaded the repo, you can install the package directly with:

```sh
python setup.py install
```

## Developpment

### Install dependencies

Please ensure you have a recent enough version of `setuptools`:

```sh
pip install --upgrade "setuptools>=40.0"
```

Install the dependencies with:

```sh
pip install -e ".[tests]"
```

This installs the normal dependencies of the package plus the dependencies for tests.

### Run tests

Run tests simply with:

```sh
python setup.py test
```

To check coverage, use the `coverage` command:

```sh
coverage run setup.py test
coverage report -m
```

### Hooks

Git hooks are included in the `hooks` directory.

Use the following command to use this hook folder for the project:

```
git config core.hooksPath hooks
```

If you're using git < 2.9 you can make a symlink instead:

```
ln -s -f ../../hooks/pre-commit .git/hooks/pre-commit
```

### Code style

The code follows the [PEP8](https://www.python.org/dev/peps/pep-0008/) style guide (88 chars per line).
Quality of code is checked with [Flake8](https://pypi.org/project/flake8/).
Style is enforced using [Black](https://github.com/ambv/black).
You need to call Black before committing changes.
You may want to configure your editor to call it automatically.
Additionnal checking can be manually performed with [Pylint](https://www.pylint.org/).
