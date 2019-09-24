import asyncio
import time

import pytest

from tamarco.core.microservice import MicroserviceContext, task, task_timer


@pytest.fixture
def yaml_settings_ms_ctx(request, event_loop, inject_in_env_settings_file_path):
    ms_ctx = MicroserviceContext()
    event_loop.run_until_complete(ms_ctx.start())
    yield ms_ctx
    event_loop.run_until_complete(ms_ctx.stop())


async def test_deploy_name_loads_from_settings():
    ms_ctx = MicroserviceContext()
    await ms_ctx.start()
    assert yaml_settings_ms_ctx.deploy_name
    assert yaml_settings_ms_ctx.deploy_name == "test_tamarco"
    await ms_ctx.stop()


class MicroserviceTestTaskContext(MicroserviceContext):
    __init_time_stamp_exec = []

    def __init__(self):
        super().__init__()
        self.time_stamp_exec = []
        self.check_pass = False
        self.settings.update_internal(
            {"system": {"deploy_name": "test", "logging": {"profile": "DEVELOP", "stdout": True}}}
        )


class TaskCheckedDecorator(MicroserviceTestTaskContext):
    """
    Class check task decorator
    """

    name = "TaskCheckedTaskDecorator"

    @task
    async def check_decorator(self):
        self.check_pass = True
        self.time_stamp_exec.append(time.time())


class TaskTimerPeriodic(MicroserviceTestTaskContext):
    """
    Class check task periodic decorator
    """

    name = "TaskTimerPeriodic"

    @task_timer(interval=500, one_shot=False, autostart=False)
    async def task_timer_periodic(self):
        self.check_pass = True
        self.time_stamp_exec.append(time.time())


class TaskExcecuteBeforePeriodicTime(MicroserviceTestTaskContext):
    """
    Class check  task periodic what execute after than periodic time
    """

    name = "TaskExcecuteBeforePeriodicTime"

    @task_timer(interval=500, one_shot=False, autostart=True)
    async def task_exec_before_periodic_time(self):
        self.check_pass = True
        self.time_stamp_exec.append(time.time())


class TaskOneShot(MicroserviceTestTaskContext):
    """
    Class check a task execute after a periodic time
    """

    name = "TaskExcecuteBeforePeriodicTime"

    @task_timer(interval=500, one_shot=True, autostart=False)
    async def task_task_one_shot(self):
        self.check_pass = True
        self.time_stamp_exec.append(time.time())


class TaskMultipleTaskAndTimerTask(MicroserviceTestTaskContext):
    """
    Class check multiple task:
        * Task
        * Periodic Task
        * Periodic One Shot
        * Periodic Task periodic before execute
    """

    name = "TaskMultipleTaskAndTimerTask"

    check_pass_one_shot = False
    time_stamp_exec_one_shot = []

    check_pass_task = False
    time_stamp_exec_task = []

    check_pass_task_periodic = False
    time_stamp_exec_task_periodic = []

    check_pass_task_execute_before_periodic = False
    time_stamp_exec_task_execute_before_periodic = []

    exception_task_times = 0

    # Task is executed after a time (1500 miliseconds)
    @task_timer(interval=1500, one_shot=True, autostart=False)
    async def task_multiple_task_one_shot(self):
        self.check_pass_one_shot = True
        self.time_stamp_exec_one_shot.append(time.time())

    # Task is executed immediately and after a period (1000 miliseconds)
    @task_timer(interval=1000, one_shot=False, autostart=True)
    async def task_multiple_task_executer_before_periodic(self):
        self.check_pass_task_execute_before_periodic = True
        self.time_stamp_exec_task_execute_before_periodic.append(time.time())

    # Task is executed according to a period (500 miliseconds)
    @task_timer(interval=500, one_shot=False, autostart=False)
    async def task_multiple_task_periodic(self):
        self.check_pass_task_periodic = True
        self.time_stamp_exec_task_periodic.append(time.time())

    # Task raises an exception and is stopped
    @task_timer(interval=1000)
    async def task_with_exception(self):
        self.exception_task_times += 1
        raise Exception

    # Normal Task
    @task
    async def task_checked_decorated(self):
        self.check_pass_task = True
        self.time_stamp_exec_task.append(time.time())


@pytest.mark.asyncio
async def test_task_checked_decorator(event_loop):
    test_microservice_task_decorator = TaskCheckedDecorator()
    test_microservice_task_decorator.loop = event_loop

    await test_microservice_task_decorator.start()
    await asyncio.sleep(1)

    # Check Test
    assert test_microservice_task_decorator.check_pass, "Not executed task correctly"
    assert len(test_microservice_task_decorator.time_stamp_exec) == 1, "Not executed once"
    await test_microservice_task_decorator.stop()


