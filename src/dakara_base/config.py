"""Config helper module.

This module gives a config loader function `load_config` that reads a YAML
config file:

>>> from path import Path
>>> config = load_config(Path("path/to/file.yaml"), debug=True)

The config object will lookup for values in environment variables and in the
config file.

The module has two functions to configure loaders: `create_logger`, which
installs the logger using coloredlogs, and `set_loglevel`, which sets the
loglevel of the logger according to the config. Usually, you call the first one
before reading the config, as `load_config` needs a logger, then call the
latter one:

>>> create_logger()
>>> from path import Path
>>> config = load_config(Path("path/to/file.yaml"), debug=True)
>>> set_loglevel(config)

If you use progress bar and logging at the same time, you should call
`create_logger` with `wrap=True`.

The module has three functions to manage Dakara Project config files. First,
`get_config_directory` gives the configuration directory according to the
operating system. Next, `get_config_file` gives the complete path to the config
file in the configuration directory:

>>> config_path = get_config_file("my_config.yaml")

Then, `create_config` copies a given config file stored in module resources to
the configuration directory:

>>> create_config("module.resources", "my_config.yaml")
"""


import logging
import os
import sys
from collections import UserDict
from distutils.util import strtobool

import coloredlogs
import progressbar
import yaml
from path import Path

try:
    from importlib.resources import path

except ImportError:
    from importlib_resources import path

from dakara_base.exceptions import DakaraError

LOG_FORMAT = "[%(asctime)s] %(name)s %(levelname)s %(message)s"
LOG_LEVEL = "INFO"


logger = logging.getLogger(__name__)


class EnvVarConfig(UserDict):
    """Dictionary with environment variable lookup.

    An instance of this class behaves like a regular dictionnary, with the
    exception that when getting a value, if the requested key exists as an
    environment variable, it is returned instead.

    The looked up variable in environment is prefixed and made upper-case.

    >>> conf = EnvVarConfig("prefix", {"key1": "foo", "key2": "bar"})
    >>> conf
    ... {"key1": "foo", "key2": "bar"}
    >>> conf.get("key1")
    ... "foo"
    >>> # let's say PREFIX_KEY2 is an environment variable with value "spam"
    >>> conf.get("key2")
    ... "spam"

    Values of nested EnvVarConfig objects will have accumulated prefixes:

    >>> conf = EnvVarConfig("prefix", {"sub": {"key": "foo"}})
    >>> # let's say PREFIX_SUB_KEY is an environment variable with value "bar"
    >>> cong.get("sub").get("key")
    ... "bar"

    By default, the value obtained from the environment is a string. If a
    default value is provided to `get`, the returned value from the environment
    will be casted to the type of the default value:

    >>> conf = EnvVarConfig("prefix", {"key": 42})
    >>> # let's say PREFIX_KEY is an environment variable with value "39"
    >>> conf.get("key")
    ... "39"
    >>> cong.get("key", 0)
    ... 39

    Args:
        prefix (str): Prefix to use when looking for value in environment
            variables.
        iterable (iterable): Values to store.
    """

    def __init__(self, prefix, iterable=None):
        self.prefix = prefix

        if iterable:
            # recursively convert dictionaries into EnvVarConfig objects
            iterable = {
                key: (
                    EnvVarConfig("{}_{}".format(self.prefix, key), val)
                    if isinstance(val, dict)
                    else val
                )
                for key, val in iterable.items()
            }

        # create values in object
        super().__init__(iterable)

    def get_value_from_env(self, key):
        """Get the value from prefixed upper case environment variable.

        Args:
            key (str): Name of the variable without prefix.

        Returns:
            str: Value from environment variable or None if not found.
        """
        return os.environ.get("{}_{}".format(self.prefix.upper(), key.upper()))

    def __getitem__(self, key):
        # try to get value from environment
        value_from_env = self.get_value_from_env(key)
        if value_from_env is not None:
            return value_from_env

        return super().__getitem__(key)

    def get(self, key, default=None):
        """Return the value for key.

        If a default value is provided, it will determine the class of the
        returned value when getting it from the environment variables.

        Args:
            key (any): Key to retreive.
            default (any): Default value if the key cannot be found.

        Returns:
            any: Value. If `default` was provided, it will be of the same type.
        """
        # guess cast from default value
        cast = str
        if default is not None:
            cast = type(default)

        # adapt casting function if necessary
        if cast is bool:
            cast = strtobool

        # try to get value from environment and cast it
        value_from_env = self.get_value_from_env(key)
        if value_from_env is not None:
            return cast(value_from_env)

        return super().get(key, default)


