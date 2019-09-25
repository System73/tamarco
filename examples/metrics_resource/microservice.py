# How to execute this example: see the "Examples" section in README.md

from time import sleep

from tamarco.core.microservice import Microservice, task
from tamarco.resources.basic.metrics import MetersManager
from tamarco.resources.basic.metrics.meters import Counter, Timer
from tamarco.resources.basic.metrics.reporters import FileHandler, StdoutHandler


class MetricsMicroservice(Microservice):
    name = "metrics_example"
    extra_loggers_names = {name, "asyncio", "tamarco"}

    def __init__(self):
        super().__init__()
        self.settings.update_internal({"system": {"deploy_name": "test", "logging": {"profile": "PRODUCTION"}}})
        MetersManager.configure(
            {
                "handlers": [
                    {"handler": StdoutHandler, "metric_prefix": "metric"},
                    {"handler": FileHandler, "file_path": "/tmp/metrics"},
                ],
                "collect_period": 2,
            }
        )

        MetersManager.add_handler(FileHandler("/tmp/metrics"))
        MetersManager.add_handler(StdoutHandler(metric_prefix="metric"))
        MetersManager.configure({"collect_period": 2})

    @Timer(callback=lambda time: print(f"The elapsed time is {time}"))
    @task
    async def time_me(self):
        sleep(1)

        with Timer(callback=lambda time: print(f"The inner elapsed time is {time}")):
            sleep(2)

    @task
    async def count_cows(self):
        cows_counter = Counter("cows_counter", "cow")
        cows_counter.inc()
        cows_counter.inc()

    @Counter("request_count", "request")
    @task
    async def count_requests(self):
        pass


def main():
    ms = MetricsMicroservice()
    ms.run()


if __name__ == "__main__":
    main()
