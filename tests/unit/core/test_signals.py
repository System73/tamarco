import asyncio
import signal
import threading
from time import sleep
from unittest import mock

import pytest

from tamarco.core.signals import SignalsManager, signal_handler


@pytest.mark.asyncio
async def test_signal_manager(event_loop):
    signals_manager = SignalsManager()
    signals_manager.set_loop(event_loop)
    flag1 = False
    flag2 = False

    def sigalrm_handler(signum, frame):
        nonlocal flag1
        flag1 = True

    async def sigint_handler(signum, frame):
        nonlocal flag2
        flag2 = True

    def exception_handler(signum, frame):
        raise Exception

    signals_manager.register_signal(sigalrm_handler, signal.SIGALRM)
    signals_manager.register_signal(sigint_handler, signal.SIGALRM)
    signals_manager.register_signal(exception_handler, signal.SIGQUIT)

    assert sigalrm_handler == signals_manager.handlers[signal.SIGALRM][0]
    assert sigint_handler == signals_manager.handlers[signal.SIGALRM][1]
    assert exception_handler == signals_manager.handlers[signal.SIGQUIT][0]

    def use_alarm():
        signal.alarm(1)

    alarm_thread = threading.Thread(target=use_alarm, name="alarm_thread")
    alarm_thread.start()
    sleep(1.1)
    alarm_thread.join()
    assert flag1

    # Allow asyncio to execute queued tasks, in this case the asynchronous signal_number handler
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert flag2

    with mock.patch("tamarco.core.signals.logger") as mock_logger:
        signals_manager._dispatch_signal(signal.SIGQUIT, None)
        assert mock_logger.warning.called


def test_signal_handler():
    @signal_handler(signal.SIGALRM)
    def handler():
        pass

    assert handler in SignalsManager().handlers[signal.SIGALRM]
