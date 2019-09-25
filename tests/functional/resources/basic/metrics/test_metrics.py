import socket
import time
from unittest import mock

import pytest

from tamarco.resources.basic.metrics import MetersManager
from tamarco.resources.basic.metrics.meters import Counter, Gauge
from tamarco.resources.basic.metrics.reporters import CarbonHandler, FileHandler, StdoutHandler


@pytest.fixture
def meters_manager():
    """ This fixture is needed because if the metrics tests fails and exit before
    the MetersManagers call to its stop() function, the coverage process will never stop
    (the MetersManagers have to kill their threads). """

    yield

    MetersManager.stop()


def test_metrics(meters_manager):
    with mock.patch("socket.socket") as socket_mock, mock.patch(
        "tamarco.resources.basic.metrics.reporters.file.open", mock.mock_open(), create=True
    ) as open_mock:
        MetersManager.add_handler(CarbonHandler("127.0.0.1", 2003, metric_prefix=socket.gethostname()))
        MetersManager.add_handler(FileHandler("/tmp/metrics"))
        MetersManager.add_handler(StdoutHandler(metric_prefix="metric"))
        MetersManager.configure({"collect_period": 1})
        MetersManager.start()

        gauge_test = Gauge("critical.path.function.time", "seconds")

        @Counter("count.things", "things")
        def count_one():
            pass

        @gauge_test.timeit()
        def wait_one_ms():
            time.sleep(0.1)

        for _ in range(0, 20):
            count_one()
            wait_one_ms()

        socket_mock.assert_called()
        open_mock.assert_called()
