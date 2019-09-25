from tamarco.resources.basic.metrics.collector import CollectorThread, MetricsCollector


class MetersManager:
    """Class to manage the metrics harvest.

    Args:
        thread: Thread where the metrics collector will start.
        default_collect_period (int): Default interval time in seconds between the beginning of the metrics harvest.
    """

    thread = CollectorThread()
    default_collect_period = 10

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def configure(cls, config):
        """Load the settings configuration.

        Args:
            config (dict): settings configuration for the Metrics Collector.
        """
        for handler_data in config.get("handlers", []):
            handler = handler_data.pop("handler")
            cls.add_handler(handler(**handler_data))

        MetricsCollector.collect_period = config.get("collect_period", cls.default_collect_period)

    @classmethod
    def add_handler(cls, handler):
        """Append new handler to the MetricsCollector handlers list.

        Args:
            handler: Metrics handler.
        """
        MetricsCollector.add_handler(handler)

    @classmethod
    def start(cls):
        """Start the thread where the Metrics Collector starts."""
        cls.thread.start()

    @classmethod
    def stop(cls):
        """Stop the thread where the Metrics Collector starts."""
        cls.thread.stop = True
