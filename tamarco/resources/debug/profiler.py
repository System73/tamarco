import asyncio
import datetime
import logging
import pstats
from cProfile import Profile

from tamarco.core.settings.settings import SettingNotFound
from tamarco.resources.bases import BaseResource
from .config import TIME_BETWEEN_SNAPSHOTS


class ProfilerResource(BaseResource):

    loggers_names = ["tamarco.profiler"]

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger("tamarco.profiler")
        self.profiler = None
        self.profiler_file_path = None
        self.cpu_watcher_task = None

        super().__init__(*args, **kwargs)

    async def start(self):
        if await self.is_profiler_enabled():
            self.profiler_file_path = f"/tmp/{self.microservice.name}_profile"
            self._initialize_profiler()
            self.logger.info(
                f"Started Profiler resource with file: {self.profiler_file_path} and "
                f"time between snapshots: {TIME_BETWEEN_SNAPSHOTS}"
            )
            self.cpu_watcher_task = asyncio.ensure_future(self.cpu_watcher(), loop=self.microservice.loop)
        else:
            self.logger.debug("Profiler resource disabled")
        await super().start()

    async def stop(self):
        if self.profiler:
            self._stop_profiler()
        if self.cpu_watcher_task:
            self.cpu_watcher_task.cancel()
        await super().stop()

    def _initialize_profiler(self):
        self.profiler = Profile()
        self.profiler.enable()

    def _stop_profiler(self):
        assert self.profiler, "Trying to stop a profiler when it isn't initialized"
        self.profiler.disable()
        self.profiler = None

    def _restart_profiler(self):
        self._stop_profiler()
        self._initialize_profiler()

    async def is_profiler_enabled(self) -> bool:
        try:
            microservices_with_profiler = await self.settings.get("microservices_with_profiler")
        except SettingNotFound:
            return False
        else:
            return self.microservice.name in microservices_with_profiler

    async def cpu_watcher(self):
        while True:
            await asyncio.sleep(TIME_BETWEEN_SNAPSHOTS)
            self.save_profile_snapshot_to_file()

    def save_profile_snapshot_to_file(self):
        try:
            with open(self.profiler_file_path, "a") as profile_file:
                self.logger.debug(f"Opened profile file {self.profiler_file_path}. Saving profile information")
                profile_file.write(f"\n\n###############\n# DATE : {datetime.datetime.now()}\n###############\n")

                stats = pstats.Stats(self.profiler, stream=profile_file)
                stats.sort_stats("tottime")
                stats.print_stats(100)

                self._restart_profiler()
        except Exception:
            self.logger.warning("Unexpected exception saving profile information")
