import json
import logging

from websocket import (
    WebSocketApp,
    WebSocketBadStatusException,
    WebSocketConnectionClosedException,
)

from dakara_base.exceptions import DakaraError
from dakara_base.safe_workers import safe, WorkerSafeTimer
from dakara_base.utils import display_message, create_url


logger = logging.getLogger(__name__)


RECONNECT_INTERVAL = 5


def connected(fun):
    """Decorator that ensures the websocket is set

    It makes sure that the given function is callel once connected.

    Args:
        fun (function): function to decorate.

    Returns:
        function: decorated function.
    """

    def call(self, *args, **kwargs):
        if self.websocket is None:
            raise NotConnectedError("No connection established")

        return fun(self, *args, **kwargs)

    return call


class WebSocketClient(WorkerSafeTimer):
    """Object representing the WebSocket connection with the Dakara server

    Args:
        config (dict): configuration for the server, the same as
            DakaraServerHTTPConnection.
        header (dict): header containing the authentication token.
    """

    def init_worker(self, config, route="", header={}):
        # url
        self.server_url = create_url(
            **config, path=route, scheme_no_ssl="ws", scheme_ssl="wss"
        )

        # other
        self.header = header
        self.websocket = None
        self.retry = False
        self.reconnect_interval = config.get("reconnect_interval", RECONNECT_INTERVAL)

        # create callbacks
        self.callbacks = {}
        self.set_default_callbacks()

        # create timer
        self.timer = self.create_timer(0, self.run)

    def set_default_callbacks(self):
        """Stub for creating callbacks

        The method is automatically called at initialization.
        """

    def exit_worker(self, *args, **kwargs):
        logger.debug("Aborting websocket connection")
        self.abort()

    def set_callback(self, name, callback):
        """Assign an arbitrary callback

        Callback is added to the `callbacks` dictionary.

        Args:
            name (str): name of the callback in the `callbacks` attribute.
            callback (function): function to assign.
        """
        self.callbacks[name] = callback

    @safe
    def on_open(self):
        """Callback when the connection is open
        """
        logger.info("Websocket connected to server")
        self.retry = False
        self.on_connected()

    @safe
    def on_close(self, code, reason):
        """Callback when the connection is closed

        If the disconnection is not due to the end of the program, consider the
        connection has been lost. In that case, a reconnection will be
        attempted within several seconds.

        Args:
            code (int): error code (often None).
            reason (str): reason of the closed connection (often None).
        """
        if code or reason:
            logger.debug("Code %i: %s", code, reason)

        # destroy websocket object
        self.websocket = None

        if self.stop.is_set():
            logger.info("Websocket disconnected from server")
            return

        if not self.retry:
            logger.error("Websocket connection lost")

        self.retry = True
        self.on_connection_lost()

        # attempt to reconnect
        logger.warning("Trying to reconnect in %i s", self.reconnect_interval)
        self.timer = self.create_timer(self.reconnect_interval, self.run)
        self.timer.start()

    @safe
    def on_message(self, message):
        """Callback when a message is received

        It will call the method which name corresponds to the event type, if
        possible.

        Args:
            message (str): a JSON text of the event.
        """
        # convert the message to an event object
        try:
            event = json.loads(message)

        # if the message is not in JSON format, assume this is an error
        except json.JSONDecodeError:
            logger.error(
                "Unexpected message from the server: '%s'", display_message(message)
            )
            return

        # attempt to call the corresponding method
        method_name = "receive_{}".format(event["type"])
        if not hasattr(self, method_name):
            logger.error("Event of unknown type received '%s'", event["type"])
            return

        getattr(self, method_name)(event.get("data"))

    @safe
    def on_error(self, error):
        """Callback when an error occurs

        Args:
            error (BaseException): class of the error.
        """
        # do not analyze error on program exit, as it will mistake the
        # WebSocketConnectionClosedException raised by invoking `abort` for a
        # server connection closed error
        if self.stop.is_set():
            return

        # the connection was refused
        if isinstance(error, WebSocketBadStatusException):
            raise AuthenticationError(
                "Unable to connect to server with this user"
            ) from error

        # the server is unreachable
        if isinstance(error, ConnectionRefusedError):
            if self.retry:
                logger.warning("Unable to talk to the server")
                return

            raise NetworkError("Network error, unable to talk to the server") from error

        # the requested endpoint does not exist
        if isinstance(error, ConnectionResetError):
            raise ParameterError("Invalid endpoint to the server") from error

        # connection closed by the server (see beginning of the method)
        if isinstance(error, WebSocketConnectionClosedException):
            # this case is handled by the on_close method
            return

        # other unlisted reason
        logger.error("Websocket: %s", str(error))

    def on_connected(self):
        """Custom callback when the connection is established with the server

        This method is a stub that can be overloaded.
        """

    def on_connection_lost(self):
        """Custom callback when the connection is lost with the server

        This method is a stub that can be overloaded.
        """

    @connected
    def send(self, message_type, data=None, *args, **kwargs):
        """Send data to the server

        Convert it to JSON string before sending.

        Args:
            message_type (str): type of the message.
            data (any): serializable data to send.
            Other arguments are passed to `websocket.WebSocketApp.send`.
        """
        # add type to the content
        content = {"type": message_type}

        # add data to the content if any
        if data:
            content["data"] = data

        return self.websocket.send(json.dumps(content), *args, **kwargs)

    def abort(self):
        """Request to interrupt the connection

        Can be called from anywhere. It will raise an
        `WebSocketConnectionClosedException` which will be passed to
        `on_error`.
        """
        self.retry = False

        # if the connection is lost, the `sock` object may not have the `abort`
        # method
        if self.websocket is not None and hasattr(self.websocket.sock, "abort"):
            self.websocket.sock.abort()

    def run(self):
        """Event loop

        Create the websocket connection and wait events from it. The method can
        be interrupted with the `abort` method.

        The WebSocketApp class is a genki: it will never complaint of anything.
        Wether it is unable to create a connection or its connection is lost,
        the `run_forever` method ends without any exception or non-None return
        value. Exceptions are handled by the yandere `on_error` callback.
        """
        logger.debug("Preparing websocket connection")
        self.websocket = WebSocketApp(
            self.server_url,
            header=self.header,
            on_open=lambda ws: self.on_open(),
            on_close=lambda ws, code, reason: self.on_close(code, reason),
            on_message=lambda ws, message: self.on_message(message),
            on_error=lambda ws, error: self.on_error(error),
        )
        self.websocket.run_forever()


class NotConnectedError(DakaraError):
    """Error raised when connection is missing
    """


class AuthenticationError(DakaraError):
    """Error raised when authentication fails
    """


class ParameterError(DakaraError, ValueError):
    """Error raised when server parameters are unproperly set
    """


class NetworkError(DakaraError):
    """Error raised when unable to communicate with the server
    """
