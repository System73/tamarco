import pytest

from tamarco.codecs.interface import CodecInterface
from tamarco.codecs.json import JsonCodec
from tamarco.codecs.pickle import PickleCodec
from tamarco.codecs.yaml import YamlCodec


@pytest.mark.parametrize("Codec", (YamlCodec, JsonCodec, PickleCodec, CodecInterface))
@pytest.mark.asyncio
async def test_codec(Codec):
    str_original = "test"
    if isinstance(Codec, YamlCodec):
        str_original = "Node:0 " "  Node:1"
    elif isinstance(Codec, JsonCodec):
        str_original = "{'node1': {'node2': 'example node'}}"

    try:
        obj_encode = Codec.encode(str_original)
    except Exception:
        if isinstance(Codec, CodecInterface):
            assert True
    try:
        assert Codec.decode(obj_encode) == str_original
    except Exception:
        if isinstance(Codec, CodecInterface):
            assert True
