import queue
from logging.handlers import QueueHandler, QueueListener

from tamarco.resources.basic.metrics.meters import Counter

MAX_QUEUE_SIZE = 10000


class QueueHandlerAsyncHandler(QueueHandler):
    """Asynchronous version of the logging QueueHandler class."""

    def __init__(self, log_queue):
        """Initialize the Asynchronous QueueHandler class.

        Args:
            log_queue (Queue): Queue class instance (python standard library).
        """
        self.counter_overflow_queue = None
        super().__init__(log_queue)

    def enqueue(self, record):
        """If there is free space in the queue, the record is added to it.

        Args:
            record (LogRecord): Entry log record.
        """
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            self.counter_overflow_queue.inc()

    def prepare(self, record):
        """To avoid exc_info from being deleted QueueHandler.prepare() sets exc_info to None and calls
        it's own format().

        Args:
            record (Log record): Entry log record.
        """
        return record


class AsyncWrapperHandler(QueueHandlerAsyncHandler):
    """Wrapper of the asynchronous queue handler class."""

    def __init__(self, handler, *args, **kwargs):
        """The queue and its listener are initialized."

        Args:
            handler (class): Handler for the logging queue.
        """
        self.queue = queue.Queue(MAX_QUEUE_SIZE)
        super().__init__(self.queue)
        self.handler = handler(*args, **kwargs)
        self.handler_name = self.handler.__class__.__name__
        self.listener = QueueListener(self.queue, self.handler)
        self.counter_overflow_queue = Counter(f"counter_overflow_queue_{self.handler_name}", "messages")
        self.listener.start()

    def __del__(self):
        """Stop the queue listener."""
        self.listener.stop()
