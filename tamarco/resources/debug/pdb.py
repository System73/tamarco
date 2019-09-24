import pdb
import signal

from tamarco.core.microservice import Microservice
from tamarco.core.patterns import Singleton
from tamarco.resources.bases import BaseResource

START_PDB_SIGNAL = signal.SIGUSR1


class PdbResource(BaseResource, metaclass=Singleton):
    async def bind(self, microservice: Microservice, name: str) -> None:
        super().bind(microservice, name)
        microservice.signals_manager.register_signal(START_PDB_SIGNAL, self.start_pdb)

    @staticmethod
    def start_pdb():
        pdb.set_trace()
