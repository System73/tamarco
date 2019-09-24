redis = {"port": 7006, "host": "127.0.0.1"}

elasticsearch = ["127.0.0.1:9200", "127.0.0.1:9300"]

rabbitmq = {"host": "127.0.0.1", "port": 5677}

signaler = {"rabbitmq": {"host": "127.0.0.1", "port": 5677}, "redis": {"port": 7006, "host": "127.0.0.1"}}
