import logging
from unittest import TestCase
from unittest.mock import ANY

from dakara_base.exceptions import (
    DakaraError,
    generate_exception_handler,
    handle_all_exceptions,
)


class GenerateExceptionHandleTestCase(TestCase):
    def test_handler(self):
        """Test to generate and use an exception handler"""
        handler = generate_exception_handler(DakaraError, "handler message")

        with self.assertRaisesRegex(DakaraError, r"initial message\nhandler message"):
            with handler():
                raise DakaraError("initial message")


class HandleAllExceptionsTestCase(TestCase):
    def test_normal_exit(self):
        """Test a normal exit."""
        logger = logging.getLogger("normal")
        with handle_all_exceptions(logger, "url") as exit_value:
            pass

        self.assertEqual(exit_value["value"], 0)

    def test_keyboard_interrupt(self):
        """Test a Ctrl+C exit."""
        logger = logging.getLogger("keyboard_interrupt")
        with self.assertLogs("keyboard_interrupt") as log:
            with handle_all_exceptions(logger, "url") as exit_value:
                raise KeyboardInterrupt

        self.assertEqual(exit_value["value"], 255)
        self.assertListEqual(log.output, ["INFO:keyboard_interrupt:Quit by user"])

    def test_known_error(self):
        """Test a known error exit."""
        logger = logging.getLogger("known_error")
        with self.assertLogs("known_error") as log:
            with handle_all_exceptions(logger, "url") as exit_value:
                raise DakaraError("error")

        self.assertEqual(exit_value["value"], 1)
        self.assertListEqual(log.output, ["CRITICAL:known_error:error"])

    def test_known_error_debug(self):
        """Test a known error exit in debug mode."""
        logger = logging.getLogger("known_error")
        with self.assertRaisesRegex(DakaraError, "error"):
            with handle_all_exceptions(logger, "url", True) as exit_value:
                raise DakaraError("error")

        self.assertEqual(exit_value["value"], 1)

    def test_unknown_error(self):
        """Test an unknown error exit."""
        logger = logging.getLogger("unknown_error")
        with self.assertLogs("unknown_error") as log:
            with handle_all_exceptions(logger, "url") as exit_value:
                raise Exception("error")

        self.assertEqual(exit_value["value"], 2)
        self.assertListEqual(
            log.output,
            [ANY, "CRITICAL:unknown_error:Please fill a bug report at 'url'"],
        )

    def test_unknown_error_debug(self):
        """Test an unknown error exit in debug mode."""
        logger = logging.getLogger("known_error")
        with self.assertRaisesRegex(Exception, "error"):
            with handle_all_exceptions(logger, "url", True) as exit_value:
                raise Exception("error")

        self.assertEqual(exit_value["value"], 2)
