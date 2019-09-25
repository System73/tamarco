import asyncio
from unittest import mock

import pytest

from tamarco.resources.basic.status.status_codes import StatusCodes
from tests.utils import AsyncMock


@pytest.mark.asyncio
async def test_status_resource(status_context):
    await status_context.start()
    await asyncio.sleep(1)
    url = "http://127.0.0.1:5747/status"

    async with status_context.client.session.get(url) as response:
        assert response.status == 200
        response = await response.json()
        assert "status" in response
        assert "status" in response["status"]
        assert isinstance(response["status"]["status"], int)


@pytest.mark.asyncio
async def test_check_status(event_loop, clean_meter_manager, status_microservice):
    status_codes = StatusCodes
    with mock.patch(
        "tamarco.core.microservice.Microservice.stop_gracefully", new_callable=AsyncMock
    ) as stop_gracefully_mock, mock.patch(
        "tamarco.resources.basic.status.resource.StatusResource.status",
        return_value={"status": status_codes.FAILED},
        new_callable=AsyncMock,
    ):

        stop_gracefully_mock._name = "stop_gracefully_mock"

        asyncio.ensure_future(status_microservice._setup())

        await asyncio.sleep(0.3)
        stop_gracefully_mock.assert_called()
