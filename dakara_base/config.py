import logging

import coloredlogs
import yaml

from dakara_base.exceptions import DakaraError


LOG_FORMAT = "[%(asctime)s] %(name)s %(levelname)s %(message)s"
LOG_LEVEL = "INFO"


logger = logging.getLogger(__name__)


def load_config(config_path, debug, mandatory_keys=None):
    """Load config from given config file

    Args:
        config_path (path.Path): path to the config file.
        debug (bool): run in debug mode.
        mandatory_keys (list): list of keys that must be present at the root
            node of the config.

    Returns:
        dict: dictionary of the config.

    Raises:
        ConfigError: if the config file cannot be open, cannot be parsed or
        misses critical sections.
    """
    logger.info("Loading config file '{}'".format(config_path))

    # load and parse the file
    try:
        with config_path.open() as file:
            try:
                config = yaml.load(file, Loader=yaml.Loader)

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


def create_logger():
    """Create logger
    """
    coloredlogs.install(fmt=LOG_FORMAT, level=LOG_LEVEL)


def set_loglevel(config):
    """Set logger level

    Arguments:
        config (dict): dictionary of the config containing at least the
            `loglevel` key.
    """
    loglevel = config.get("loglevel", LOG_LEVEL)
    coloredlogs.set_level(loglevel)


class ConfigError(DakaraError):
    """Error raised for invalid configuration file
    """


class ConfigNotFoundError(ConfigError):
    """Unable to read configuration file
    """


class ConfigParseError(ConfigError):
    """Unable to parse config file
    """


class ConfigInvalidError(ConfigError):
    """Config has missing mandatory keys
    """
