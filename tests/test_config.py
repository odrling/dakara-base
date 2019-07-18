from unittest import TestCase
from unittest.mock import ANY, patch

from path import Path
from yaml.parser import ParserError

from dakara_base.config import (
    load_config,
    LOG_FORMAT,
    LOG_LEVEL,
    ConfigInvalidError,
    ConfigNotFoundError,
    ConfigParseError,
    create_logger,
    set_loglevel,
)
from dakara_base.resources_manager import get_file


class LoadConfigTestCase(TestCase):
    """Test the `load_config` function
    """

    def setUp(self):
        # create config path
        self.config_path = get_file("tests.resources", "config.yaml")

    def test_success(self):
        """Test to load a config file
        """
        # call the method
        with self.assertLogs("dakara_base.config", "DEBUG") as logger:
            config = load_config(self.config_path, False)

        # assert the result
        self.assertDictEqual(config, {"key": {"subkey": "value"}})

        # assert the effect on logs
        self.assertListEqual(
            logger.output,
            [
                "INFO:dakara_base.config:Loading config file '{}'".format(
                    self.config_path
                )
            ],
        )

    def test_success_debug(self):
        """Test to load the config file with debug mode enabled
        """
        # call the method
        with self.assertLogs("dakara_base.config", "DEBUG"):
            config = load_config(self.config_path, True)

        # assert the result
        self.assertDictEqual(config, {"key": {"subkey": "value"}, "loglevel": "DEBUG"})

    def test_fail_not_found(self):
        """Test to load a not found config file
        """
        # call the method
        with self.assertLogs("dakara_base.config", "DEBUG"):
            with self.assertRaises(ConfigNotFoundError) as error:
                load_config(Path("nowhere"), False)

        # assert the error
        self.assertEqual(str(error.exception), "No config file found")

    @patch("dakara_base.config.yaml.load", autospec=True)
    def test_load_config_fail_parser_error(self, mocked_load):
        """Test to load an invalid config file
        """
        # mock the call to yaml
        mocked_load.side_effect = ParserError("parser error")

        # call the method
        with self.assertLogs("dakara_base.config", "DEBUG"):
            with self.assertRaises(ConfigParseError) as error:
                load_config(self.config_path, False)

        # assert the error
        self.assertEqual(str(error.exception), "Unable to parse config file")

        # assert the call
        mocked_load.assert_called_with(ANY, Loader=ANY)

    def test_load_config_fail_missing_keys(self):
        """Test to load a config file without required keys
        """
        # call the method
        with self.assertLogs("dakara_base.config", "DEBUG"):
            with self.assertRaises(ConfigInvalidError) as error:
                load_config(self.config_path, False, ["not-present"])

        self.assertEqual(
            str(error.exception), "Invalid config file, missing 'not-present'"
        )


class CreateLoggerTestCase(TestCase):
    """Test the `create_logger` function
    """

    @patch("dakara_base.config.coloredlogs.install", autospec=True)
    def test(self, mocked_install):
        """Test to call the method
        """
        # call the method
        create_logger()

        # assert the call
        mocked_install.assert_called_with(fmt=LOG_FORMAT, level=LOG_LEVEL)


class SetLoglevelTestCase(TestCase):
    """Test the `set_loglevel` function
    """

    @patch("dakara_base.config.coloredlogs.set_level", autospec=True)
    def test_configure_logger(self, mocked_set_level):
        """Test to configure the logger
        """
        # call the method
        set_loglevel({"loglevel": "DEBUG"})

        # assert the result
        mocked_set_level.assert_called_with("DEBUG")

    @patch("dakara_base.config.coloredlogs.set_level", autospec=True)
    def test_configure_logger_no_level(self, mocked_set_level):
        """Test to configure the logger with no log level
        """
        # call the method
        set_loglevel({})

        # assert the result
        mocked_set_level.assert_called_with("INFO")
