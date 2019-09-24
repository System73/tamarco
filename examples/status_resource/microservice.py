# How to execute this example: see the "Examples" section in README.md

import asyncio

from tamarco.core.microservice import Microservice, MicroserviceContext, task
from tamarco.resources.io.http.resource import HTTPClientResource, HTTPServerResource


class HTTPClientContext(MicroserviceContext):
    http_client = HTTPClientResource()


class StatusMicroservice(Microservice):
    name = "status_example"
    extra_loggers_names = {name, "asyncio", "tamarco"}
    http_server = HTTPServerResource()

    def __init__(self):
        super().__init__()
        self.settings.update_internal(
            {
                "system": {
                    "deploy_name": "test",
                    "logging": {"profile": "PRODUCTION"},
                    "resources": {
                        "tamarco_http_report_server": {"host": "127.0.0.1", "port": 5747, "debug": False},
                        "http_server": {"host": "127.0.0.1", "port": 8080, "debug": True},
                    },
                }
            }
        )

    @task
    async def get_status_each_second(self):
        ms_context = HTTPClientContext()
        ms_context.loop = asyncio.get_event_loop()
        await ms_context.start()
        await asyncio.sleep(1)

        while True:
            await asyncio.sleep(1)

            async with ms_context.http_client.session.get("http://127.0.0.1:5747/status") as response:
                self.logger.info("Requested http://127.0.0.1:5747/status")
                assert response.status == 200
                response = await response.json()
                self.logger.info(f"Response: {response}")
                assert type(response) == dict


def main():
    ms = StatusMicroservice()
    ms.run()


if __name__ == "__main__":
    main()