@pytest.mark.asyncio
async def test_task_timer_periodic(event_loop):
    test_microservice_periodic = TaskTimerPeriodic()
    test_microservice_periodic.loop = event_loop
    time_start = time.time()

    await test_microservice_periodic.start()
    await asyncio.sleep(1)

    # Check Test
    assert test_microservice_periodic.check_pass, "Not executed correctly timer periodic"
    assert len(test_microservice_periodic.time_stamp_exec) >= 1, "Not executed 1 times. Once periodic interval"
    assert (
        test_microservice_periodic.time_stamp_exec[0] - time_start >= 0.5
    ), "Not executed correctly because time periodic is less than interval period time"
    await test_microservice_periodic.stop()


@pytest.mark.asyncio
async def test_task_timer_periodic_excecute_before_sleep(event_loop):
    test_microservice_periodic_execute_before_sleep = TaskExcecuteBeforePeriodicTime()
    test_microservice_periodic_execute_before_sleep.loop = event_loop
    time_start = time.time()

    await test_microservice_periodic_execute_before_sleep.start()
    await asyncio.sleep(1)

    # Check Test
    assert test_microservice_periodic_execute_before_sleep.check_pass, "Not executed correctly timer periodic"
    assert (
        len(test_microservice_periodic_execute_before_sleep.time_stamp_exec) >= 2
    ), "Not executed 2 times. The start time and a periodic interval"
    assert (
        test_microservice_periodic_execute_before_sleep.time_stamp_exec[0] - time_start < 1
    ), "Not executed correctly because time execute is greater than interval "
    assert (
        not test_microservice_periodic_execute_before_sleep.time_stamp_exec[1] - time_start < 0.5
        and not test_microservice_periodic_execute_before_sleep.time_stamp_exec[1] - time_start > 3
    ), "Not executed correctly because time periodic "
    await test_microservice_periodic_execute_before_sleep.stop()


@pytest.mark.asyncio
async def test_task_timer_oneshot(event_loop):
    test_microservice_task_one_shot = TaskOneShot()
    test_microservice_task_one_shot.loop = event_loop
    time_start = time.time()

    await test_microservice_task_one_shot.start()
    await asyncio.sleep(1)

    # Check Test
    assert test_microservice_task_one_shot.check_pass, "Not executed timer correctly"
    assert len(test_microservice_task_one_shot.time_stamp_exec) == 1, "Not executed 1 times"
    assert test_microservice_task_one_shot.time_stamp_exec[0] - time_start >= 0.5, "Not executed in time correctly"
    await test_microservice_task_one_shot.stop()


@pytest.mark.asyncio
async def test_multiple_task(event_loop):
    test_microservice_multiple_task = TaskMultipleTaskAndTimerTask()
    test_microservice_multiple_task.loop = event_loop
    time_start = time.time()

    await test_microservice_multiple_task.start()
    await asyncio.sleep(4)

    assert test_microservice_multiple_task.exception_task_times, 1

    # Checked Task decorator
    assert test_microservice_multiple_task.check_pass_task, "Not executed task checked decorated"
    assert len(test_microservice_multiple_task.time_stamp_exec_task) == 1, "Not executed task checked decorated once"
    assert (
        test_microservice_multiple_task.time_stamp_exec_task[0] - time_start < 1
    ), "Not executed task checked decorated once the first"

    # Checked Task Periodic
    assert test_microservice_multiple_task.check_pass_task_periodic, "Not executed task periodic"
    assert len(test_microservice_multiple_task.time_stamp_exec_task_periodic) > 1, "Not executed task once"
    assert (
        test_microservice_multiple_task.time_stamp_exec_task_periodic[0] - time_start >= 0.5
    ), "Not executed the first"
    for i in range(1, len(test_microservice_multiple_task.time_stamp_exec_task_periodic)):
        diff_time = (
            test_microservice_multiple_task.time_stamp_exec_task_periodic[i]
            - test_microservice_multiple_task.time_stamp_exec_task_periodic[i - 1]
        )
        assert diff_time > 0.45 and diff_time < 0.65, "No correctly periocity"

    # Checked Task execute before Periodic
    assert (
        test_microservice_multiple_task.check_pass_task_execute_before_periodic
    ), "Not executed task execute before periodic"
    assert (
        len(test_microservice_multiple_task.time_stamp_exec_task_execute_before_periodic) > 1
    ), "Not executed task once"
    assert (
        test_microservice_multiple_task.time_stamp_exec_task_execute_before_periodic[0] - time_start < 1
    ), "Not executed the first"
    for i in range(1, len(test_microservice_multiple_task.time_stamp_exec_task_execute_before_periodic)):
        diff_time = (
            test_microservice_multiple_task.time_stamp_exec_task_execute_before_periodic[i]
            - test_microservice_multiple_task.time_stamp_exec_task_execute_before_periodic[i - 1]
        )
        assert diff_time > 0.95 and diff_time < 1.5, "No correctly periocity"

    # Check Task One Shot
    assert test_microservice_multiple_task.check_pass_one_shot, "Not executed task oneshot"
    assert len(test_microservice_multiple_task.time_stamp_exec_one_shot) == 1, "Not executed task once"
    assert test_microservice_multiple_task.time_stamp_exec_one_shot[0] - time_start >= 1.45, "Not executed the first"
