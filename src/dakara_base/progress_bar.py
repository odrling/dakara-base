import logging

import progressbar
from progressbar.widgets import WidgetBase


logger = logging.getLogger(__name__)


class ShrinkableTextWidget(WidgetBase):
    """Widget which size auto-shrinks with terminal width

    It contains a descriptive text using by default one quarter of the screen
    width, which can be truncated by the middle if it does not fit.

    Args:
        text (str): text to display on screen.
        ratio (float): ratio of screen width to use for text.
    """

    def __init__(self, text, ratio=0.25):
        assert len(text) > 5, "Text too short"
        self.text = text
        self.ratio = ratio

    def __call__(self, progress, data):
        # set widget width to a fraction of terminal width
        width = int(progress.term_width * self.ratio)

        # truncate text if necessary
        text = self.text
        if len(text) > width:
            half = int(width * 0.5)
            text = text[: half - 2].strip() + "..." + text[-half + 1 :].strip()

        return text.ljust(width)


def progress_bar(*args, text=None, **kwargs):
    """Gives the default un-muted progress bar for the project

    It prints an optionnal shrinkable text, a timer, a progress bar and an ETA.

    Args:
        text (str): text to display describing the current operation.

    Returns:
        generator: progress bar.
    """
    widgets = []

    # add optional text widget
    if text:
        widgets.extend([ShrinkableTextWidget(text), " "])

    # add other widgets
    widgets.extend([progressbar.Timer(), progressbar.Bar(), progressbar.ETA()])

    # create progress bar
    return progressbar.progressbar(*args, widgets=widgets, **kwargs)


def null_bar(*args, text=None, **kwargs):
    """Gives the defaylt muted progress bar for the project

    It only logs the optionnal text.

    Args:
        text (str): text to log describing the current operation.

    Returns:
        progressbar.bar.NullBar: null progress bar that does not do anything.
    """
    # log text immediately
    if text:
        logger.info(text)

    # create null progress bar
    bar = progressbar.NullBar()
    return bar(*args, **kwargs)


def wrap_stderr_for_logging():
    """Wrap the standard error stream for using logging and progress bar
    """
    progressbar.streams.wrap_stderr()
