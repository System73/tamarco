import asyncio
import logging
import sys
import time
import uuid
from collections import OrderedDict
from collections.abc import Callable
from functools import partial
from threading import Thread
from typing import Coroutine, Union

from tamarco.core.dependency_resolver import CantSolveDependencies, resolve_dependency_order
from tamarco.core.logging.logging import Logging
from tamarco.core.patterns import Singleton
from tamarco.core.settings.settings import Settings, SettingsView
from tamarco.core.signals import SignalsManager
from tamarco.core.tasks import TasksManager, get_task_wrapper, get_thread_wrapper
from tamarco.core.utils import Informer, ROOT_SETTINGS, get_fn_full_signature
from tamarco.resources.bases import BaseResource
from tamarco.resources.basic.metrics.resource import MetricsResource
from tamarco.resources.basic.registry.resource import Registry
from tamarco.resources.basic.status.resource import StatusResource
from tamarco.resources.debug.profiler import ProfilerResource
from tamarco.resources.io.http.resource import HTTPServerResource

logger = logging.getLogger("tamarco")


class MicroserviceBase(metaclass=Singleton):
    # Name of the microservice, is used by the resources
    # to report a name of service.
    name = None

    # Instance id of the microservice, name is shared
    # among instances but the instance id is unique.
    instance_id = uuid.uuid4()

    # Name of the deploy, is used by the resources
    # to report a deploy name, is loaded by settings.
    deploy_name = None

    # Loggers to be added by the application code.
    extra_loggers_names = []

    # Main event loop.
    loop = asyncio.get_event_loop()

    # Manager for task.
    tasks_manager = TasksManager()

    # Settings manager.
    settings = Settings()

    # Logging manager.
    logging = Logging()

    @property
    def loggers_names(self):
        """All loggers used by the framework.

        Returns:
            list: list of loggers names used by the microservice.
        """
        loggers = {"tamarco", "tamarco.tasks", "tamarco.settings", "asyncio"}
        for resource in self.resources.values():
            loggers.update(resource.loggers_names)
        loggers.update(self.extra_loggers_names)
        loggers.update({self.name})
        return loggers

    def __new__(cls, *args, **kwargs):
        cls.resources = OrderedDict()

        dependency_graph = {
            attr_name: getattr(cls, attr_name).depends_on
            for attr_name in dir(cls)
            if isinstance(getattr(cls, attr_name), BaseResource)
        }

        try:
            resources_dep_ordered = resolve_dependency_order(dependency_graph)
        except CantSolveDependencies as e:
            print(e, file=sys.stderr)
            exit(12)
        else:
            for name in resources_dep_ordered:
                cls.resources[name] = getattr(cls, name)

        return super().__new__(cls, *args, **kwargs)

    def __init__(self):
        assert self.name is not None, "Error, name should be defined in your microservice class"
        self.logger = None
        self._configure_provisional_logger()

    def _configure_provisional_logger(self):
        """Provisional logging used before be able to read the final configuration from the settings."""
        self.logger = logging.getLogger(self.name)
        stdout_handler = logging.StreamHandler(sys.stdout)
        print(f"Configuring logger provisional logger of {self.name} to INFO and stdout")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(stdout_handler)
        self.logger.info(f"Configured {self.name} logger")

    async def bind(self):
        """Call the bind function of all the resources.
        It binds the resources to the microservice, allowing to the resources to identify their microservice.
        """
        self.logger.info(f"Binding to microservice the resources: {list(self.resources.keys())}")

        await self.settings.bind(self.loop)

        for name, resource in self.resources.items():
            try:
                await resource.bind(self, name)
            except Exception:
                self.logger.exception(f"Unexpected exception binding the resource {resource}")
                exit(11)

    async def run_in_all_resources(self, method):
        """Run the method name in all the resources.

        Args:
            method (str): Method name to run in all the resources.
        """
        for resource in self.resources.values():
            self.logger.debug(f"Calling {method} of resource {resource.name}")
            try:
                await getattr(resource, method)()
            except Exception:
                self.logger.exception(f"Error in {method} of resource {resource}")
            else:
                if method == "start":
                    self.logger.info(f"Started {resource.name} from {self.name}")

    async def start_logging(self):
        """Initializes the logging of the microservice."""
        self.logger.info(f"Starting logging in microservice {self.name} with loggers: {self.loggers_names}")
        await self.logging.start(
            loggers=self.loggers_names, microservice_name=self.name, deploy_name=self.deploy_name, loop=self.loop
        )
        Informer.log_all_info(self.logger)

    async def stop_settings(self):
        """Stops the settings of the microservice."""
        self.logger.info("Stopping microservice settings")
        await self.settings.stop()

    async def start_settings(self):
        """Initializes the settings of the microservice."""
        self.logger.info("Starting microservice settings")
        await self.settings.start()
        self.deploy_name = await self.settings.get(f"{ROOT_SETTINGS}.deploy_name")
        await self._configure_logging_settings()
        await self._configure_resource_settings()

    async def _configure_logging_settings(self):
        self.logger.info("Configuring logging settings")
        self.logging.configure_settings(SettingsView(self.settings, f"{ROOT_SETTINGS}.logging", self.name))

    async def _configure_resource_settings(self):
        self.logger.info("Configuring resources settings")
        for resource in self.resources.values():
            await resource.configure_settings(
                SettingsView(self.settings, f"{ROOT_SETTINGS}.resources.{resource.name}", self.name)
            )

    def _collect_tasks(self):
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, "_mark_task"):
                self.tasks_manager.register_task(attr._name, attr)
            elif hasattr(attr, "_mark_thread"):
                self.tasks_manager.register_thread(attr._name, attr)


