from pkg_resources import (
    resource_filename,
    resource_listdir as resource_listdir_orig,
    resource_exists,
)

from path import Path

from dakara_base.exceptions import DakaraError


def resource_listdir(*args, **kwargs):
    """List resources without special files
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
        filename (str): name or path to the file.

    Returns:
        path.Path: absolute path of the file.

    Raises:
        ResourceNotFoundError: if the file cannot be get.
    """
    if not resource_exists(resource, filename):
        raise ResourceNotFoundError(
            "File '{}' not found within resources".format(filename)
        )

    return Path(resource_filename(resource, filename))


def generate_get_resource(resource, resource_list, resource_name):
    """Function factory for resource getter

    Args:
        resource (str): requirement.
        resource_list (list of str): list of files within the requirement.
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

        return Path(resource_filename(resource, filename))

    return get_resource


class ResourceNotFoundError(DakaraError):
    """Error raised when a resource can not be found.
    """
