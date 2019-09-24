import logging
import socket

from tamarco.core.settings.settings import SettingNotFound
from tamarco.resources.bases import BaseResource
from tamarco.resources.basic.metrics.manager import MetersManager
from tamarco.resources.basic.metrics.reporters.carbon import CarbonHandler
from tamarco.resources.basic.metrics.reporters.file import FileHandler
from tamarco.resources.basic.metrics.reporters.prometheus import PrometheusHandler
from tamarco.resources.basic.metrics.reporters.stdout import StdoutHandler
from tamarco.resources.basic.status.status_codes import StatusCodes
from tamarco.resources.io.http.resource import HTTPServerResource
from .settings import PROMETHEUS_METRICS_HTTP_ENDPOINT


class MetricsResource(BaseResource):
    """Resource class to handle the applications metrics."""

    depends_on = ["tamarco_http_report_server"]
    loggers_names = ["tamarco.metrics"]

    def __init__(self, *args, **kwargs):
        """Initialize the metrics resource.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self._metric_prefix = None
        self.logger = logging.getLogger("tamarco.metrics")
        self.status_codes = StatusCodes
        self.http_server_resource = HTTPServerResource()

    @property
    def metric_prefix(self):
        """Get the metrics prefix as a attribute.

        Returns:
            str: Metric prefix.
        """
        if not self._metric_prefix:
            self._metric_prefix = self._get_metric_prefix()
        return self._metric_prefix

    def _get_metric_prefix(self):
        """Build the metrics prefix.

        Returns:
            str: Metric prefix.
        """
        deploy_name = self.microservice.deploy_name
        service_name = self.microservice.name
        hostname = socket.gethostname()
        metrics_prefix = f"{deploy_name}.{service_name}.{hostname}"
        return metrics_prefix

    async def _configure_carbon_handler(self):
        """Load the Carbon handler configuration settings and adds the handler to the Meters Manager."""
        try:
            enabled = await self.settings.get("handlers.carbon.enabled")
        except SettingNotFound:
            self.logger.warning("Metrics carbon handler cannot be configured because the enabled setting is missing")
        else:
            if enabled:
                try:
                    host = await self.settings.get("handlers.carbon.host")
                    port = await self.settings.get("handlers.carbon.port")
                except SettingNotFound:
                    self.logger.warning(
                        "Metrics carbon handler cannot be configured because the host and/or port "
                        "settings are missing."
                    )
                else:
                    carbon_handler = CarbonHandler(host, port, self.metric_prefix)
                    MetersManager.add_handler(carbon_handler)
            else:
                self.logger.info("Metrics carbon handler is disabled")

    async def _configure_file_handler(self):
        """Load the File handler configuration settings and adds the handler to the Meters Manager."""
        try:
            enabled = await self.settings.get("handlers.file.enabled")
        except SettingNotFound:
            self.logger.warning("Metrics file handler cannot be configured because the enabled setting is missing")
        else:
            if enabled:
                try:
                    file_path = await self.settings.get("handlers.file.path")
                    file_handler = FileHandler(file_path=file_path)
                except SettingNotFound:
                    self.logger.warning("Metrics file handler cannot be configured because the path setting is missing")
                else:
                    MetersManager.add_handler(file_handler)
            else:
                self.logger.info("Metrics file handler is disabled")

    async def _configure_stdout_handler(self):
        """Load the Standard Output handler configuration settings and adds the handler to the Meters Manager."""
        try:
            enabled = await self.settings.get("handlers.stdout.enabled")
        except SettingNotFound:
            self.logger.warning("Metrics stdout handler cannot be configured because the enabled setting is missing")
        else:
            if enabled:
                try:
                    stdout_prefix = await self.settings.get("handlers.stdout.prefix")
                except SettingNotFound:
                    self.logger.warning(
                        "Metrics stdout handler cannot be configured because the prefix setting is " "missing"
                    )
                else:
                    stdout_handler = StdoutHandler(metric_prefix=stdout_prefix)
                    MetersManager.add_handler(stdout_handler)
            else:
                self.logger.info("Metrics stdout handler is disabled")

    async def _configure_prometheus_handler(self):
        """Load the Prometheus handler configuration settings and adds the handler to the Meters Manager."""
        try:
            enabled = await self.settings.get("handlers.prometheus.enabled")
        except SettingNotFound:
            self.logger.warning(
                "Metrics prometheus handler cannot be configured because the enabled setting is " "missing"
            )
        else:
            if enabled:
                try:
                    prometheus_handler = PrometheusHandler(metric_id_prefix=self.microservice.name)
                    MetersManager.add_handler(prometheus_handler)
                    self.microservice.tamarco_http_report_server.add_endpoint(
                        uri=PROMETHEUS_METRICS_HTTP_ENDPOINT, endpoint_handler=prometheus_handler.http_handler
                    )
                except Exception:
                    self.logger.exception("Unexpected exception configuring the Metrics prometheus handler")
            else:
                self.logger.info("Metrics prometheus handler is disabled")

    async def _configure_collect_period(self):
        """Load the collect period setting and adds it to the Meters Manager."""
        try:
            collect_frequency = await self.settings.get("collect_frequency")
        except SettingNotFound:
            self.logger.warning(
                f"Metrics collect frequency is not configured because the collect_frequency setting is "
                f"missing. Using the default value: {MetersManager.default_collect_period}"
            )
        else:
            self.logger.info(f"Metrics collect frequency configured: {collect_frequency} seconds")
            MetersManager.configure(config={"collect_period": collect_frequency})

    async def start(self):
        """Configure the metrics available handlers."""
        await super().start()
        await self._configure_carbon_handler()
        await self._configure_file_handler()
        await self._configure_stdout_handler()
        await self._configure_collect_period()
        await self._configure_prometheus_handler()
        MetersManager.start()

    async def stop(self):
        """Stop the Metrics Manager."""
        self.logger.info(f"Stopping Metrics resource: {self.name}")
        await super().stop()
        MetersManager.stop()

    async def status(self):
        """Return the resource status code.

        Returns:
            dict: Resource status.
        """
        return {"status": self._status}
