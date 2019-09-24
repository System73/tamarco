import ujson

from tamarco.codecs.interface import CodecInterface


class JsonCodec(CodecInterface):
    """Encodes and decode JSON objects."""

    @staticmethod
    def encode(obj):
        """Converts arbitrary object recursively into a JSON."""
        return ujson.dumps(obj)

    @staticmethod
    def decode(obj):
        """Converts a JSON string to dict object structure."""
        return ujson.loads(obj)
