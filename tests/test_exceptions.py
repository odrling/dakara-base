from unittest import TestCase

from dakara_base.exceptions import DakaraError, generate_exception_handler


class GenerateExceptionHandleTestCase(TestCase):
    def test_handler(self):
        """Test to generate and use an exception handler"""
        handler = generate_exception_handler(DakaraError, "handler message")

        with self.assertRaisesRegex(DakaraError, r"initial message\nhandler message"):
            with handler():
                raise DakaraError("initial message")
