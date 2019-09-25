import asyncio
import logging
import signal

from tamarco.core.patterns import Singleton

logger = logging.getLogger("tamarco.signals")

# Object that holds all the signals names and numbers,
# is a copy of the values of the standard module of python
signals_name_to_number = {}

for signal_name in filter(lambda may_sig_name: may_sig_name.startswith("SIG"), dir(signal)):
    signals_name_to_number[signal_name] = getattr(signal, signal_name)


def signal_handler(signal_number):
    """Decorator to declare a function as a signal handler.

    Args:
        signal_number (int): integer with the signal number to handle.
    """

    def wrapper(fn):
        SignalsManager().register_signal(fn, signal_number)
        return fn

    return wrapper


class SignalsManager(metaclass=Singleton):
    """Class responsible of the handling of unix signals."""

    handlers = {}

    def __init__(self):
        self.loop = None
        self.async_timeout_seconds = 5

    def set_loop(self, loop):
        """Declares the event loop used for handlers that are coroutines.

        Args:
            loop: asyncio event loop where to launch coroutines.
        """
        self.loop = loop

    def register_signal(self, handler, signal_number):
        """Register a handler for a signal.

        Args:
            handler: function or coroutine to handle the signal_number.
            signal_number (int): number of the signal_number to be handled.
        """
        if signal_number not in self.handlers:
            self.handlers[signal_number] = []
            signal.signal(signal_number, self._dispatch_signal)
        self.handlers[signal_number].append(handler)

    async def _cancellation_wrapper(self, task):
        try:
            await asyncio.wait_for(task, self.async_timeout_seconds)
        except asyncio.CancelledError:
            logger.warning(f"Timeout triggered calling {task} in async signal_number handler", exc_info=True)

    def _dispatch_signal(self, signum, frame):
        for handler in self.handlers[signum]:
            if asyncio.iscoroutinefunction(handler):
                try:
                    asyncio.ensure_future(self._cancellation_wrapper(task=handler(signum, frame)), loop=self.loop)
                except Exception:
                    logger.warning(
                        f"Error trying to execute the async signal_number handler {handler} of the "
                        f"signal_number: {signum}",
                        exc_info=True,
                    )
            else:
                try:
                    handler(signum, frame)
                except Exception:
                    logger.warning(
                        f"Unexpected exception in the signal_number handler {handler} of the "
                        f"signal_number: {signum}",
                        exc_info=True,
                    )
