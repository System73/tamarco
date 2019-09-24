import datetime
import logging

from pyes import ES
from pyes.exceptions import NoServerAvailable

from tamarco.core.logging.formatters import logstash
from tamarco.core.logging.handlers.asyncronous import AsyncWrapperHandler


class ElasticSearchHandler(logging.Handler):
    """Logging handler that sends the logs to a Elasticsearch instance."""

    def __init__(
        self,
        conn_strs=None,
        record_type="record",
        level=logging.NOTSET,
        fqdn=False,
        service_name=None,
        deploy_name=None,
        version=0,
    ):
        """Initialize the handler.

        Args:
            conn_strs (list): List of Elasticsearch connections strings.
            record_type (str): The record type always will be 'record'.
            level (str): Logging level. Default: NOTSET
            fqdn (bool): If True, the host field in the log record will be the fully qualified domain. Otherwise,
                the system hostname.
            service_name (str): Service name.
            deploy_name (str): Deploy name.
            version (int): If 1 it is used the Logstash formatter version 1. Otherwise, the logstash formatter
                version 0.
        """
        logging.Handler.__init__(self, level=level)
        self.conn_strs = conn_strs if conn_strs else ["127.0.0.1:9200"]
        self.connected = False
        self.conn = None
        self.try_conn()
        self.record_type = record_type
        if version == 1:
            self.formatter = logstash.LogstashFormatterVersion1(record_type, fqdn, service_name, deploy_name)
        else:
            self.formatter = logstash.LogstashFormatterVersion0(record_type, fqdn, service_name, deploy_name)

    def try_conn(self):
        """Try a new connection to the Elasticsearch."""
        try:
            self.conn = ES(self.conn_strs, timeout=5)
            self.connected = True
        except NoServerAvailable:
            print("Error connecting to elasticsearch for logging")

    @property
    def index_name(self):
        """Construct the logs Elasticsearch index.

        Returns:
            string: Logstash index.
        """
        return "logstash-" + datetime.date.today().strftime("%Y.%m.%d")

    def emit(self, record):
        """Emit the specified log record.

        Args:
            record (LogRecord): Entry log to emit.
        """
        entry = self.formatter.format(record)
        if self.connected:
            self.conn.index(entry, self.index_name, self.record_type)
        else:
            self.try_conn()


class AsyncElasticSearchHandler(AsyncWrapperHandler):
    """Asynchronous version of the logging handler that sends the logs to a Elasticsearch instance."""

    def __init__(self, *args, **kwargs):
        """Initialize the asynchronous Elasticsearch handler."""
        super().__init__(ElasticSearchHandler, *args, **kwargs)
