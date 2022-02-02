"""Exceptions helper module.

This module defines the base exception class for any project using this
library. All exception classes should inherit from `DakaraError`:

>>> class MyError(DakaraError):
...     pass

This helps to differentiate known exceptions and unknown ones, which are real
bugs.

It defines `generate_exception_handler` that allows to generate functions which
will catch an exception, add a custom error message and re-raise it. It also
defines `handle_all_exceptions` that can be used on `__main__` module to catch
all program executions.
"""

import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DakaraError(Exception):
    """Basic exception class for the project."""


def generate_exception_handler(exception_class, error_message):
    """Generate a context manager to take care of given exception.

    It will add a custom message to an expected exception class. The exception
    is then re-raised.

    >>> class MyError(Exception):
    ...     pass
    >>> handle_my_error = generate_exception_handler(MyError, "extra message")
    >>> try:
    ...     with handle_my_error():
    ...         raise MyError("initial message")
    ... except MyError as error:
    ...     pass
    >>> assert str(error) == "initial message\nextra message"

    Args:
        exception_class (Exception or list of Exception): Exception class to
            catch.
        error_message (str): Error message to display. It will be displayed on
            the next line after the exception message.
    """

    @contextmanager
    def function():
        try:
            yield None

        except exception_class as error:
            raise error.__class__("{}\n{}".format(error, error_message)) from error

    return function


class ExitValue:
    """Container for the exit value."""

    def __init__(self):
        self.value = 0


@contextmanager
def handle_all_exceptions(bugtracker_url, logger=logger, debug=False):
    """Handle all exceptions and yield a return value.

    >>> with handle_all_exceptions(
    ...    "https://www.example.com/bugtracker"
    ... ) as exit_value:
    ...    # your program here
    >>> exit(exit_value.value)

    Args:
        bugtracker_url (str): URL address of the bugtracker, displayed on
            unexpected exceptions.
        logger (logging.Logger): Logger. If not given, will take the current
            module's logger.
        debug (bool): If True, known and unknown exceptions will be directly
            raised.

    Yield:
        ExitValue: Container with the return value, stored in attribute
        "value". If no error happened, the return value is 0, in case of
        Ctrl+C, it is 255, in case of a known error, it is 1, in case of an
        unknown error, it is 2.
    """
    container = ExitValue()

    try:
        yield container

    except KeyboardInterrupt:
        container.value = 255
        logger.info("Quit by user")

    except DakaraError as error:
        container.value = 1

        # directly re-raise the error in debug mode
        if debug:
            raise

        # just log it otherwise
        logger.critical(error)

    except BaseException as error:
        container.value = 2

        # directly re-raise the error in debug mode
        if debug:
            raise

        # re-raise it and show a special message otherwise
        logger.exception("Unexpected error: {}".format(error))
        logger.critical("Please fill a bug report at '{}'".format(bugtracker_url))
