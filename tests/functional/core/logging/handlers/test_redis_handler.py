import time
from logging import LogRecord

from tamarco.core.logging.handlers.redis import AsyncRedisHandler


def test_redis_handler(client_redis):
    handler = AsyncRedisHandler()
    for _ in range(10):
        log_record = LogRecord(
            name="test_logging_ColoredFormatter_format",
            level=1,
            pathname="test/logging",
            lineno=1,
            msg="hello world",
            args=["args1", "args2"],
            exc_info=None,
        )
        time_stamp = 1_400_000_000
        log_record.created = time_stamp
        handler.enqueue(log_record)
    time.sleep(2)
    key = client_redis.keys()[0]
    assert b'logstash' == key
    vals = client_redis.lrange(key, 0, -1)
    assert 10 == len(vals)
