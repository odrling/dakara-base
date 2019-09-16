import logging
from io import StringIO
from unittest import TestCase
from unittest.mock import MagicMock

from dakara_base import progress_bar


class ShrinkablaTextWidgetTestCase(TestCase):
    """Test the widget for shrinkable text
    """

    def test_no_shrink(self):
        """Test a not shrinked case
        """
        # prepare mock objects
        progress = MagicMock()
        progress.term_width = 80
        data = MagicMock()

        # create the widget and update it
        widget = progress_bar.ShrinkableTextWidget("some text here")
        result = widget(progress, data)

        # assert the result
        self.assertEqual(len(result), 20)
        self.assertEqual(result, "some text here      ")

    def test_shrink(self):
        """Test a not shrinked case
        """
        # prepare mock objects
        progress = MagicMock()
        progress.term_width = 40
        data = MagicMock()

        # create the widget and update it
        widget = progress_bar.ShrinkableTextWidget("some text here")
        result = widget(progress, data)

        # assert the result
        self.assertEqual(len(result), 10)
        self.assertEqual(result, "som...here")

    def test_too_short(self):
        """Test a too short case
        """
        # create the widget
        with self.assertRaises(AssertionError) as error:
            progress_bar.ShrinkableTextWidget("some")

        # assert the error
        self.assertEqual(str(error.exception), "Text too short")


class ProgressBarTestCase(TestCase):
    """Test the default progress bar
    """

    @staticmethod
    def get_lines(file):
        """Get a neat list of printed lines from a dummy file descriptor.

        Args:
            file (io.StringIO): Dummy file descriptor that get the output of
                the progress bar. It must not be closed.

        Returns:
            list of str: List of actually printed lines. Blank lines are removed.
        """
        content = file.getvalue()
        lines = content.replace("\r", "\n").splitlines()
        return [line for line in lines if line.strip()]

    def test_text(self):
        """Test a bar with text
        """
        # call the bar
        with StringIO() as file:
            for _ in progress_bar.progress_bar(
                range(1), fd=file, term_width=65, text="some text here"
            ):
                pass

            lines = self.get_lines(file)

        # assert the lines
        self.assertEqual(len(lines), 2)
        self.assertEqual(
            lines,
            [
                "some text here   Elapsed Time: 0:00:00|           |ETA:  --:--:--",
                "some text here   Elapsed Time: 0:00:00|###########|Time:  0:00:00",
            ],
        )

    def test_no_text(self):
        """Test a bar without text
        """
        # call the bar
        with StringIO() as file:
            for _ in progress_bar.progress_bar(range(1), fd=file, term_width=65):
                pass

            lines = self.get_lines(file)

        # assert the lines
        self.assertEqual(len(lines), 2)
        self.assertEqual(
            lines,
            [
                "Elapsed Time: 0:00:00|                            |ETA:  --:--:--",
                "Elapsed Time: 0:00:00|############################|Time:  0:00:00",
            ],
        )


class NullBarTestCase(TestCase):
    """Test the null progress bar
    """

    def setUp(self):
        # create logger similar to the one of the tested module
        self.logger = logging.getLogger("dakara_base.progress_bar")

    def test_text(self):
        """Test a null bar with text
        """
        # call the bar
        with self.assertLogs("dakara_base.progress_bar") as logger:
            self.logger.info("start bar")
            for _ in progress_bar.null_bar(range(1), text="some text here"):
                pass

            self.logger.info("end bar")

        # assert the logs
        self.assertListEqual(
            logger.output,
            [
                "INFO:dakara_base.progress_bar:start bar",
                "INFO:dakara_base.progress_bar:some text here",
                "INFO:dakara_base.progress_bar:end bar",
            ],
        )

    def test_no_text(self):
        """Test a null bar without text
        """
        # call the bar
        with self.assertLogs("dakara_base.progress_bar") as logger:
            self.logger.info("start bar")
            for _ in progress_bar.null_bar(range(1)):
                pass

            self.logger.info("end bar")

        # assert the logs
        self.assertListEqual(
            logger.output,
            [
                "INFO:dakara_base.progress_bar:start bar",
                "INFO:dakara_base.progress_bar:end bar",
            ],
        )
