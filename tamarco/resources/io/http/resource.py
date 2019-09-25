import asyncio
import copy
import logging
from collections import OrderedDict

import aiohttp
import ujson as json
from cachetools import TTLCache
from sanic import Sanic
from sanic_cors import CORS

from tamarco.core.settings.settings import SettingNotFound
from tamarco.resources.bases import BaseResource
from tamarco.resources.basic.status.status_codes import StatusCodes


class HTTPErrorCacheMiddlewareEnabled(Exception):
    pass


class HTTPCacheMiddleware:
    def __init__(self, maxsize=1_000, ttl=60, header_keys=None):
        """
        Args:
            maxsize (int): Cache max size.
            ttl (int): Time To Live of the keys in the cache.
            header_keys (header_keys): List of the headers that will be part of the cache key.
        """
        self.cache = TTLCache(maxsize, ttl)
        self.maxsize = maxsize
        self.ttl = ttl
        self.header_keys = header_keys if isinstance(header_keys, list) else []

    def _get_cache_key(self, request):
        headers = self._get_json_headers(request)
        return request.url + headers

    async def middleware_request(self, request):
        """
        Args:
            request (Request): Request to intercept.
        """
        cache_key = self._get_cache_key(request)
        try:
            response = copy.deepcopy(self.cache[cache_key])
        except KeyError:
            return
        response.headers["x-cache"] = "HIT"
        return response

    async def middleware_response(self, request, response):
        """
        Args:
            request (Request): Request to intercept.
            response (HTTPResponse): Response to intercept.
        """
        if "x-cache" not in response.headers:
            response.headers["x-cache"] = "MISS"
            cache_key = self._get_cache_key(request)
            self.cache[cache_key] = copy.deepcopy(response)

    def _get_json_headers(self, request):
        """
        Args:
            request (Request): Request to intercept.
        """
        if not self.header_keys:
            return ""

        header_dict = {}
        for key in self.header_keys:
            header_dict[key] = request.headers.get(key)
        ordered_dict = OrderedDict(sorted(header_dict.items()))
        return json.dumps(ordered_dict)


class HTTPServerResource(BaseResource):
    depends_on = []
    loggers_names = ["tamarco.http"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = Sanic("http_app", log_config=None)
        CORS(
            self.app,
            automatic_options=True,
            origins="*",
            supports_credentials=True,
            methods=["GET", "POST", "PATCH", "PUT", "DELETE", "HEAD", "OPTIONS"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "Accept",
                "Origin",
                "User-Agent",
                "DNT",
                "Cache-Control",
                "X-Mx-ReqToken",
                "Keep-Alive",
                "X-Requested-With",
                "If-Modified-Since",
            ],
        )
        self.logger = logging.getLogger("tamarco.http")
        self._server_task = None
        self.status_codes = StatusCodes
        self.middleware_cache = HTTPCacheMiddleware()

    def set_cache_middleware(self, maxsize=None, ttl=None, header_keys=None):
        if maxsize is not None and maxsize != self.middleware_cache.maxsize:
            self.middleware_cache.maxsize = maxsize

        if ttl is not None and ttl != self.middleware_cache.ttl:
            self.middleware_cache.ttl = ttl

        if header_keys:
            self.middleware_cache.header_keys = header_keys

        self.middleware_cache = HTTPCacheMiddleware(
            self.middleware_cache.maxsize, self.middleware_cache.ttl, self.middleware_cache.header_keys
        )

    def enable_cache_middleware(self):
        try:
            self.app.middleware("request")(self.middleware_cache.middleware_request)
            self.app.middleware("response")(self.middleware_cache.middleware_response)
        except Exception:
            self.logger.warning("Unexpected exception enabling cache in HTTP Server resource", exc_info=True)
            raise HTTPErrorCacheMiddlewareEnabled()

    async def start(self):
        self.app.config.KEEP_ALIVE = await self.settings.get("keep_alive_connections", False)
        try:
            self._server_task = asyncio.ensure_future(
                self.app.create_server(
                    host=await self.settings.get("host"),
                    port=await self.settings.get("port"),
                    debug=await self.settings.get("debug"),
                    return_asyncio_server=True,
                ),
                loop=self.microservice.loop,
            )

            cache_enabled = await self.settings.get("cache_enabled", False)
            if cache_enabled:
                maxsize = await self.settings.get("cache_maxsize", None)
                ttl = await self.settings.get("cache_ttl", None)
                header_keys = await self.settings.get("cache_header_keys", None)
                self.set_cache_middleware(maxsize, ttl, header_keys)
                self.enable_cache_middleware()
        except SettingNotFound:
            self.logger.error("The HTTP Server resource settings are missing")
        await super().start()

    def add_endpoint(self, uri, endpoint_handler):
        """
        Args:
            uri (str): Uri of the endpoint.
            endpoint_handler: Handler of the endpoint.
        """
        self.app.route(uri)(endpoint_handler)

    async def stop(self):
        self.logger.info(f"Stopping HTTP Server resource: {self.name}")
        self._status = StatusCodes.STOPPING
        if self._server_task is not None:
            self._server_task.cancel()
        await super().stop()

    async def status(self):
        return {"status": self.status_codes.STARTED}


class HTTPClientResource(BaseResource):
    depends_on = []
    loggers_names = ["tamarco.http"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("tamarco.http")
        self.session = None
        self.status_codes = StatusCodes

    async def start(self):
        self.session = aiohttp.ClientSession(loop=self.microservice.loop)
        await super().start()

    async def stop(self):
        self.logger.info(f"Stopping HTTP Client resource: {self.name}")
        await self.session.close()
        await super().stop()

    async def status(self):
        return {"status": self.status_codes.STARTED}
