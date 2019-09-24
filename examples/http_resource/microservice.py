# How to execute this example: see the "Examples" section in README.md

import asyncio

from sanic.response import text

from tamarco.core.microservice import Microservice, MicroserviceContext, thread
from tamarco.resources.io.http.resource import HTTPClientResource, HTTPServerResource


class HTTPMicroservice(Microservice):
    name = "http_example"
    extra_loggers_names = {name, "asyncio", "tamarco"}

    def __init__(self):
        super().__init__()
        self.settings.update_internal(
            {
                "system": {
                    "deploy_name": "test",
                    "logging": {"profile": "PRODUCTION"},
                    "resources": {"http_server": {"host": "127.0.0.1", "port": 8080, "debug": True}},
                }
            }
        )

    http_server = HTTPServerResource()

    @thread
    async def get_index_each_second(self):
        class HTTPClientContext(MicroserviceContext):
            http_client = HTTPClientResource()

        ms_context = HTTPClientContext()
        ms_context.loop = asyncio.get_event_loop()
        await ms_context.start()

        await asyncio.sleep(2)
        self.logger.info(f"Index url: http://127.0.0.1:8080/")

        while True:
            async with ms_context.http_client.session.get("http://127.0.0.1:8080/") as response:
                assert response.status == 200
                assert await response.text() == "Hello world!"
            await asyncio.sleep(1)


ms = HTTPMicroservice()


@ms.http_server.app.route("/")
async def index(request):
    print("Requested /")
    return text("Hello world!")


def main():
    ms.run()


if __name__ == "__main__":
    main()
