import logging
import socket
import traceback
from datetime import datetime

import ujson as json


class LogstashFormatterBase(logging.Formatter):
    """Base formatter class to convert the log record in the different logstash formats."""

    def __init__(self, message_type="Logstash", fqdn=False, service_name=None, deploy_name=None):
        """Initialize the logstash base formatter class.

        Args:
            message_type (str): Type field in the log record.
            fqdn (bool): If True, the host field in the log record will be the fully qualified domain. Otherwise,
                the system hostname.
            service_name (str): Service name field in the log record.
            deploy_name (str): Deploy name field in the log record.
        """
        self.message_type = message_type
        self.service_name = service_name
        self.deploy_name = deploy_name
        if fqdn:
            self.host = socket.getfqdn()
        else:
            self.host = socket.gethostname()
        self.skip_list = (
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "id",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "msecs",
            "message",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "thread",
            "threadName",
            "extra",
            "auth_token",
            "password",
            "tags",
        )

        self.easy_types = (str, bool, dict, float, int, list, type(None), tuple, set)

    def get_extra_fields(self, record):
        """Get the fields (and its values) present in the log record that are not in the `skip_list` attribute
        set in the `_init_` method.

        Args:
            record (LogRecord): Log record to process.

        Returns:
            dict: The keys of the dictionary are LogRecord attributes and the dict values are the string
            representation of the attributes values.
        """
        fields = {}

        for key, value in record.__dict__.items():
            if key not in self.skip_list:
                if isinstance(value, self.easy_types):
                    fields[key] = value
                else:
                    fields[key] = repr(value)

        return fields

    def get_debug_fields(self, record):
        """Get the fields (and its values) present in the log record that are related with the debugging process.

        Args:
            record (LogRecord): Log record to process.

        Returns:
            dict: The keys of the dictionary are LogRecord attributes and the dict values are the attributes values.
        """
        fields = {
            "stack_trace": self.format_exception(record.exc_info),
            "lineno": record.lineno,
            "process": record.process,
            "thread_name": record.threadName,
        }

        if not getattr(record, "funcName", None):
            fields["funcName"] = record.funcName

        if not getattr(record, "processName", None):
            fields["processName"] = record.processName

        return fields

    @classmethod
    def format_source(cls, message_type, host, path):
        """Format the source field of the log record.

        Args:
            message_type (str): Type of the log record message.
            host (str): Hostname or the fully qualified domain where the logging call was made.
            path (str): The full pathname of the source file where the logging call was made.

        Returns:
            string: URI of the file where the logging call was made.
        """
        return f"{message_type}://{host}/{path}"

    @classmethod
    def format_timestamp(cls, time):
        """Convert the timestamp passed by argument to the format: YYYY-mm-ddTHH:MM:SS.sssZ.

        Args:
            time (timestamp): Timestamp to format.

        Returns:
            string: Timestamp formatted with the format (YYYY-mm-ddTHH:MM:SS.sssZ).
        """
        tstamp = datetime.utcfromtimestamp(time)
        return f'{tstamp.strftime("%Y-%m-%dT%H:%M:%S")}.{int(tstamp.microsecond / 1000):03}Z'

    @classmethod
    def format_exception(cls, exc_info):
        """Concatenate the strings present in the exc_info list.

        Args:
            exc_info (list): Exception information to be included in the log entry.

        Returns:
            string: If exc_info is an empty list, an empty string is returned. If exc_info is not an empty list,
            the string resulting from concatenating all exc_info items is returned.
        """
        return "".join(traceback.format_exception(*exc_info)) if exc_info else ""

    @classmethod
    def serialize(cls, message):
        """Convert arbitrary object recursively into JSON.

        Args:
            message (dict): Log entry information.

        Returns:
            json: The log entry information in a JSON object.
        """
        return json.dumps(message).encode()


class LogstashFormatterVersion0(LogstashFormatterBase):
    """Formatter class to convert the log record into the logstash format version 0."""

    version = 0

    def format(self, record):  # noqa: A003
        """Convert the log record into the logstash format version 0, adding extra and debug info if applicable.

        Args:
            record (LogRecord): Log entry.

        Returns:
            json: Log entry information in a JSON object.
        """
        # Create message dict.
        message = {
            "@timestamp": self.format_timestamp(record.created),
            "@message": record.getMessage(),
            "@source": self.format_source(self.message_type, self.host, record.pathname),
            "@source_host": self.host,
            "@source_path": record.pathname,
            "@tags": getattr(record, "tags", []),
            "@type": self.message_type,
            "@fields": {"levelname": record.levelname, "logger": record.name},
        }

        # Add extra fields.
        message["@fields"].update(self.get_extra_fields(record))

        if self.service_name:
            message["@fields"]["service_name"] = self.service_name

        if self.deploy_name:
            message["@fields"]["deploy_name"] = self.deploy_name

        # If exception, add debug info.
        if record.exc_info:
            message["@fields"].update(self.get_debug_fields(record))

        return self.serialize(message)


class LogstashFormatterVersion1(LogstashFormatterBase):
    """Formatter class to convert the log record into the logstash format version 1."""

    def format(self, record):  # noqa: A003
        """Converts the log record into the logstash format version 1, adding extra and debug info if applicable.

        Args:
            record (LogRecord): Log entry.

        Returns:
            json: Log entry information in a JSON object.
        """
        # Create message dict.
        message = {
            "@timestamp": self.format_timestamp(record.created),
            "@version": "1",
            "message": record.getMessage(),
            "host": self.host,
            "path": record.pathname,
            "tags": getattr(record, "tags", []),
            "type": self.message_type,
            # Extra Fields
            "level": record.levelname,
            "logger_name": record.name,
        }

        # Add extra fields.
        message.update(self.get_extra_fields(record))

        # If exception, add debug info.
        if record.exc_info:
            message.update(self.get_debug_fields(record))

        return self.serialize(message)
