import sys

import pytest
import redis
from redis.exceptions import ConnectionError, TimeoutError


@pytest.fixture
def client_redis():
    redis_conf = {"host": "127.0.0.1", "port": 7006}
    try:
        conn = redis.StrictRedis(**redis_conf)
    except (ConnectionError, TimeoutError) as e:
        print(f"Error connecting to redis of logger !! {e}", file=sys.stderr)
    return conn
