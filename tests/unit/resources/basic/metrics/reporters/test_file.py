from unittest import mock

from tamarco.resources.basic.metrics.reporters import FileHandler
from tests.unit.resources.basic.metrics.reporters.test_base import check_metric_str


def test_file(sample_meters):
    with mock.patch("tamarco.resources.basic.metrics.reporters.file.open", mock.mock_open(), create=True) as open_mock:
        handler = FileHandler(metric_prefix="test")
        handler.write(sample_meters)
        file_mock = open_mock.mock_calls[1][1][0]
        check_metric_str(file_mock)
