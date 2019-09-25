from tamarco.resources.basic.metrics.collector import CollectorThread, MetricsCollector
from tamarco.resources.basic.metrics.meters import Counter
from tamarco.resources.basic.metrics.reporters import FileHandler
from tamarco.resources.basic.metrics.reporters.base import CarbonBaseHandler


def test_class_metrics_collector_add_handler():
    MetricsCollector.handlers.clear()
    MetricsCollector.add_handler(CarbonBaseHandler())
    assert isinstance(MetricsCollector.handlers[0], CarbonBaseHandler)


def test_class_metrics_collector():
    MetricsCollector.handlers.clear()
    MetricsCollector.add_handler(FileHandler())
    MetricsCollector.collect_period = 2
    MetricsCollector.meters = []
    counter = Counter("test_name", "test_unit")
    counter.inc()
    collector_thread = CollectorThread()
    assert isinstance(MetricsCollector.handlers[0], FileHandler)
    collector_thread.start()
    if not isinstance(MetricsCollector.meters[0], Counter):
        collector_thread.stop = True
        assert False, "type(MetricsCollector.meters[0]) is not Counter"  # noqa: B011
    collector_thread.stop = True
