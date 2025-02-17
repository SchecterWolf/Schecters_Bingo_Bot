__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from abc import ABC, abstractmethod

class IGameController(ABC):
    @abstractmethod
    def startGame(self, *args, **kwargs):
        pass

    @abstractmethod
    def stopGame(self, *args, **kwargs):
        pass
