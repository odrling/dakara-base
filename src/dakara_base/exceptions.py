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

from contextlib import contextmanager


class DakaraError(Exception):
    """Basic exception class for the project."""


def generate_exception_handler(exception_class, error_message):
    """Generate a context manager to take care of given exception.

    It will add a custom message to an expected exception class. The exception
    is then re-raised.

    >>> class MyError(Exception):
    >>>     pass
    >>> handle_my_error = generate_exception_handler(MyError, "extra message")
    >>> try:
    >>>     with handle_my_error():
    >>>         raise MyError("initial message")
    >>> except MyError as error:
    >>>     pass
    >>> str(error)
    ... "initial message\nextra message"

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


@contextmanager
def handle_all_exceptions(logger, bugtracker_url, debug=False):
    """Handle all exceptions and yield a return value.

    >>> with handle_all_exceptions(
    ...    logging,
    ...    "https://www.example.com/bugtracker"
    ... ) as exit_value:
    ...    # your program here
    >>> exit(exit_value["value"])

    Args:
        logger (logging.Logger): Logger.
        bugtracker_url (str): URL address of the bugtracker, displayed on
            unexpected exceptions.
        debug (bool): If True, known and unknown exceptions will be directly
            raised.

    Yield:
        dict: Container with the return value, stored in key "value".
    """
    container = {"value": 0}

    try:
        yield container

    except KeyboardInterrupt:
        container["value"] = 255
        logger.info("Quit by user")

    except DakaraError as error:
        container["value"] = 1

        # directly re-raise the error in debug mode
        if debug:
            raise

        # just log it otherwise
        logger.critical(error)

    except BaseException as error:
        container["value"] = 2

        # directly re-raise the error in debug mode
        if debug:
            raise

        # re-raise it and show a special message otherwise
        logger.exception("Unexpected error: {}".format(error))
        logger.critical("Please fill a bug report at '{}'".format(bugtracker_url))
