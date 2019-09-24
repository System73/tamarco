import logging

import etcd
import ujson
import yaml


class EtcdTool:
    """Utility to load settings to an etcd server from a yml file source.

    Unlike the rest of Tamarco it is based in a syncronous library because it is designed to be used as utility
    from the command line or testing.
    """

    def __init__(self, host="127.0.0.1", port=2379, protocol="https", encode=None):
        """
        Args:
            host (str): Etcd host.
            port (int): Etcd port.
            protocol (str): Protocol to use with the etcd server.
            encode (str): Json to encode the values with a json encoder.
        """
        self.client = etcd.Client(host, port, protocol)
        self.encode = encode

    def write(self, key, value):
        """Set one etcd key with the value.

        Args:
            key (str): Path to the setting.
            value: Key value.
        """
        try:
            if self.encode == "json":
                value = ujson.dumps(value)
            self.client.write(key, value)
        except Exception:
            logging.error(f"Error writing key {key} to etcd.")
            raise

    def read(self, key, recursive=False, value=False):
        """Read data from etcd.

        Args:
            key (str): Path to the setting.
            recursive (bool): Read recursively a etcd directory.
            value (bool): Get the value

        Returns:
            Etcd value or directory structure.
        """
        try:
            if value:
                response = self.client.read(key, recursive=False).value
            else:
                return self.client.read(key, recursive=recursive)

            if self.encode == "json":
                return ujson.loads(response)
            return response
        except Exception:
            logging.error(f"Error reading key {key}.")
            raise

    def delete(self, key, recursive=False):
        """Delete one key in etcd.

        Args:
            key (str): Path to the setting.
            recursive (bool): Delete recursively a etcd directory.
        """
        try:
            self.client.delete(key, recursive=recursive)
        except Exception:
            logging.error(f"Error deleting key {key}.")
            raise

    def load_items(self, yml_dictionary, path=""):
        """Write a dictionary recursively in a certain path of etcd.

        Args:
            yml_dictionary (dict): dictionary that represents the settings to load in etcd.
            path (str): path where to write the yml_dictionary.
        """
        for key, value in yml_dictionary.items():
            new_path = path + "/" + key
            if isinstance(value, dict):
                self.load_items(value, new_path)
            else:
                if self.encode == "json":
                    value = ujson.dumps(value)
                self.write(new_path, value)

    def load(self, yml_file):
        """Load and convert a yml file to a dictionary then it saves the dictionary in etcd, mapping the dictionary's
        keys to settings paths.

        Args:
            yml_file (str): path the the yml file to read.
        """
        logging.info(f"Loading file: {yml_file}")
        try:
            yml_dictionary = yaml.full_load(open(yml_file))
            self.load_items(yml_dictionary)
        except Exception:
            logging.error(f"Error reading file {yml_file}.")
            raise
