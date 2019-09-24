import socket
from unittest import mock

from tamarco.resources.basic.metrics.reporters import CarbonHandler
from tests.unit.resources.basic.metrics.reporters.test_base import check_metric_str


def test_carbon(sample_meters):
    with mock.patch("socket.socket") as socket_mock:
        handler = CarbonHandler(metric_prefix="test")
        handler.write(sample_meters)
        socket_call = socket_mock.mock_calls[2][1][0]
        check_metric_str(socket_call.decode())


def test_carbon_socket_error(sample_meters):
    with mock.patch("socket.socket"):
        handler = CarbonHandler()
        handler.socket.send = mock.Mock(side_effect=socket.timeout)
        handler.write(sample_meters)
        handler.socket.connect.assert_called_with((handler.host, handler.port))
        handler.socket.send.assert_called()
