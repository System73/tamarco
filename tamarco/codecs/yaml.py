import yaml

from tamarco.codecs.interface import CodecInterface


class YamlCodec(CodecInterface):
    @staticmethod
    def encode(obj):
        """Serialize a python object into a YAML stream."""
        return yaml.dump(obj)

    @staticmethod
    def decode(obj):
        """Parse the first YAML document in a stream and produce the corresponding python object."""
        return yaml.full_load(obj)
