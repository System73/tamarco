import ast
import asyncio
from unittest import mock
from unittest.mock import Mock

import pytest
import sanic.response

from tamarco.core.microservice import Microservice
from tamarco.resources.basic.status.resource import StatusResource, get_global_status
from tamarco.resources.basic.status.status_codes import StatusCodes
from tamarco.resources.io.http.resource import HTTPServerResource
from tests.utils import AsyncMock


@pytest.fixture
def status_resource():
    status_resource = StatusResource()
    status_resource.resources_to_restart_on_failure = ["status"]
    status_resource.critical_resources = ["status"]
    return status_resource


@pytest.mark.asyncio
async def test_get_status(status_resource):
    status_response = await status_resource.status()
    assert isinstance(status_response, dict)
    assert "status" in status_response
    assert isinstance(status_response["status"], int)


@pytest.mark.parametrize(
    "resources_states,global_status",
    [
        ({"r1": {"status": StatusCodes.STARTED}, "r2": {"status": StatusCodes.STARTED, "foo": "bar"}}, 200),
        ({"r1": {"status": StatusCodes.STARTED}, "r2": {"status": StatusCodes.FAILED}}, 500),
        ({"r1": {"status": StatusCodes.STARTED}, "r2": {"status": StatusCodes.STOPPED}}, 500),
        ({"r1": {"status": StatusCodes.STOPPED}, "r2": {"status": StatusCodes.FAILED}}, 500),
        ({"r1": {"status": StatusCodes.NOT_STARTED}, "r2": {"status": StatusCodes.STARTED}}, 102),
        ({"r1": {"status": StatusCodes.CONNECTING}, "r2": {"status": StatusCodes.STARTED}}, 102),
        ({"r1": {"status": StatusCodes.NOT_STARTED}, "r2": {"status": StatusCodes.FAILED}}, 500),
        ({"r1": {"status": StatusCodes.CONNECTING}, "r2": {"status": StatusCodes.FAILED}}, 500),
        ({"r1": {"status": StatusCodes.NOT_STARTED}, "r2": {"status": StatusCodes.STOPPED}}, 500),
        ({"r1": {"status": StatusCodes.CONNECTING}, "r2": {"status": StatusCodes.STOPPED}}, 500),
        ({"r1": {"status": StatusCodes.NOT_STARTED}, "r2": {"status": StatusCodes.CONNECTING}}, 102),
    ],
)
def test_get_global_status(resources_states, global_status):
    assert get_global_status(resources_states) == global_status


@pytest.mark.asyncio
async def test_request_status_endpoint():
    from tamarco.resources.basic.status.resource import sanic_status_endpoint

    with mock.patch("sanic.request.Request") as mock_request:
        StatusResource().microservice = Mock()
        StatusResource().microservice.resources = {"http_server": HTTPServerResource()}
        response = await sanic_status_endpoint(mock_request)
        assert isinstance(response, sanic.response.HTTPResponse)
        end_response = ast.literal_eval(response.body.decode("utf-8"))
        assert "status" in end_response["http_server"]
        assert isinstance(end_response["http_server"]["status"], int)


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
                    "resources": {
                        "status": {
                            "restart_policy": {
                                "resources": {
                                    "restart_microservice_on_failure": ["http_server"],
                                    "restart_resource_on_failure": [],
                                }
                            }
                        },
                        "http_server": {"host": "127.0.0.1", "port": 8080, "debug": True},
                    },
                }
            }
        )


@pytest.mark.asyncio
async def test_check_status_with_failed_status(status_resource):
    with mock.patch(
        "tamarco.resources.basic.status.resource.StatusResource.status",
        new_callable=AsyncMock,
        return_value={"status": StatusCodes.FAILED},
    ), mock.patch("tamarco.core.microservice.Microservice.stop_gracefully", new_callable=AsyncMock) as stop_g_mock:
        status_resource.microservice = StatusMicroservice()
        await status_resource._restart_microservice_on_failure()
        stop_g_mock.assert_called()


@pytest.mark.asyncio
async def test_check_status_with_wrong_status(status_resource):
    with mock.patch(
        "tamarco.resources.basic.status.resource.StatusResource.status",
        new_callable=AsyncMock,
        return_value={"wrong": "bad_status"},
    ), mock.patch("tamarco.core.microservice.Microservice.stop_gracefully", new_callable=AsyncMock) as stop_g_mock:
        status_resource.microservice = StatusMicroservice()
        await status_resource._restart_microservice_on_failure()
        stop_g_mock.assert_called()


@pytest.mark.asyncio
async def test_stop_check_status(status_resource, event_loop):
    with mock.patch(
        "tamarco.resources.basic.status.resource.StatusResource._check_status_repeatedly", new_callable=AsyncMock
    ), mock.patch("tamarco.resources.io.http.resource.HTTPServerResource.start", new_callable=AsyncMock):
        status_task = asyncio.ensure_future(status_resource._check_status_repeatedly(), loop=event_loop)
        status_resource._status = status_resource.status_codes.STOPPED
        await asyncio.sleep(0.5)
        assert status_task.done()


@pytest.mark.asyncio
async def test_restart_resource_on_failure(status_resource):
    with mock.patch(
        "tamarco.resources.basic.status.resource.StatusResource.status",
        new_callable=AsyncMock,
        return_value={"status": StatusCodes.FAILED},
    ):
        with mock.patch(
            "tamarco.resources.basic.status.resource.StatusResource.start", new_callable=AsyncMock
        ) as start_mock:
            with mock.patch(
                "tamarco.resources.basic.status.resource.StatusResource.stop", new_callable=AsyncMock
            ) as stop_mock:
                status_resource.microservice = StatusMicroservice()
                await status_resource._restart_resource_on_failure()
                start_mock.assert_called()
                stop_mock.assert_called()
