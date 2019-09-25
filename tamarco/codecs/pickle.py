import pickle

from tamarco.codecs.interface import CodecInterface


class PickleCodec(CodecInterface):
    """Encodes and decode pickle objects."""

    @staticmethod
    def encode(obj):
        """Return the pickled representation of obj as a bytes object."""
        return pickle.dumps(obj)

    @staticmethod
    def decode(obj):
        """Read a pickled object hierarchy from obj (bytes) and return the pickled representation."""
        return pickle.loads(obj)
