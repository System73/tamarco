from tamarco.core.microservice import MicroserviceContext
from tamarco.resources.io.http.resource import HTTPClientResource, HTTPServerResource


class HTTPContext(MicroserviceContext):
    name = "test"

    def __init__(self):
        super().__init__()
        self.settings.update_internal(
            {
                "system": {
                    "deploy_name": "test",
                    "logging": {"profile": "DEVELOP", "stdout": True},
                    "resources": {
                        "server": {"host": "127.0.0.1", "port": 8080, "debug": True, "keep_alive_connections": False}
                    },
                }
            }
        )

    server = HTTPServerResource()
    client = HTTPClientResource()
