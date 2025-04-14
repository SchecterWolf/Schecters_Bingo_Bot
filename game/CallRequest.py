__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .Player import Player
from config.ClassLogger import ClassLogger, LogLevel
from game.Bing import Bing
from typing import Set

class CallRequest:
    __LOGGER = ClassLogger(__name__)

    def __init__(self, player: Player, requestBing: Bing):
        self.players: Set[Player] = {player}
        self.requestBing = requestBing

    def getRequesterName(self) -> str:
        return self.getPrimaryRequester().card.getCardOwner()

    def getRequesterID(self) -> int:
        return self.getPrimaryRequester().userID

    def mergeRequests(self, request: "CallRequest"):
        if not self.isMatchingRequest(request):
            CallRequest.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Cannot merge call requests of different types.\
This requests bing index is f{self.requestBing.bingIdx} and the merge's bing index is f{request.requestBing.bingIdx}")
            return

        self.players.update(request.players)

    def isMatchingRequest(self, request: "CallRequest") -> bool:
        return request.requestBing.bingIdx == self.requestBing.bingIdx

    def removePlayer(self, player: Player):
        self.players.discard(player)

    def hasPlayer(self, player: Player):
        return player in self.players

    def getPrimaryRequester(self) -> Player:
        return Player("", -1) if not self.players else next(iter(self.players))

