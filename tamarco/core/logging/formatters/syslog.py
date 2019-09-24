import logging
import socket
from datetime import datetime

import ujson as json


class SyslogFormatter(logging.Formatter):
    """Formatter to log records like syslog records."""

    def __init__(self):
        """Initialize the syslog formatter class."""
        super().__init__()
        self.isoformat_sep = " "

    def format_timestamp(self, timestamp):
        """Format the log record timestamp.

        Args:
            timestamp (timestamp): Log record timestamp to format.

        Returns:
            string: Datetime in ISO 8601 format (YYYY-MM-DD HH:MM:SS[.mmmmmm][+HH:MM]).
        """
        return datetime.fromtimestamp(timestamp).isoformat(sep=self.isoformat_sep)

    def format(self, record):  # noqa: A003
        """Format the specified record as text.

        Args:
            record (LogRecord): Log record to format.

        Returns:
            string: Log record formatted as syslog string.
        """
        tags = f"[{list(record.tags)})] " if hasattr(record, "tags") else "[null] "
        new_record = (
            f"[{self.format_timestamp(record.created)}] [{socket.getfqdn()}] [{record.levelname}] "
            f"[({record.name}) {record.filename}:{record.lineno}] {tags}[{record.getMessage()}] "
        )

        if not hasattr(record, "extra_msg"):
            new_record += "[null]"
        else:
            try:
                # The next line only works with the first level of the dict!
                extra_msg = {"json_" + str(k): str(v) for k, v in record.extra_msg.items()}
                if record.exc_info:
                    extra_msg.update({"json_exception": self.formatException(record.exc_info)})
                new_record += f"[{json.dumps(extra_msg)}] "
            except Exception:
                pass

        return new_record