def load_config(config_path, debug, mandatory_keys=None):
    """Load config from given YAML file.

    Args:
        config_path (path.Path): Path to the config file.
        debug (bool): Run in debug mode. This creates or overwrites the
            `loglovel` key of the config to "DEBUG".
        mandatory_keys (list): List of keys that must be present at the root
            level of the config.

    Returns:
        dict: Dictionary of the config.

    Raises:
        ConfigNotFoundError: If the config file cannot be open.
        ConfigParseError: If the config cannot be parsed.
        ConfigInvalidError: If the config misses critical sections.
    """
    logger.info("Loading config file '%s'", config_path)

    # load and parse the file
    try:
        with config_path.open() as file:
            try:
                config = EnvVarConfig("DAKARA", yaml.load(file, Loader=yaml.Loader))

            except yaml.parser.ParserError as error:
                raise ConfigParseError("Unable to parse config file") from error

    except FileNotFoundError as error:
        raise ConfigNotFoundError("No config file found") from error

    # if requested check file content
    if mandatory_keys:
        for key in mandatory_keys:
            if key not in config:
                raise ConfigInvalidError(
                    "Invalid config file, missing '{}'".format(key)
                )

    # if debug is set as argument, override the config
    if debug:
        config["loglevel"] = "DEBUG"

    return config


def create_logger(wrap=False, custom_log_format=None, custom_log_level=None):
    """Create logger.

    Args:
        wrap (bool): If True, wrap the standard error stream for using logging
            and progress bar. You have to enable this flag if you use
            `progress_bar`.
        custom_log_format (str): Custom format string to use for logs.
        custom_log_level (str): Custom level of logging.
    """
    # wrap stderr on demand
    if wrap:
        progressbar.streams.wrap_stderr()

    # setup loggers
    log_format = custom_log_format or LOG_FORMAT
    log_level = custom_log_level or LOG_LEVEL
    coloredlogs.install(fmt=log_format, level=log_level)


def set_loglevel(config):
    """Set logger level.

    Arguments:
        config (dict): Dictionary of the config.
    """
    loglevel = config.get("loglevel", LOG_LEVEL)
    coloredlogs.set_level(loglevel)


def get_config_directory():
    """Returns the Dakara config directory to use for the current OS.

    Returns:
        path.Path: Path of the Dakara config directory. Value is not expanded,
        so you have to call `.expand()` on the return value.
    """
    if "linux" in sys.platform:
        return Path("~") / ".config" / "dakara"

    if "win" in sys.platform:
        return Path("$APPDATA") / "Dakara"

    raise NotImplementedError(
        "This operating system ({}) is not currently supported".format(sys.platform)
    )


def create_config_file(resource, filename, force=False):
    """Create a new config file in user directory.

    Args:
        resource (str): Resource where to find the config file.
        filename (str): Name of the config file.
        force (bool): If True, config file in user directory is overwritten if
            it existed already. Otherwise, prompt the user.
    """
    with path(resource, filename) as file:
        # get the file
        origin = Path(file)
        destination = get_config_file(filename)

        # create directory
        destination.dirname().mkdir_p()

        # check destination does not exist
        if not force and destination.exists():
            try:
                result = strtobool(
                    input("{} already exists, overwrite? [y/N] ".format(destination))
                )

            except ValueError:
                result = False

            if not result:
                return

        # copy file
        origin.copyfile(destination)
        logger.info("Config created in '{}'".format(destination))


def get_config_file(filename):
    """Get path of the config in user directory.

    It does not check if the file exists.

    Args:
        filename (str): Name of the config file.

    Returns:
        path.Path: Path to the config file.
    """
    directory = get_config_directory().expand()
    return directory / filename


class ConfigError(DakaraError):
    """Generic error raised for invalid configuration file."""


class ConfigNotFoundError(ConfigError):
    """Unable to read configuration file."""


class ConfigParseError(ConfigError):
    """Unable to parse config file."""


class ConfigInvalidError(ConfigError):
    """Config has missing mandatory keys."""
