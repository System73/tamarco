import asyncio
import inspect
import logging
import os
import platform
import sys
import threading
from pprint import pformat

import aiohttp

logger = logging.getLogger("tamarco")

ROOT_SETTINGS = "system"


def is_awaitable(obj):
    """Detect awaitable objects.

    Args:
        obj: Object to inspect.

    Returns:
        bool: True if the object is awaitable, False if not.
    """
    return asyncio.iscoroutine(obj) or hasattr(obj, "__await__")


def get_etcd_configuration_from_environment_variables() -> dict:
    """Returns the etcd configuration from the enviroment variables.

    Returns:
        dict: Etcd configuration with host and port keys.
    """
    tamarco_etcd_host = os.environ.get("TAMARCO_ETCD_HOST", None)
    tamarco_etcd_port = os.environ.get("TAMARCO_ETCD_PORT", 2379)
    if tamarco_etcd_host is None:
        return {}
    etcd_configuration = {"host": tamarco_etcd_host, "port": int(tamarco_etcd_port)}
    return etcd_configuration


def inside_a_container():
    """Detect if the process is inside a Docker container.

    Returns:
        bool: True if the microservice is running inside a docker container.
    """
    cgroups = open("/proc/1/cgroup", "r").read()
    return "docker" in cgroups


def get_fn_full_signature(fn):
    args_sig = inspect.signature(fn)
    return f"def {fn.__name__}{args_sig}"


class Informer:
    """Return information about the environment where the microservice is running."""

    @classmethod
    def log_all_info(cls, logger):
        logger.info("Information:\n" + pformat(cls.report_all_info()))

    @classmethod
    def report_all_info(cls):
        info = {}
        info.update(cls.report_os_info())
        info.update(cls.report_git_info())
        info.update(cls.report_interpreter_info())
        return info

    @staticmethod
    def report_os_info():
        return {
            "os_info": {
                "process_id": os.getpid(),
                "container_id": os.environ.get("HOSTNAME", "not_in_container"),
                "platform": platform.platform(),
            }
        }

    @staticmethod
    def report_interpreter_info():
        return {
            "python_interpreter": {
                "executable": sys.executable,
                "version": str(sys.version),
                "flags": sys.flags,
                "implementation": sys.implementation,
            }
        }

    @staticmethod
    def report_git_info():
        try:
            from git import Repo

            repo = Repo(".")
            branch = repo.active_branch
            return {
                "git": {
                    "branch": branch.name,
                    "commit": {"hash": str(branch.commit), "datetime": str(branch.commit.authored_datetime)},
                }
            }
        except ImportError:
            logger.warning("Git package is not installed, omitting version control information")
            return {}
        except Exception:
            logger.warning("Unexpected exception trying to get version control information, omitting that information")
            return {}


def set_thread_name():
    """Allow to distinguish more easily the different threads of a microservice by their name."""
    try:
        import prctl

        thread_name = threading.current_thread().name
        prctl.set_name(thread_name)
    except ImportError:
        logger.warning("Library prctl is not installed. Thread names cannot be set")
    except Exception:
        logger.warning("Unexpected exception setting the thread name for the prctl process")


class QueueTimeout(asyncio.Queue):
    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.pop("timeout", 10)
        super().__init__(*args, **kwargs)

    async def get(self):
        return await asyncio.wait_for(super().get(), self.timeout)


async def check_connection_http_url(url, loop=None, retries=3):
    if not url:
        return False
    for i in range(1, retries + 1):
        print(f"Checking connection #{i} from URL={url}")
        async with aiohttp.ClientSession(loop=loop) as client:
            try:
                async with client.get(url) as resp:
                    assert resp.status == 200
            except Exception:
                await asyncio.sleep(1)
            else:
                return True
    return False
