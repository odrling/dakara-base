"""Exceptions helper module.

This module defines the base exception class for any project using this
library. All exception classes should inherit from `DakaraError`:

>>> class MyError(DakaraError):
...     pass

This helps to differentiate known exceptions and unknown ones, which are real
bugs. On program execution, a try/except structure determines the reason of
interruption of the program:

>>> import logging
>>> debug = False
>>> try:
...     # your program here
... except KeyboardInterrupt:
...     logging.info("Quit by user")
...     exit(255)
... except SystemExit:
...     logging.info("Quit by system")
...     exit(254)
... except DakaraError as error:
...     # known error
...     if debug:
...         # directly re-raise the error in debug mode
...         raise
...     # just log it otherwise
...     logging.critical(error)
...     exit(1)
... except BaseException as error:
...     # unknown error
...     if debug:
...         # directly re-raise the error in debug mode
...         raise
...     # re-raise it and show a special message otherwise
...     logging.exception("Unexpected error: {}".format(error))
...     logging.critical("Please fill a bug report at <url of bugtracker>")
...     exit(128)
>>> exit(0)

It also devifes `generate_exception_handler` that allows to generate functions which
will catch an exception, add a custom error message and re-raise it.
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
