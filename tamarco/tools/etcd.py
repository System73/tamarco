from pprint import pprint

from tamarco.core.settings.utils import parse_dir_response
from tamarco.core.settings.utils.etcd_tool import EtcdTool


def write_yml(yml_file, host="127.0.0.1", port=2379):
    """Write a yml file to etcd.

    Args:
        yml_file (str): Path to the yml file.
        host (str): Etcd host.
        port (int): Etcd port.
    """
    print(f"Writing the yml file {yml_file} in ETCD. Host: {host}. Port: {port}.")
    etcd_tool = EtcdTool(host=host, port=port)
    etcd_tool.load(yml_file)
    print("Write finished correctly.")


def read(key, recursive=True, host="127.0.0.1", port=2379):
    """Read a file or a directory in etcd.

    Args:
        key (str): Key or directory to read.
        recursive (bool): Recursive read when the key is a directory.
        host (str): Etcd host.
        port (int): Etcd port.
    """
    print(f"Reading {key} from {host}:{port}")
    etcd_tool = EtcdTool(host=host, port=port)
    response = etcd_tool.read(key=key, recursive=recursive)
    parsed_response = parse_dir_response(response, key)
    pprint(parsed_response)


def delete(key, recursive=True, host="127.0.0.1", port=2379):
    """Delete a file or a directory in etcd.

    Args:
        key (str): Key or directory to delete.
        recursive (bool): Recursive delete when the key is a directory.
        host (str): Etcd host.
        port (int): Etcd port.
    """
    print(f"Deleting {key} in {host}:{port}")
    etcd_tool = EtcdTool(host=host, port=port)
    etcd_tool.delete(key=key, recursive=recursive)
    print("Delete finished correctly.")


main = {"write_yml": write_yml, "read": read, "delete": delete}
