class CodecInterface:
    """The interface that all Tamarco codecs must implement."""

    @staticmethod
    def encode(obj):
        raise NotImplementedError

    @staticmethod
    def decode(obj):
        raise NotImplementedError
