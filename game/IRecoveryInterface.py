__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from abc import ABC, abstractmethod

class IRecoveryInterface(ABC):
    @abstractmethod
    def getGameID(self) -> int:
        pass

    @abstractmethod
    def hasRecovery(self) -> bool:
        pass

    @abstractmethod
    def removeRecovery(self):
        pass

    @abstractmethod
    def updateRecovery(self, game):
        pass

    # TODO Even though python doesn't strictly require the return types to match, I still don't like
    # that the iface can't specify the return type with a circular dependency.
    # Ideally, I would make an iface for the game object as well... maybe in the future I'll do that
    # as well.
    @abstractmethod
    def recoverGame(self, stats):
        pass
