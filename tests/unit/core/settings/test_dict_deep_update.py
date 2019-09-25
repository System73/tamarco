from tamarco.core.settings.utils import dict_deep_update


def test_dict_deep_update():
    original = {"resources": {"amqp": {"host": "127.0.0.1"}}}

    update = {"resources": {"amqp": {"port": 10000}}}

    merge = dict_deep_update(original, update)
    merge_reverse = dict_deep_update(update, original)

    for results in (merge, merge_reverse):
        assert results["resources"]["amqp"]["port"] == update["resources"]["amqp"]["port"]
        assert results["resources"]["amqp"]["host"] == original["resources"]["amqp"]["host"]
