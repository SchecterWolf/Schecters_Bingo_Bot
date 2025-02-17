__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .GameGuild import GameGuild

from abc import abstractmethod
from game.ActionData import ActionData
from game.Game import Game
from game.IGameInterface import IGameInterface
from game.Result import Result

class IAsyncDiscordGame(IGameInterface):
    def __init__(self, gameGuild: GameGuild):
        super().__init__(Game())
        self.gameGuild = gameGuild

    @abstractmethod
    async def init(self) -> Result:
        pass

    @abstractmethod
    async def start(self) -> Result:
        pass

    @abstractmethod
    async def destroy(self) -> Result:
        pass

    @abstractmethod
    async def stop(self) -> Result:
        pass

    @abstractmethod
    async def pause(self) -> Result:
        pass

    @abstractmethod
    async def resume(self) -> Result:
        pass

    @abstractmethod
    async def addPlayer(self, data: ActionData) -> Result:
        pass

    @abstractmethod
    async def makeCall(self, data: ActionData) -> Result:
        pass

    @abstractmethod
    async def requestCall(self, data: ActionData) -> Result:
        pass

    @abstractmethod
    async def deleteRequest(self, data: ActionData) -> Result:
        pass

