from unittest import mock

from tamarco.resources.basic.metrics.reporters import StdoutHandler
from tests.unit.resources.basic.metrics.reporters.test_base import check_metric_str


def test_stdout(sample_meters):
    handler = StdoutHandler("test")
    with mock.patch("builtins.print") as print_mock:
        handler.write(sample_meters)
        stdout = print_mock.call_args[0][0]
        from pprint import pprint

        pprint(stdout)
        check_metric_str(stdout)