class MicroserviceContext(MicroserviceBase):
    """"This class is used to use tamarco resources without using a full microservice,
    for example a script.
    """

    name = "microservice_context"

    async def start(self):
        self.tasks_manager.set_loop(self.loop)
        await self.bind()
        await self.start_settings()
        await self.start_logging()
        await self.run_in_all_resources("pre_start")
        await self.run_in_all_resources("start")
        await self.run_in_all_resources("post_start")
        self._collect_tasks()
        self.tasks_manager.start_all()

    async def stop(self):
        self.tasks_manager.stop_all()
        await self.stop_settings()
        await self.run_in_all_resources("stop")
        await self.run_in_all_resources("post_stop")


class Microservice(MicroserviceBase):
    """Main class of a microservice.
    This class is responsible for controlling the lifecycle of the microservice, also
    builds and provides the necessary elements that a resource needs to work.

    The resources of a microservice should be declared in this class. The microservice automatically takes the ownership
    of all the declared resources.
    """

    # The signals manager are responsive of handling the signal_number of the system, providing a graceful stopping in
    # the service when necessary.
    signals_manager = SignalsManager()

    # Default http server resource. It is used by the metrics and status resource to expose information.
    tamarco_http_report_server = HTTPServerResource()

    # Default metric resource.
    metrics = MetricsResource()

    # Default status resource. It is responsive of apply the restart policies and expose the status of the resources
    # an HTTP API.
    status = StatusResource()

    # Default profiler resource. It is responsive of profile de application when the setting is activated.
    profiler = ProfilerResource()

    # Default registry resource. It is responsive of maintain a etcd registry with all the alive microservice instances
    # and their IPs to be used by a discovery system.
    registry = Registry()

    def __init__(self):
        super().__init__()
        self.tasks_manager.set_loop(self.loop)
        self.signals_manager.set_loop(self.loop)

    async def pre_start(self):
        """Pre start stage of lifecycle.
        This method can be overwritten by the user to add some logic in the start.
        """
        self.logger.info("============ Pre Starting ============")
        await self.run_in_all_resources("pre_start")

    async def start(self):
        """Start stage of lifecycle.
        This method can be overwritten by the user to add some logic in the start.
        """
        self.logger.info("============ Starting ============")
        await self.run_in_all_resources("start")
        self._collect_tasks()
        self.tasks_manager.start_all()

    async def post_start(self):
        """Post start stage of lifecycle.
        This method can be overwritten by the user to add some logic in the start.
        """
        self.logger.info("============ Post Starting ============")
        await self.run_in_all_resources("post_start")

    async def stop(self):
        """Stop stage of the lifecycle.
        This method can be overwritten by the user to add some logic to the shut down.
        This method should close all the I/O operations opened by the resources.
        """
        self.logger.info("============ Stopping ============")
        await self.run_in_all_resources("stop")
        await self.stop_settings()
        self.tasks_manager.stop_all()

    async def post_stop(self):
        """Post stop stage of the lifecycle.
        This method can be overwritten by the user to add some logic to the shut down.
        """
        self.logger.info("============ Post Stopping ============")
        await self.run_in_all_resources("post_stop")

    async def _setup(self):
        await self.bind()
        await self.start_settings()
        await self.start_logging()
        await self.pre_start()
        await self.start()
        await self.post_start()

    def run(self):
        """Run a microservice.
        It initializes the main event loop of asyncio, so this function only are going to end when the microservice
        ends its live cycle.
        """
        self.logger.info(f"Running microservice {self.name}. Calling setup method")
        try:
            self.loop.run_until_complete(self._setup())
            self.loop.run_forever()
        except Exception:
            self.logger.critical(
                "Unexpected exception in the setup or during the run of the loop, stopping the " "microservice",
                exc_info=True,
            )
            self.loop.run_until_complete(self.stop_gracefully())

    async def stop_gracefully(self):
        """Stop the microservice gracefully.
        Shut down the microservice. If after 30 seconds the microservice is not closed gracefully it forces a exit.
        """

        thread = Thread(target=self._wait_and_force_exit)
        thread.start()
        await self.stop()
        await self.post_stop()
        if self.loop.is_running():
            self.loop.stop()

    def _wait_and_force_exit(self):
        time.sleep(30)
        self.logger.critical("Error stopping all the resources. Forcing exit.")
        exit(1)


