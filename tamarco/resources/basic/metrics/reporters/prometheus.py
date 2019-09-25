import logging
from random import choice

from sanic.response import text

from tamarco.resources.basic.metrics.reporters.base import CarbonBaseHandler

logger = logging.getLogger("tamarco.metrics")


class PrometheusHandler(CarbonBaseHandler):
    """Handler for the applications metrics that sends them to a Prometheus API."""

    def __init__(self, metric_id_prefix=None):
        """Initialize the Carbon handler.

        Args:
            metric_id_prefix (str): Concatenated prefix in all metrics.
        """
        self.http_body = "# HELP NO METRICS\n"
        self.metric_id_prefix = metric_id_prefix if metric_id_prefix else ""
        super().__init__()

    async def http_handler(self, request):
        """Handler for the Prometheus endpoint.

        Args:
            request: HTTP request.

        Returns:
            object: Response object with body in text format.
        """
        return text(body=self.http_body, status=200)

    def write(self, meters):
        """Build the metrics report from all meters.

        Args:
            meters (list): List of meters from which the metrics will be obtained.
        """
        try:
            self.http_body = self.format_metrics(meters)
        except Exception:
            self.http_body = "# HELP Error collecting metrics"
            logger.warning("Unexpected exception formatting metrics in Metrics prometheus handler", exc_info=True)

    def format_metrics(self, meters):
        """Format available metrics from all `meters`.

        Args:
            meters (list): List of meters from which the metrics will be obtained.

        Returns:
            str: A text with a metric per line.
        """
        http_body = ""
        meters_by_type = {meter.metric_id: meter.metric_type for meter in meters}
        for meter_id, meter_type in meters_by_type.items():
            help_and_type_lines = False
            meters_with_meter_id = {meter for meter in meters if meter.metric_id == meter_id}
            for meter in meters_with_meter_id:
                metrics = meter._collect_metrics()
                if not help_and_type_lines:
                    http_body += self.parse_help_line(self.parse_metric_id(meter.metric_id), choice(metrics).units)
                    http_body += self.parse_type_line(self.parse_metric_id(meter_id), meter_type)
                    help_and_type_lines = True
                http_body += self.parse_metrics(metrics)
        return http_body

    @staticmethod
    def parse_type_line(metric_id, metric_type):
        """Build the Prometheus TYPE line.

        Args:
            metric_id (str): Identifier of the metric.
            metric_type (str): Type of the metric.

        Returns:
            str: Prometheus TYPE line.
        """
        return f"# TYPE {metric_id} {metric_type}\n"

    @staticmethod
    def parse_help_line(metric_id, meter_unit):
        """Build the Prometheus HELP line.

        Args:
            metric_id (str): Identifier of the metric.
            meter_unit (str): Unit of the metric.

        Returns:
            str: Prometheus HELP line.
        """
        return f"# HELP {metric_id} units {meter_unit}\n"

    def parse_metric_id(self, metric_id: str):
        """Format the identifier of the metric.

        Args:
            metric_id (str): Identifier of the metric.

        Returns:
            str: formatted metric id.
        """
        metric_id_replaced = metric_id.replace(".", "_")
        return f"{self.metric_id_prefix}_{metric_id_replaced}"

    def parse_metrics(self, metrics):
        """Format all the metrics from the `metrics` list.

        Args:
            metrics (list): list of metrics.

        Returns:
            str: A text with a metric per line.
        """
        parsed_metric = ""
        for metric in metrics:
            metric_value = metric.value if not metric.empty else "NaN"
            label_str = self.parse_labels(metric.labels)
            metric_id = self.parse_metric_id(metric.id)
            parsed_metric += f"{metric_id}{label_str} {metric_value}\n"
        return parsed_metric

    @staticmethod
    def parse_labels(labels):
        """Format the labels metric and their values.

        Args:
            labels (list): List of metric labels.

        Returns:
            str: A string with all the labels and their values separated by dots.
        """
        if labels:
            labels_str_list = [f'{key}="{value}"' for key, value in labels.items()]
            labels_str = "{" + ",".join(labels_str_list) + "}"
            return labels_str
        else:
            return ""
