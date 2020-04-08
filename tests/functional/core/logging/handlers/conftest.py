import pytest
import redis


@pytest.fixture
def client_redis():
    redis_conf = {"host": "127.0.0.1", "port": 7006}
    return redis.StrictRedis(**redis_conf)
