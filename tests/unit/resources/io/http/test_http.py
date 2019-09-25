import asyncio

import pytest
from sanic.response import HTTPResponse

from tamarco.resources.io.http.resource import HTTPCacheMiddleware, HTTPErrorCacheMiddlewareEnabled, HTTPServerResource


@pytest.mark.asyncio
async def test_http_cache_middleware_1():
    m = HTTPCacheMiddleware(maxsize=1_000_000, ttl=60)
    assert m is not None
    assert m.maxsize == 1_000_000
    assert m.ttl == 60
    assert m.maxsize == m.cache.maxsize
    assert m.ttl == m.cache.ttl


@pytest.mark.asyncio
async def test_http_cache_middleware_2():
    class RequestMock:
        url = None

    m = HTTPCacheMiddleware(maxsize=1_000_000, ttl=2)
    request = RequestMock()
    request.url = "http:127.0.0.1:9090/v1/test1"
    response = HTTPResponse()
    response.body = {"data": "datatatata"}
    response.headers = {"custom_header_name": "custom_header_value"}
    assert await m.middleware_request(request) is None
    await m.middleware_response(request, response)
    assert response.headers.get("x-cache") == "MISS"
    response_check = await m.middleware_request(request)
    assert response
    assert response_check.body == response.body
    assert response_check.headers["x-cache"] == "HIT"
    del response.headers["x-cache"]
    del response_check.headers["x-cache"]
    assert response_check.headers == response.headers
    assert response_check.status == response.status
    await asyncio.sleep(2)
    assert await m.middleware_request(request) is None


@pytest.mark.asyncio
async def test_http_cache_resource_1():
    http_resource = HTTPServerResource()

    maxsize_cache_old = http_resource.middleware_cache.maxsize
    ttl_cache_old = http_resource.middleware_cache.ttl
    http_resource.set_cache_middleware(666, 2)
    assert maxsize_cache_old != http_resource.middleware_cache.maxsize
    assert http_resource.middleware_cache.maxsize == 666
    assert ttl_cache_old != http_resource.middleware_cache.ttl
    assert http_resource.middleware_cache.ttl == 2


@pytest.mark.asyncio
async def test_http_cache_resource_2():
    http_resource = HTTPServerResource()

    try:
        http_resource.enable_cache_middleware()
    except HTTPErrorCacheMiddlewareEnabled:
        pytest.fail("Error cache middleware enabled.")
