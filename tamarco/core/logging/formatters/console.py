import logging
from datetime import datetime

import ujson


class ConsoleFormatter(logging.Formatter):
    """Formatter to log records in console."""

    def __init__(self):
        """Initialize the python core logging formatter and set custom attribute."""
        super().__init__()

    @staticmethod
    def format_timestamp(timestamp):
        """Format the time for our log record.

        Args:
            timestamp (timestamp): Timestamp to format.

        Returns:
            string: Datetime in ISO 8601 format (YYYY-MM-DD HH:MM:SS[.mmmmmm][+HH:MM]).
        """
        return datetime.fromtimestamp(timestamp).isoformat(sep=" ")

    def format(self, record):  # noqa: A003
        """Format the specified record as text.

        Args:
            record (LogRecord): Logging record to format.

        Returns:
            string: Log record formatted as a colored text.
        """
        tags = f"{list(record.tags)} " if hasattr(record, "tags") else ""
        new_record = (
            f"[{self.format_timestamp(record.created)}] [{record.levelname}] [({record.name}) {record.filename}:"
            f"{record.lineno}] {tags} {record.getMessage()}"
        )

        if hasattr(record, "extra_msg"):
            try:
                new_record += f" [{ujson.dumps(record.extra_msg)}]"
            except Exception:
                pass
        if record.exc_info:
            new_record += f" {self.formatException(record.exc_info)}"

        return new_record