def task(name_or_fn):
    """Decorator to convert a method of a microservice in a asyncio task.
    The task is started and stopped when the microservice starts and stops respectively.

    Args:
        name_or_fn: Name of the task or function. If function the task name is the declared name of the function.
    """

    def decorator(name, fn):
        wrapper = get_task_wrapper(fn, name)
        wrapper._mark_task = True
        wrapper._name = name
        return wrapper

    if name_or_fn is str:
        name = name_or_fn
        return partial(decorator, name)
    elif callable(name_or_fn):
        if not asyncio.iscoroutinefunction(name_or_fn):
            raise Exception(f"Tamarco {name_or_fn} task not created! The function is not asynchronous")
        fn = name_or_fn
        name = get_fn_full_signature(fn)
        return decorator(name, fn)
    else:
        raise Exception("task decorator should be used with a parameter (name) that is a str or without parameter")


def thread(name_or_fn):
    """Decorator to convert a method of a microservice in a thread.
    The thread is started and stopped when the microservice starts and stops respectively.

    Args:
        name_or_fn: Name of the thread or function. If function the thread name is the declared name of the function.
    """

    def decorator(name: str, fn: Callable):
        wrapper = get_thread_wrapper(fn, name)
        wrapper._mark_thread = True
        wrapper._name = name
        return wrapper

    if name_or_fn is str:
        name = name_or_fn
        return partial(decorator, name)
    elif callable(name_or_fn):
        fn = name_or_fn
        name = get_fn_full_signature(fn)
        return decorator(name, fn)
    else:
        raise Exception("task decorator should be used with a parameter (name) that is a str or without parameter")


def task_timer(interval=1000, one_shot=False, autostart=False) -> Union[Callable, Coroutine]:
    """Decorator to declare a task that should repeated in time intervals.

    Examples:
        >>> @task_timer()
        >>> async def execute(*arg,**kwargs)
        >>>     print('tick')

        >>> @task_timer(interval=1000, oneshot=True, autostart=True)
        >>> async def execute(*args,**kwargs)
        >>>     print('tick')

    Args:
        interval (int): Interval in milliseconds when the task is repeated.
        one_shot (bool): Only runs the task once.
        autostart (bool): Task is automatically initialized with the microservice.
    """

    def wrapper_task_timer(fn: Union[str, Callable]) -> Union[Callable, Coroutine]:
        """Function that adds timer functionality"""

        async def fn_with_sleep(*args, **kwargs):
            try:
                # Interval time in float (seconds transform)
                interval_seconds = interval / 1000

                # Oneshot param True always first all sleep after that execute and finish
                execute_task = autostart and not one_shot

                while True:
                    if execute_task:
                        logger.debug(
                            f"Executing task timer {fn.__name__} with the params: interval = {interval}, "
                            f"one_shot = {one_shot}, autostart = {autostart}"
                        )
                        await fn(*args, **kwargs)
                    if one_shot and execute_task:
                        break
                    execute_task = True
                    await asyncio.sleep(interval_seconds)
            except Exception:
                logger.exception(f"Unexpected exception running task timer {fn.__name__}. Timer will not recover")

        # Change name timer function with original task name
        fn_with_sleep.__name__ = fn.__name__
        return task(fn_with_sleep)

    return wrapper_task_timer
