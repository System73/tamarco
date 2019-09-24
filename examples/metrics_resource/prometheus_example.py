# How to execute this example: see the "Examples" section in README.md

import asyncio
from random import random

from tamarco.core.microservice import Microservice, task
from tamarco.resources.basic.metrics.meters import Counter, Summary


class MetricsMicroservice(Microservice):
    name = "metrics_example"
    extra_loggers_names = {name, "asyncio", "tamarco"}

    def __init__(self):
        super().__init__()
        self.settings.update_internal(
            {
                "system": {
                    "deploy_name": "test",
                    "logging": {"profile": "PRODUCTION"},
                    "resources": {
                        "metrics": {"handlers": {"prometheus": {"enabled": True}}, "collect_frequency": 1},
                        "tamarco_http_report_server": {"host": "127.0.0.1", "port": 5747, "debug": False},
                    },
                }
            }
        )

    async def post_start(self):
        await super().post_start()
        self.logger.info("See Prometheus results in: http://localhost:5747/metrics")

    @task
    async def count_me(self):
        counter_task = Counter("tasks", "calls")
        while True:
            counter_task.inc()
            await asyncio.sleep(0.5)

    @task
    async def summary(self):
        summary_test = Summary("summary", "calls")
        while True:
            summary_test.observe(random())
            await asyncio.sleep(0.1)


def main():
    ms = MetricsMicroservice()
    ms.run()


if __name__ == "__main__":
    main()
