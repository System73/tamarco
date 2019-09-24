from tamarco.resources.basic.metrics import MetersManager
from tamarco.resources.basic.metrics.collector import MetricsCollector
from tamarco.resources.basic.metrics.reporters import FileHandler


def test_configure_meters_manager():
    MetricsCollector.handlers.clear()
    MetricsCollector.collect_period = 2
    MetersManager.configure({"handlers": [{"handler": FileHandler, "file_path": "/tmp/metrics"}], "collect_period": 2})
    assert isinstance(MetricsCollector.handlers[0], FileHandler)
    MetersManager.thread.stop = True
