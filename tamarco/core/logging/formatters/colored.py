import logging
from datetime import datetime

import ujson


class ColoredFormatter(logging.Formatter):
    """Formatter to log colored records in console."""

    def __init__(self, color_blind=False):
        """Initialize the python core logging formatter and set custom attribute.

        Args:
            color_blind (bool): Change the color scheme for a higher color contrast.
        """
        super().__init__()
        self.color_blind = color_blind

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
        # https://github.com/tartley/colorama#recognised-ansi-sequences
        if self.color_blind:
            level_color = {
                "DEBUG": "\x1b[1;37;42m DEBUG \x1b[0m ",
                "INFO": "\x1b[1;30;47m INFO \x1b[0m ",
                "WARNING": "\x1b[1;37;45m WARNING \x1b[0m ",
                "ERROR": "\x1b[1;33;41m ERROR \x1b[0m ",
                "CRITICAL": "\x1b[1;37;46m CRITICAL \x1b[0m ",
            }
        else:
            level_color = {
                "DEBUG": "\x1b[1;37;42m DEBUG \x1b[0m ",
                "INFO": "\x1b[1;30;47m INFO \x1b[0m ",
                "WARNING": "\x1b[1;37;43m WARNING \x1b[0m ",
                "ERROR": "\x1b[1;37;41m ERROR \x1b[0m ",
                "CRITICAL": "\x1b[1;37;44m CRITICAL \x1b[0m ",
            }

        level = level_color[record.levelname] if record.levelname in level_color else f"[{record.levelname}] "
        tags = f"{list(record.tags)} " if hasattr(record, "tags") else ""
        new_record = (
            f"[{self.format_timestamp(record.created)}] {level} [({record.name}) {record.filename}:"
            f"{record.lineno}] {tags}\x1b[0;33m {record.getMessage()} \x1b[0m"
        )

        if hasattr(record, "extra_msg"):
            try:
                new_record += f"\x1b[0;33m\n {ujson.dumps(record.extra_msg, indent=3)} \x1b[0m"
            except Exception:
                pass
        if record.exc_info:
            new_record += f"\n \x1b[0;31m {self.formatException(record.exc_info)} \x1b[0m"

        return new_record
