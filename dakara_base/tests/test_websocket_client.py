from unittest import TestCase
from unittest.mock import patch, MagicMock, ANY
from threading import Event
from queue import Queue

from websocket import WebSocketBadStatusException, WebSocketConnectionClosedException

from dakara_base.websocket_client import (
    connected,
    NotConnectedError,
    WebSocketClient,
    ParameterError,
    AuthenticationError,
    NetworkError,
)


class ConnectedTestCase(TestCase):
    """Test the `connected` decorator
    """

    class Connected:
        def __init__(self):
            self.websocket = None

        @connected
        def dummy(self):
            pass

    def test_connected_sucessful(self):
        """Test the connected decorator when websocket is set

        Use the `run` method for the test.
        """
        instance = self.Connected()

        # set the token
        instance.websocket = True

        # call a protected method
        instance.dummy()

    def test_connected_error(self):
        """Test the connected decorator when token is not set

        Use the interal `get_token_header` method for test.
        """
        instance = self.Connected()

        # call a protected method
        with self.assertRaises(NotConnectedError):
            instance.dummy()


class WebSocketClientTestCase(TestCase):
    """Test the WebSocket connection with the server
    """

    def setUp(self):
        # create a mock websocket
        self.websocket = MagicMock()

        # create a server address
        self.address = "www.example.com"

        # create an URL
        self.url = "ws://www.example.com/ws"

        # create a secured URL
        self.url_secured = "wss://www.example.com/ws"

        # create token header
        self.header = {"token": "token"}

        # create a reconnect interval
        self.reconnect_interval = 1

        # create stop event and errors queue
        self.stop = Event()
        self.errors = Queue()

        # create a DakaraServerWebSocketConnection instance
        self.client = WebSocketClient(
            self.stop,
            self.errors,
            {"url": self.url, "reconnect_interval": self.reconnect_interval},
            header=self.header,
        )

    def set_websocket(self):
        """Set the websocket object to a mock
        """
        self.client.websocket = MagicMock()

    def test_init_worker_url(self):
        """Test the created object with provided URL
        """
        # use the already created client object
        self.assertEqual(self.client.server_url, self.url)
        self.assertEqual(self.client.header, self.header)
        self.assertEqual(self.client.reconnect_interval, self.reconnect_interval)
        self.assertIsNone(self.client.websocket)

    def test_init_worker_address(self):
        """Test to create ojbcet with provided address
        """
        # create a client
        client = WebSocketClient(
            self.stop, self.errors, {"address": self.address}, route="ws"
        )

        # assert the client
        self.assertEqual(client.server_url, self.url)

        # create a secured client
        client_secured = WebSocketClient(
            self.stop, self.errors, {"address": self.address, "ssl": True}, route="ws"
        )

        # assert the client
        self.assertEqual(client_secured.server_url, self.url_secured)

    def test_init_worker_missing_key(self):
        """Test to create object with missing mandatory key
        """
        # try to create a client from invalid config
        with self.assertRaises(ParameterError) as error:
            WebSocketClient(self.stop, self.errors, {}, route="api")

        # assert the error
        self.assertEqual(
            str(error.exception), "Missing parameter in server config: 'address'"
        )

    @patch.object(WebSocketClient, "abort")
    def test_exit_worker(self, mocked_abort):
        """Test to exit the worker
        """
        # call the method
        with self.assertLogs("dakara_base.websocket_client", "DEBUG") as logger:
            self.client.exit_worker()

        # assert the effect on logger
        self.assertListEqual(
            logger.output,
            ["DEBUG:dakara_base.websocket_client:Aborting websocket connection"],
        )

        # assert the call
        mocked_abort.assert_called_with()

    @patch.object(WebSocketClient, "on_connected")
    def test_on_open(self, mocked_on_connected):
        """Test the callback on connection open
        """
        # call the method
        with self.assertLogs("dakara_base.websocket_client", "DEBUG") as logger:
            self.client.on_open()

        # assert the effect
        self.assertFalse(self.client.retry)

        # assert the effect on logger
        self.assertListEqual(
            logger.output,
            ["INFO:dakara_base.websocket_client:Websocket connected to server"],
        )

        # assert the call
        mocked_on_connected.assert_called_with()

    @patch.object(WebSocketClient, "create_timer")
    @patch.object(WebSocketClient, "on_connection_lost")
    def test_on_close_normal(self, mocked_on_connection_lost, mocked_create_timer):
        """Test the callback on connection close when the program is closing
        """
        # create the websocket
        self.set_websocket()

        # pre assert
        self.assertIsNotNone(self.client.websocket)
        self.assertFalse(self.client.retry)

        # set the program is closing
        self.stop.set()

        # call the method
        with self.assertLogs("dakara_base.websocket_client", "DEBUG") as logger:
            self.client.on_close(None, None)

        # assert the websocket object has been destroyed
        self.assertIsNone(self.client.websocket)
        self.assertFalse(self.client.retry)

        # assert the effect on logger
        self.assertListEqual(
            logger.output,
            ["INFO:dakara_base.websocket_client:Websocket disconnected from server"],
        )

        # assert the call
        mocked_create_timer.assert_not_called()
        mocked_on_connection_lost.assert_not_called()

    @patch.object(WebSocketClient, "create_timer")
    @patch.object(WebSocketClient, "on_connection_lost")
    def test_on_close_retry(self, mocked_on_connection_lost, mocked_create_timer):
        """Test the callback on connection close when connection should retry
        """
        # create the websocket
        self.set_websocket()

        # pre assert
        self.assertFalse(self.client.retry)

        # call the method
        with self.assertLogs("dakara_base.websocket_client", "DEBUG") as logger:
            self.client.on_close(None, None)

        # assert the retry flag is set
        self.assertTrue(self.client.retry)

        # assert the effect on logger
        self.assertListEqual(
            logger.output,
            [
                "ERROR:dakara_base.websocket_client:Websocket connection lost",
                "WARNING:dakara_base.websocket_client:Trying to reconnect in 1 s",
            ],
        )

        # assert the different calls
        mocked_create_timer.assert_called_with(self.reconnect_interval, self.client.run)
        mocked_create_timer.return_value.start.assert_called_with()
        mocked_on_connection_lost.assert_called_with()

    @patch.object(WebSocketClient, "receive_dummy", create=True)
    def test_on_message_successful(self, mocked_receive_dummy):
        """Test a normal use of the on message method
        """
        event = '{"type": "dummy", "data": "data"}'
        content = "data"

        # call the method
        self.client.on_message(event)

        # assert the dummy method has been called
        mocked_receive_dummy.assert_called_with(content)

    def test_on_message_failed_json(self):
        """Test the on message method when event is not a JSON string
        """
        event = "definitely not a JSON string"

        # call the method
        with self.assertLogs("dakara_base.websocket_client", "DEBUG") as logger:
            self.client.on_message(event)

        # assert the effect on logger
        self.assertListEqual(
            logger.output,
            [
                "ERROR:dakara_base.websocket_client:"
                "Unexpected message from the server: '{}'".format(event)
            ],
        )

    def test_on_message_failed_type(self):
        """Test the on message method when event has an unknown type
        """
        event = '{"type": "dummy", "data": "data"}'

        # call the method
        with self.assertLogs("dakara_base.websocket_client", "DEBUG") as logger:
            self.client.on_message(event)

        # assert the effect on logger
        self.assertListEqual(
            logger.output,
            [
                "ERROR:dakara_base.websocket_client:"
                "Event of unknown type received 'dummy'"
            ],
        )

    def test_on_error_closing(self):
        """Test the callback on error when the program is closing

        The error should be ignored.
        """
        # close the program
        self.stop.set()

        # call the method
        self.client.on_error(Exception("error message"))

        # assert the list of errors is empty
        self.assertTrue(self.errors.empty())

    def test_on_error_unknown(self):
        """Test the callback on an unknown error

        The error should be logged only.
        """
        # pre assert
        self.assertFalse(self.stop.is_set())

        class CustomError(Exception):
            pass

        # call the method
        with self.assertLogs("dakara_base.websocket_client", "DEBUG") as logger:
            self.client.on_error(CustomError("error message"))

        # assert the list of errors is empty
        self.assertTrue(self.errors.empty())

        # assert the effect on logger
        self.assertListEqual(
            logger.output,
            ["ERROR:dakara_base.websocket_client:Websocket: error message"],
        )

    def test_on_error_authentication(self):
        """Test the callback on error when the authentication is refused
        """
        # pre assert
        self.assertFalse(self.stop.is_set())

        # call the method
        self.client.on_error(WebSocketBadStatusException("error %s %s", 0))

        # assert the list of errors is not empty
        self.assertFalse(self.errors.empty())
        _, error, _ = self.errors.get()
        self.assertIsInstance(error, AuthenticationError)

    def test_on_error_network_normal(self):
        """Test the callback on error when the server is unreachable
        """
        # pre assert
        self.assertFalse(self.client.retry)
        self.assertFalse(self.stop.is_set())

        # call the method
        self.client.on_error(ConnectionRefusedError("error"))

        # assert the list of errors is not empty
        self.assertFalse(self.errors.empty())
        _, error, _ = self.errors.get()
        self.assertIsInstance(error, NetworkError)

    def test_on_error_network_retry(self):
        """Test the callback on error when the server is unreachable on retry

        No exception should be raised, the error should be logged only.
        """
        # pre assert
        self.assertFalse(self.stop.is_set())

        # set retry flag on
        self.client.retry = True

        # call the method
        with self.assertLogs("dakara_base.websocket_client", "DEBUG") as logger:
            self.client.on_error(ConnectionRefusedError("error"))

        # assert the list of errors is empty
        self.assertTrue(self.errors.empty())

        # assert the effect on logger
        self.assertListEqual(
            logger.output,
            ["WARNING:dakara_base.websocket_client:Unable to talk to the server"],
        )

    def test_on_error_route(self):
        """Test the callback on error when the route is invalid
        """
        # pre assert
        self.assertFalse(self.stop.is_set())

        # call the method
        self.client.on_error(ConnectionResetError("error"))

        # assert the call
        self.assertFalse(self.errors.empty())
        _, error, _ = self.errors.get()
        self.assertIsInstance(error, ValueError)

    def test_on_error_closed(self):
        """Test the callback on error when the connection is closed by server
        """
        # pre assert
        self.assertFalse(self.stop.is_set())
        self.assertFalse(self.client.retry)

        # call the methods
        self.client.on_error(WebSocketConnectionClosedException("error"))

    def test_send(self):
        """Test a normal use of the function
        """
        event = '{"data": "data"}'
        content = {"data": "data"}

        # set the websocket
        self.set_websocket()

        # call the method
        self.client.send(content)

        # assert the call
        self.client.websocket.send.assert_called_with(event)

    def test_abort_connected(self):
        """Test to abort the connection
        """
        # pre assert
        self.assertFalse(self.client.retry)

        # set the websocket
        self.set_websocket()

        # call the method
        self.client.abort()

        # assert the call
        self.client.websocket.sock.abort.assert_called_with()
        self.assertFalse(self.client.retry)

    def test_abort_disconnected(self):
        """Test to abort the connection when already disconnected
        """
        # pre assert
        self.assertFalse(self.client.retry)
        self.assertIsNone(self.client.websocket)

        # call the method
        self.client.abort()

        # assert the call
        self.assertFalse(self.client.retry)

    def test_abort_retry(self):
        """Test to abort the connection when retry is set
        """
        # set the retry flag on
        self.client.retry = True

        # call the method
        self.client.abort()

        # assert the call
        self.assertFalse(self.client.retry)

    @patch.object(WebSocketClient, "on_error")
    @patch.object(WebSocketClient, "on_message")
    @patch.object(WebSocketClient, "on_close")
    @patch.object(WebSocketClient, "on_open")
    @patch("dakara_base.websocket_client.WebSocketApp")
    def test_run(
        self,
        mock_websocket_app_class,
        mocked_on_open,
        mocked_on_close,
        mocked_on_message,
        mocked_on_error,
    ):
        """Test to create and run the connection
        """
        # pre assert
        self.assertIsNone(self.client.websocket)

        # call the method
        with self.assertLogs("dakara_base.websocket_client", "DEBUG") as logger:
            self.client.run()

        # assert the effect on logger
        self.assertListEqual(
            logger.output,
            ["DEBUG:dakara_base.websocket_client:Preparing websocket connection"],
        )

        # assert the call
        mock_websocket_app_class.assert_called_with(
            self.url,
            header=self.header,
            on_open=ANY,
            on_close=ANY,
            on_message=ANY,
            on_error=ANY,
        )
        self.client.websocket.run_forever.assert_called_with()

        # assert that the callback are correctly set
        # since the callback methods are adapted, we cannot check directy if
        # the given method reference is the same as the corresponding instance
        # method
        # so, we check that calling the given method calls the instance method
        websocket = MagicMock()
        _, kwargs = mock_websocket_app_class.call_args

        kwargs["on_open"](websocket)
        self.client.on_open.assert_called_with()

        kwargs["on_close"](websocket, None, None)
        self.client.on_close.assert_called_with(None, None)

        kwargs["on_message"](websocket, "message")
        self.client.on_message.assert_called_with("message")

        kwargs["on_error"](websocket, "error")
        self.client.on_error.assert_called_with("error")

        # post assert
        # in real world, this test is impossible, since the websocket object
        # has been destroyed by `on_close`
        # we use the fact this callback is not called to check if the
        # object has been created as expected
        # maybe there is a better scenario to test this
        self.assertIsNotNone(self.client.websocket)
