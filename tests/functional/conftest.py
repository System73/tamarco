import subprocess
from time import sleep

import pytest

from tamarco.tools.etcd import write_yml
from ..conftest import SETTINGS_FILE_PATH


def local_command(command):
    print(f"\nLaunching command: {command}")
    process = subprocess.Popen(command, shell=True)
    return_code = process.wait()
    return process, return_code


def docker_compose_up():
    print("Bringing up the docker compose")
    command = f"docker-compose up -d"
    _, return_code = local_command(command)
    if return_code != 0:
        pytest.fail(msg="Failed setting up the containers.")


def docker_compose_down():
    print("Removing all containers")
    command = f"docker-compose kill && docker-compose down"
    _, return_code = local_command(command)
    if return_code != 0:
        print("Warning: Error stopping all the containers.")
    else:
        print("Removed docker containers.")


@pytest.fixture(scope="session", autouse=True)
def docker_compose():
    docker_compose_up()
    sleep(10)
    write_yml(SETTINGS_FILE_PATH)
    yield
    docker_compose_down()
