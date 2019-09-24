from tamarco.resources.basic.metrics.reporters.base import CarbonBaseHandler


class StdoutHandler(CarbonBaseHandler):
    """Handler for the applications metrics that send them to the standard output."""

    def write(self, meters):
        """Build the metrics report from all meters.

        Args:
            meters (list): List of meters from which the metrics will be obtained.
        """
        metrics_str = self.format_metrics(meters)
        print(metrics_str)
