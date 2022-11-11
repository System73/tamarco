import logging
import threading
import time

from tamarco.core.utils import set_thread_name

logger = logging.getLogger("tamarco.metrics")


class MetricsCollector:
    """ "Collect all the metrics from all the meters and using all the handler configured.

    Attributes:
        meters (list): List of meters from which the metrics will be obtained.
        handlers (list): List of metrics handlers where the metrics will be sent/stored.
        collect_period (int): interval time in seconds between the beginning of the metrics harvest.
    """

    meters = []
    handlers = []
    collect_period = 10

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def add_handler(cls, handler):
        """Append a handler in the handlers list.

        Args:
            handler: Metrics handler.
        """
        cls.handlers.append(handler)

    @classmethod
    def run(cls):
        """Collect the available metrics at defined time intervals."""
        set_thread_name()
        thread = threading.currentThread()
        while not thread.stop:
            start_time = time.time()
            try:
                cls.collect_metrics()
                cls.reset_meters()
            except Exception:
                logger.warning("Unexpected exception in Metrics collector thread", exc_info=True)
            cls.sleep_until_the_next_write(start_time)

    @classmethod
    def collect_metrics(cls):
        """Build the metrics reports for all configured handlers."""
        for handler in cls.handlers:
            handler.write(cls.meters)

    @classmethod
    def reset_meters(cls):
        """Reset the Summary meter."""
        for meter in cls.meters:
            from tamarco.resources.basic.metrics.meters import Summary

            if isinstance(meter, Summary):
                meter._reset()

    @classmethod
    def sleep_until_the_next_write(cls, start_time):
        """Sleep the remaining time left (after the beginning of the metrics harvest) to reach
        `collect_period` seconds.

        Args:
            start_time (int): Time in seconds when the metrics harvest started.
        """
        end_time = time.time()
        elapsed_time = end_time - start_time
        sleep_time = cls.collect_period - elapsed_time
        if sleep_time > 0:
            time.sleep(sleep_time)

    @classmethod
    def register_metric(cls, meter):
        """Append a new meter to the meters list.

        Args:
            meter: Metrics meter.
        """
        cls.meters.append(meter)


class CollectorThread(threading.Thread):
    """Run the metrics collector in a new thread."""

    stop = False
    name = "MetricsColl"

    def run(self):
        MetricsCollector.run()
