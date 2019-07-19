"""Resources manager helper module

This module provides some helpers to use the functions of the module
pkg_resources morre efficiently. The `resource_listdir` has the same behavior
as in pkg_resources, but it filters special files whose name starts with "__"
(like "__pycache__").

The `get_file` function allows to get any file in the module using a Python
module-like path called requirement. Suppose we have a file in
"resources/art/icon.png", the resource can be accessed with:

>>> get_file("resources.art", "icon.png")
Path("/absolute/path/to/resources/art/icon.png")

The `generate_get_resource` function is a function factory that generates
functions which work like `get_file`, but for a predefined requirement. The
main advantage is that it scans the filesystem only once, not at each call.
Suppose we have the same file in "resources/art/icon.png":

>>> list_arts = resource_listdir("resources.art", "")
>>> get_art = generate_get_resource("resources.art", list_arts, "art")
>>> get_art("icon.png")
Path("/absolute/path/to/resources/art/icon.png")
"""


from pkg_resources import (
    resource_exists,
    resource_filename,
    resource_listdir as resource_listdir_orig,
)

from path import Path

from dakara_base.exceptions import DakaraError


def resource_listdir(*args, **kwargs):
    """List resources without special files

    Args:
        See `pkg_resources.resource_listdir`.

    Returns:
        list: List of filenames.
    """
    return [
        filename
        for filename in resource_listdir_orig(*args, **kwargs)
        if not filename.startswith("__")
    ]


def get_file(resource, filename):
    """Get an arbitrary resource file

    Args:
        resource (str): requirement.
        filename (str): filename or path to the file.

    Returns:
        path.Path: absolute path of the file.

    Raises:
        ResourceNotFoundError: if the file cannot be get.
    """
    if not resource_exists(resource, filename):
        raise ResourceNotFoundError(
            "File '{}' not found within resources".format(filename)
        )

    return Path(resource_filename(resource, filename)).normpath()


def generate_get_resource(resource, resource_list, resource_name):
    """Function factory for resource getter

    Args:
        resource (str): requirement.
        resource_list (list): list of filenames within the requirement.
        resource_name (str): human readable name of the resource.

    Returns:
        function: resource getter.
    """

    def get_resource(filename):
        """Get a resource within the resource files

        Args:
            filename (str): name of the file to get.

        Returns:
            path.Path: absolute path of the file.

        Raises:
            ResourceNotFoundError: if the resource cannot be get.
        """
        if filename not in resource_list:
            raise ResourceNotFoundError(
                "{} file '{}' not found within resources".format(
                    resource_name.capitalize(), filename
                )
            )

        return Path(resource_filename(resource, filename)).normpath()

    return get_resource


class ResourceNotFoundError(DakaraError):
    """Error raised when a resource can not be found.
    """
