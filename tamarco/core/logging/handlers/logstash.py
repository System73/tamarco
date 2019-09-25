from logging.handlers import DatagramHandler

from .asyncronous import AsyncWrapperHandler
from ..formatters import logstash


class UDPLogstashHandler(DatagramHandler):
    """Logging handler for Logstash over UDP."""

    def __init__(
        self, host, port=5959, message_type="logstash", fqdn=False, service_name=None, deploy_name=None, version=0
    ):
        """Initialize the Logstash handler.

        Args:
            host (str): The host of the logstash server.
            port (int): The port of the logstash server.
            message_type (str): The type of the message (always be 'logstash').
            fqdn (bool): If True, the host field in the log record will be the fully qualified domain. Otherwise,
                the system hostname.
            service_name (str): Service name.
            deploy_name (str): Deploy name.
            version (int): If 1 it is used the Logstash formatter version 1. Otherwise, the logstash formatter
                version 0.
        """
        super().__init__(host, port)
        if version == 1:
            self.formatter = logstash.LogstashFormatterVersion1(message_type, fqdn, service_name, deploy_name)
        else:
            self.formatter = logstash.LogstashFormatterVersion0(message_type, fqdn, service_name, deploy_name)

    def makePickle(self, record):
        """Convert the log record into the chosen logstash format (version 0 or 1).

        Args:
            record (LogRecord): Entry log.

        Returns:
            json: Log entry information in a JSON object.
        """
        return self.formatter.format(record)


class AsyncUDPLogstashHandler(AsyncWrapperHandler):
    """Asynchronous version of the logging handler that sends the logs to a Logstash instance."""

    def __init__(
        self, host, port=5959, message_type="logstash", fqdn=False, service_name=None, deploy_name=None, version=0
    ):
        """Initialize the asynchronous Logstash handler.

         Args:
            host (str): The host of the logstash server.
            port (int): The port of the logstash server.
            message_type (str): The type of the message (always be 'logstash').
            fqdn (bool): If True, the host field in the log record will be the fully qualified domain. Otherwise,
                the system hostname.
            service_name (str): Service name.
            deploy_name (str): Deploy name.
            version (int): If 1 it is used the Logstash formatter version 1. Otherwise, the logstash formatter
                version 0.
        """
        super().__init__(UDPLogstashHandler, host, port, message_type, fqdn, service_name, deploy_name, version)
