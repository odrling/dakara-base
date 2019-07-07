from unittest import TestCase

from dakara_base.utils import display_message


class DisplayMessageTestCase(TestCase):
    """Test the message display helper
    """

    def test_small_message(self):
        """Test a small message is completelly displayed
        """
        message = "few characters"
        message_displayed = display_message(message, limit=50)

        self.assertLessEqual(len(message_displayed), 50)
        self.assertEqual(message_displayed, "few characters")

    def test_long_message(self):
        """Test a long message is cut
        """
        message = "few characters"
        message_displayed = display_message(message, limit=5)

        self.assertLessEqual(len(message_displayed), 5)
        self.assertEqual(message_displayed, "fe...")
