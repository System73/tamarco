import asyncio
import logging

from sanic.response import json

from tamarco.core.patterns import Singleton
from tamarco.resources.bases import BaseResource
from tamarco.resources.basic.status.status_codes import StatusCodes
from .settings import STATUS_HTTP_ENDPOINT

logger = logging.getLogger("tamarco.status")

PERIOD_BETWEEN_CHECKS = 1


def get_global_status(status):
    """
    Taking into account all the resources states of the microservice:
            a. Return HTTP 200 if all the resources are in the status STARTED.
            b. Return HTTP 500 if any resource is in the state STOPPED or FAILED.
            c. Return HTTP 102 otherwise.

    Args:
        status (dict): all resources with a dict where we can get their values status.

    Returns:
        int: global status
    """
    status_list = []
    status_dict_values = status.values()
    for status_values in status_dict_values:
        try:
            status_list.append(status_values["status"])
        except Exception:
            logger.warning("Could not get the status of one particular resource", exc_info=True)

    if all(StatusCodes.STARTED == status for status in status_list):  # if status_list is empty => True
        return 200
    if any(StatusCodes.STOPPED == status or StatusCodes.FAILED == status for status in status_list):
        return 500
    return 102


async def sanic_status_endpoint(request):
    response = {}
    status = StatusResource()
    for name, resource in status.microservice.resources.items():
        response[name] = await resource.status()
    status = get_global_status(response)
    return json(body=response, status=status)


class StatusResource(BaseResource, metaclass=Singleton):
    """ """

    depends_on = ["tamarco_http_report_server"]
    loggers_names = ["tamarco.status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger
        self.status_codes = StatusCodes
        self.critical_resources = []
        self.resources_to_restart_on_failure = []

    async def status(self):
        return {"status": self.status_codes.STARTED, "status_str": "STARTED"}

    async def start(self):
        await super().start()
        self.microservice.tamarco_http_report_server.add_endpoint(
            uri=STATUS_HTTP_ENDPOINT, endpoint_handler=sanic_status_endpoint
        )
        self.critical_resources = await self.settings.get(
            "restart_policy.resources.restart_microservice_on_failure", []
        )
        self.resources_to_restart_on_failure = await self.settings.get(
            "restart_policy.resources.restart_resource_on_failure", []
        )
        asyncio.ensure_future(self._check_status_repeatedly())

    async def stop(self):
        self.logger.info(f"Stopping Status resource: {self.name}")
        await super().stop()

    async def _check_status_repeatedly(self):
        while self._status == self.status_codes.STARTED:
            await asyncio.sleep(PERIOD_BETWEEN_CHECKS)
            await self._check_status()

    async def _check_status(self):
        await self._restart_microservice_on_failure()
        await self._restart_resource_on_failure()

    async def _restart_microservice_on_failure(self):
        for name, resource in self.microservice.resources.items():
            if name in self.critical_resources or "all" in self.critical_resources:
                status_response = await resource.status()
                try:
                    if status_response["status"] == StatusCodes.FAILED:
                        logger.critical(
                            f"{name} resource has a failed status. Closing microservice " f"{self.microservice.name}"
                        )
                        await self.microservice.stop_gracefully()
                        break
                except KeyError:
                    logger.critical(
                        f"{name} resource has an unknown status. Closing microservice {self.microservice.name}",
                        exc_info=True,
                    )
                    await self.microservice.stop_gracefully()
                    break

    async def _restart_resource_on_failure(self):
        for name, resource in self.microservice.resources.items():
            if name in self.resources_to_restart_on_failure or "all" in self.resources_to_restart_on_failure:
                status_response = await resource.status()
                try:
                    if status_response["status"] == StatusCodes.FAILED:
                        await resource.stop()
                        await resource.start()
                except KeyError:
                    logger.error(f"Resource {name} reporting wrong its status")
                except Exception:
                    logger.error(f"Unknown exception, restarting the resource {name}. Closing microservice")
                    self.microservice.stop_gracefully()
