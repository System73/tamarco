import asyncio
import logging
from functools import partial, wraps
from threading import Thread
from typing import Callable, Coroutine

from tamarco.core.utils import is_awaitable

logger = logging.getLogger("tamarco.tasks")

THREAD_STOP_TIMEOUT = 3


async def observe_exceptions(coro, name):
    """Function wrapper to observe exceptions of a coroutine in the logs.

    Args:
        coro: Coroutine to wrap with logging.
        name (str): Task name.
    """
    try:
        return await coro
    except asyncio.CancelledError:
        logger.warning(f"Tamarco task {name} cancelled")
        raise
    except Exception:
        logger.warning(f"Unexpected exception in Tamarco task {name}", exc_info=True)
        raise


def get_task_wrapper(coro_fn, name):
    """Returns a coroutine that prints unexpected exceptions to the logging.

    Args:
        coro_fn: Coroutine to wrap.
        name (str): Task name.
    """

    @wraps(coro_fn)
    async def wrapper(*args, **kwargs):
        coro = coro_fn(*args, **kwargs)
        return await observe_exceptions(coro, name)

    return wrapper


def get_thread_wrapper(target, name):
    """Returns a target thread that prints unexpected exceptions to the logging.

    Args:
        target: Func or coroutine to wrap.
        name(str): Task name.
    """

    @wraps(target)
    def wrapper(*args, **kwargs):
        try:
            result = target(*args, **kwargs)
        except Exception:
            logger.warning(f"Unexpected exception in Tamarco thread {name}", exc_info=True)
            raise
        else:
            if is_awaitable(result):
                thread_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(thread_loop)
                coro = result
                result = thread_loop.run_until_complete(observe_exceptions(coro, name))
            return result

    return wrapper


class TasksManager:
    """Helper class to handle asyncio tasks and threads.
    The class is responsible of the start and stop of the tasks/threads.
    """

    def __init__(self, task_limit=None):
        self.tasks_coros = {}
        self.threads_fns = {}
        self.tasks = {}
        self.threads = {}
        self.loop = asyncio.get_event_loop()
        self.task_limit = task_limit

    def set_loop(self, loop):
        """Sets the loop where the asyncio tasks are going to run.

        Args:
            loop: Asyncio event loop.
        """
        self.loop = loop

    def register_task(self, name, task_coro, *args, **kwargs):
        """Registers an asyncio task.

        Args:
            name (str): Name of task. For identification purposes.
            task_coro: Coroutine or function that is going to be wrapped by the task.
            *args: Arguments for the coroutine.
            **kwargs: Keywords arguments for the coroutine.
        """
        if not is_awaitable(task_coro):
            task_coro = task_coro(*args, **kwargs)
        self._register_task(name, task_coro)

    def _register_task(self, name: str, task_coro: Coroutine):
        assert name not in self.tasks_coros, f"Error, name {name} of task already taken for Tasks fns"
        assert asyncio.iscoroutine(task_coro), f"Error, Task {name} is no a coroutine"
        self.tasks_coros[name] = task_coro

    def register_thread(self, name, thread_fn, *args, **kwargs):
        """Registers a thread.

        Args:
            name (str): Name of the thread to register. It is for identification purposes.
            thread_fn: Main function of the thread.
            *args: Arguments for the thread function.
            **kwargs: Keywords arguments for the thread function.
        """
        self._register_thread(name, partial(thread_fn, *args, **kwargs))

    def _register_thread(self, name: str, thread_fn: Callable) -> None:
        assert name not in self.threads_fns, f"Error name {name} of thread already taken for Threads fns"
        self.threads_fns[name] = thread_fn

    def stop_all(self):
        """Stop all running threads and tasks."""
        self.stop_all_threads()

        for task_name in list(self.tasks.keys()):
            self.stop_task(task_name)
        self.tasks.clear()

    def start_all(self):
        """Starts all registered threads and tasks."""
        for thread_name in self.threads_fns.keys():
            self.start_thread(thread_name)
        self.threads_fns.clear()

        for task_name in self.tasks_coros.keys():
            self.start_task(task_name)
        self.tasks_coros.clear()

    def start_task(self, name, task_coro=None):
        """Start a single task.

        Args:
            name (str): Name of task. For identification purposes.
            task_coro: Coroutine or function that is going to be wrapped by the task.

        Returns:
            Asyncio future with the result of the task.
        """
        assert name not in self.tasks, f"Name {name} is already taken for a task"
        if not task_coro:
            task_coro = self.tasks_coros[name]
        logger.debug(f"Starting the task {name}")
        self.tasks[name] = asyncio.ensure_future(task_coro, loop=self.loop)
        self.tasks[name].add_done_callback(partial(self._delete_task, name))
        return self.tasks[name]

    async def wait_for_start_task(self, name, task_coro):
        """Start task waiting to open it if the number of concurrent tasks exceeds the task limit.

        Args:
            name (str): Name of task. For identification purposes.
            task_coro: Coroutine or function that is going to be wrapped by the task.

        Returns:
            Asyncio future with the result of the task.
        """
        if self.task_limit:
            while True:
                if len(self.tasks) < self.task_limit:
                    return self.start_task(name, task_coro)
                logger.debug("Limit number of coroutines reached in Tamarco task manager, waiting to open a new one")
                await asyncio.sleep(0.1, loop=self.loop)
        else:
            return self.start_task(name, task_coro)

    def _delete_task(self, name, future):
        try:
            del self.tasks[name]
        except KeyError:
            logger.debug(f"Task {name} was already removed from the task manager when the done callback is called")

    def start_thread(self, name) -> Thread:
        """Start a thread by name.

        Args:
            name(str): Thread name. For identification purposes.

        Returns:
            Thread: Thread object.
        """
        assert name not in self.threads, f"Name {name} is already taken for a task"
        logger.debug(f"Starting the thread {name}")
        self.threads[name] = Thread(target=self.threads_fns[name], name=name)
        self.threads[name].stop = False
        self.threads[name].start()
        return self.threads[name]

    def stop_all_threads(self):
        """Stop all threads."""
        for name, thread in self.threads.items():
            logger.debug(f"Stopping thread {name}")
            thread.stop = True

        for name, thread in self.threads.items():
            self._join_thread(name, thread)

        self.threads.clear()

    def stop_task(self, name):
        """Stop a task by name.

        Args:
            name (str): Name of task. For identification purposes.
        """
        logger.debug(f"Stopping the task {name}")
        self.tasks[name].cancel()
        del self.tasks[name]

    def stop_thread(self, name):
        """Stop a thread by name.

        Args:
            name(str): Thread name. For identification purposes.
        """
        thread = self.threads[name]
        logger.debug(f"Stopping the thread {name}")
        thread.stop = True
        self._join_thread(name, thread)
        del self.threads[name]

    @staticmethod
    def _join_thread(name: str, thread) -> None:
        thread.join(timeout=THREAD_STOP_TIMEOUT)
        if thread.is_alive():
            logger.warning(f"Trying to stop thread {name}, but did not join")
        else:
            logger.debug(f"Stopped thread {name}")
