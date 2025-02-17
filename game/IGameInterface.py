__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .ActionData import ActionData
from .Game import Game
from .Result import Result

from abc import ABC, abstractmethod

class IGameInterface(ABC):
    def __init__(self, game: Game):
        super().__init__()
        self.game = game

    @abstractmethod
    def init(self) -> Result:
        pass

    @abstractmethod
    def destroy(self) -> Result:
        pass

    @abstractmethod
    def start(self) -> Result:
        pass

    @abstractmethod
    def stop(self) -> Result:
        pass

    @abstractmethod
    def pause(self) -> Result:
        pass

    @abstractmethod
    def resume(self) -> Result:
        pass

    @abstractmethod
    def addPlayer(self, data: ActionData) -> Result:
        pass

    @abstractmethod
    def makeCall(self, data: ActionData) -> Result:
        pass

    @abstractmethod
    def requestCall(self, data: ActionData) -> Result:
        pass

    @abstractmethod
    def deleteRequest(self, data: ActionData) -> Result:
        pass

