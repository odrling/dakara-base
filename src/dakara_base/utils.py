from furl import furl

from dakara_base.exceptions import DakaraError


def display_message(message, limit=100):
    """Display the 100 first characters of a message
    """
    if len(message) <= limit:
        return message

    return message[: limit - 3].strip() + "..."


def create_url(
    url="",
    address="",
    host="",
    port=None,
    path="",
    ssl=False,
    scheme_no_ssl="",
    scheme_ssl="",
    **kwargs
):
    """Create an URL from arguments

    If `url` is given, the function returns it directly.  If neither `host` nor
    `port` are given, they are extracted from `address` with the `host:port`
    format.  If `ssl` is given and True, `scheme_ssl` is used, otherewise
    `scheme_no_ssl` is used.  If `path` is given, it is appended to the URL.

    Args:
        url (str): direct URL.
        address (str): host, or host and port.
        host (str): host.
        port (str): port.
        path (str): path appended to the URL.
        ssl (bool): use a secured URL or not.
        scheme_no_ssl (str): scheme used if `ssl` is false.
        scheme_ssl (str): scheme used if `ssl` is true.

    Returns:
        str: URL string.
    """
    # setting URL directly
    if url:
        return furl(url).add(path=path).url

    # getting host and port indirectly from address
    if not host:
        # try to separete host and port if they are both given in
        # address key in the form host:port
        try:
            host, port = address.split(":")

        except ValueError:
            host = address

    # getting scheme
    if ssl:
        scheme = scheme_ssl

    else:
        scheme = scheme_no_ssl

    # check mandatory arguments are given
    if not (scheme and host):
        raise URLParameterError(
            "Unable to set mandatory arguments for URL in server config, please check "
            "'url', 'address', 'host', 'port' and/or 'ssl'"
        )

    # combine the arguments
    try:
        return furl(scheme=scheme, host=host, port=port, path=path).url

    except ValueError as error:
        raise URLParameterError(
            "Error when setting URL in server config: {}".format(error)
        ) from error


class URLParameterError(DakaraError, ValueError):
    """Error raised when server parameters are unproperly set
    """
