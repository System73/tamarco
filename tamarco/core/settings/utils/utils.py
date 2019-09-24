import ujson


def format_key_to_etcd(key):
    """Format a dot based key as a etcd key.

    Args:
        key (str): Path to the setting.

    Returns:
        str: Formatted key.
    """
    return "/" + key.replace(".", "/")


def _format_key_from_etcd(queried_key, response_key):
    """Format a key from etcd format to a subkey in dotted format."""
    queried_key = format_key_to_etcd(queried_key)
    key = response_key.replace(queried_key, "", 1)
    if key.startswith("/"):
        key = key[1:]
    return key


def parse_dir_response(response, queried_key):
    """Parse a response that is a dir to a python dict.

    Args:
        response: Etcd response.
        queried_key: Key of the query in the etcd response.

    Returns:
        dict: Dictionary with the parsed response.
    """
    setting = {}
    for result in response.children:
        if result.value is None:
            break
        if result.dir:
            setting.update({_format_key_from_etcd(queried_key, result.key): parse_dir_response(result, queried_key)})
        else:
            sub_key = _format_key_from_etcd(queried_key, result.key)
            if "/" in sub_key:
                sub_keys = sub_key.split("/")[:-1]
                last_key = sub_key.split("/")[-1:][0]
                sub_setting = setting
                for key in sub_keys:
                    sub_setting[key] = sub_setting.get(key, {})
                    sub_setting = sub_setting[key]
                sub_setting.update({last_key: ujson.loads(result.value)})
            else:
                setting.update({sub_key: ujson.loads(result.value)})
    return setting


def dict_deep_update(target, update):
    """Recursively update a dict. Subdict's won't be overwritten but also updated.

    Args:
        target: Target dictionary to update.
        update: Parameters to update.
    Returns:
        dict: Updated dictionary.
    """
    for key, value in update.items():
        if key not in target:
            target[key] = value
        elif isinstance(value, dict):
            target[key] = dict_deep_update(value, target[key])
    return target
