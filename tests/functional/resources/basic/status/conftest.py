import pytest

from tamarco.core.microservice import Microservice, MicroserviceContext
from tamarco.resources.basic.metrics.collector import CollectorThread
from tamarco.resources.basic.metrics.manager import MetersManager
from tamarco.resources.basic.status.resource import StatusResource
from tamarco.resources.io.http.resource import HTTPClientResource, HTTPServerResource


class StatusContext(MicroserviceContext):
    name = "test"
    status = StatusResource()
    client = HTTPClientResource()
    tamarco_http_report_server = HTTPServerResource()

    def __init__(self):
        super().__init__()
        self.settings.update_internal(
            {
                "system": {
                    "deploy_name": "test",
                    "logging": {"profile": "DEVELOP", "stdout": True},
                    "resources": {"tamarco_http_report_server": {"host": "127.0.0.1", "port": 5747, "debug": True}},
                }
            }
        )


class StatusMicroservice(Microservice):
    name = "test"
    http_server = HTTPServerResource()

    def __init__(self):
        super().__init__()
        self.settings.update_internal(
            {
                "system": {
                    "deploy_name": "test",
                    "logging": {"profile": "DEVELOP", "stdout": True},
                    "resources": {"http_server": {"host": "127.0.0.1", "port": 8080, "debug": True}},
                }
            }
        )


@pytest.fixture
def clean_meter_manager():
    MetersManager.thread = CollectorThread()


@pytest.fixture
def status_context(event_loop):
    StatusContext.loop = event_loop
    status_context = StatusContext()

    yield status_context

    event_loop.run_until_complete(status_context.stop())


@pytest.fixture
def status_microservice(event_loop):
    StatusMicroservice.loop = event_loop
    status_microservice = StatusMicroservice()

    yield status_microservice

    event_loop.run_until_complete(status_microservice.stop())
    event_loop.run_until_complete(status_microservice.post_stop())
