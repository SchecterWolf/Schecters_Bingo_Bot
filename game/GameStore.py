__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .IGameController import IGameController
from .IGameInterface import IGameInterface

from typing import Dict, Optional

class GameStore:
    __instance = None
    __games: Dict[int, IGameInterface] = dict()
    __controller: Optional[IGameController] = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def addController(self, controller: IGameController):
        if not GameStore.__controller:
            GameStore.__controller = controller

    def getController(self) -> Optional[IGameController]:
        return GameStore.__controller

    def addGame(self, gameID: int, game: IGameInterface) -> bool:
        if GameStore.__games.get(gameID):
            return False
        GameStore.__games[gameID] = game
        return True

    def getGame(self, gameID: int) -> Optional[IGameInterface]:
        return GameStore.__games.get(gameID)

    def removeGame(self, gameID: int):
        GameStore.__games.pop(gameID, None)

