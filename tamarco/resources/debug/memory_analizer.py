import asyncio
import datetime
import logging

import objgraph

from tamarco.core.patterns import Singleton
from tamarco.resources.bases import BaseResource

TIME_BETWEEN_SNAPSHOTS = 30


class MemoryAnalyzerResource(BaseResource, metaclass=Singleton):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("tamarco.memory_analyzer")
        self.memory_watcher_task = None

    async def start(self):
        self.logger.info(f"Starting Memory Analyzer resource")
        self.memory_watcher_task = asyncio.ensure_future(self.memory_watcher(), loop=self.microservice.loop)

    async def stop(self):
        self.logger.info(f"Stopping Memory Analyzer resource")
        self.memory_watcher_task.cancel()

    async def memory_watcher(self):
        try:
            while True:
                await self.objgraph_save()
                await asyncio.sleep(TIME_BETWEEN_SNAPSHOTS)
        except Exception:
            self.logger.warning("Unexpected exception saving objgraph object")

    async def objgraph_save(self):
        try:
            objgraph_file = open(f"/tmp/{self.microservice.name}_objgraph.log", "a")
        except Exception:
            self.logger.exception("Unexpected exception opening profile log file")
            return
        try:
            objgraph_file.write(f"\n\n###############\n# DATE : {datetime.datetime.now()}\n###############\n")
            objgraph_file.write("############### growth ###############\n")
            objgraph.show_growth(limit=50, file=objgraph_file)
        except Exception:
            self.logger.exception("Unexpected exception writing objgraph information")
        finally:
            objgraph_file.close()
