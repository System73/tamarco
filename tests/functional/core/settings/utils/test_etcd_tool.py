from os import path

from tamarco.core.settings.utils.etcd_tool import EtcdTool


def test_add_key():
    response_dict = {}

    client = EtcdTool(host="127.0.0.1")
    client.write(key="/added_key", value="added value")

    response = client.read("/", recursive=True)

    for result in response.children:
        response_dict[result.key] = result.value

    assert response_dict["/added_key"] == "added value"


def test_delete_key():
    response_dict = {}
    client = EtcdTool(host="127.0.0.1")

    client.write(key="/added_key_1", value="added value 1")
    client.write(key="/added_key_2", value="added value 2")

    client.delete(key="/added_key_1")

    response = client.read("/", recursive=True)

    for result in response.children:
        response_dict[result.key] = result.value

    assert "/added_key_1" not in response_dict
    assert response_dict["/added_key_2"] == "added value 2"


def test_load_file():
    response_dict = {}
    test_folder = path.abspath(path.join(__file__, ".."))
    setting_file = "settings.yml"
    settings = test_folder + "/" + setting_file
    client = EtcdTool(host="127.0.0.1")
    client.load(settings)

    response = client.read("/", recursive=True)

    for result in response.children:
        response_dict[result.key] = result.value

    assert response_dict["/key_1"] == "1000"
    assert response_dict["/key_2"] == "1000"
    assert response_dict["/key_3"] == "1000.0"
    assert response_dict["/key_4"] == "1000.0"
    assert response_dict["/key_5"] == "1000"
    assert response_dict["/key_6"] == "Yes"
    assert response_dict["/key_7"] == "True"

    assert response_dict["/one_level/key_1"] == "1000"
    assert response_dict["/one_level/key_2"] == "1000"
    assert response_dict["/one_level/key_3"] == "1000.0"
    assert response_dict["/one_level/key_4"] == "1000.0"
    assert response_dict["/one_level/key_5"] == "1000"
    assert response_dict["/one_level/key_6"] == "Yes"
    assert response_dict["/one_level/key_7"] == "True"

    assert response_dict["/two_levels/intermediate_level/key_1"] == "1000"
    assert response_dict["/two_levels/intermediate_level/key_2"] == "1000"
    assert response_dict["/two_levels/intermediate_level/key_3"] == "1000.0"
    assert response_dict["/two_levels/intermediate_level/key_4"] == "1000.0"
    assert response_dict["/two_levels/intermediate_level/key_5"] == "1000"
    assert response_dict["/two_levels/intermediate_level/key_6"] == "Yes"
    assert response_dict["/two_levels/intermediate_level/key_7"] == "True"
