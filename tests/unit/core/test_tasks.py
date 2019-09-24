import asyncio
import time
from threading import current_thread

import pytest

from tamarco.core.tasks import TasksManager


@pytest.fixture
def tasks_manager(event_loop):
    tasks_manager = TasksManager()
    tasks_manager.set_loop(event_loop)

    yield tasks_manager

    tasks_manager.stop_all()


@pytest.mark.asyncio
async def test_task_handle(event_loop, tasks_manager):
    tasks_manager.task_limit = 2

    assert len(tasks_manager.tasks_coros) == 0
    assert len(tasks_manager.tasks) == 0

    async def sleeper():
        while True:
            await asyncio.sleep(0.1)

    tasks_manager.register_task(name="sleeper", task_coro=sleeper)

    assert len(tasks_manager.tasks_coros) == 1
    assert len(tasks_manager.tasks) == 0

    tasks_manager.start_all()

    assert len(tasks_manager.tasks) == 1
    assert len(tasks_manager.tasks_coros) == 0

    tasks_manager.stop_all()

    assert len(tasks_manager.tasks) == 0
    assert len(tasks_manager.tasks_coros) == 0

    await tasks_manager.wait_for_start_task(name="1", task_coro=sleeper())
    await tasks_manager.wait_for_start_task(name="2", task_coro=sleeper())
    coro = tasks_manager.wait_for_start_task(name="3", task_coro=sleeper())
    asyncio.ensure_future(coro, loop=event_loop)
    await asyncio.sleep(0.15, loop=event_loop)
    tasks_manager.stop_all()
    await asyncio.sleep(0.15, loop=event_loop)
    assert len(tasks_manager.tasks) == 1

    tasks_manager.stop_all()

    assert len(tasks_manager.tasks) == 0


@pytest.mark.asyncio
async def test_thread_handle(event_loop, tasks_manager):
    assert len(tasks_manager.threads_fns) == 0
    assert len(tasks_manager.threads) == 0

    def sleeper():
        while not current_thread().stop:
            time.sleep(0.1)

    tasks_manager.register_thread(name="sleeper", thread_fn=sleeper)

    assert len(tasks_manager.threads_fns) == 1
    assert len(tasks_manager.threads) == 0

    tasks_manager.start_all()

    assert len(tasks_manager.threads) == 1
    assert len(tasks_manager.threads_fns) == 0

    tasks_manager.stop_all()

    assert len(tasks_manager.threads) == 0
    assert len(tasks_manager.threads_fns) == 0
