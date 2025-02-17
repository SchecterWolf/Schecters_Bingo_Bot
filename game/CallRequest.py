__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .Player import Player
from config.ClassLogger import ClassLogger
from config.Log import LogLevel
from game.Bing import Bing

class CallRequest:
    __LOGGER = ClassLogger(__name__)

    def __init__(self, player: Player, requestBing: Bing):
        self.players = [player]
        self.requestBing = requestBing

    def getRequesterName(self) -> str:
        return "" if not self.players else self.players[0].card.getCardOwner()

    def mergeRequests(self, request: "CallRequest"):
        if not self.isMatchingRequest(request):
            CallRequest.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Cannot merge call requests of different types.\
This requests bing index is f{self.requestBing.bingIdx} and the merge's bing index is f{request.requestBing.bingIdx}")
            return

        self.players.extend(request.players)

    def isMatchingRequest(self, request: "CallRequest") -> bool:
        return request.requestBing.bingIdx == self.requestBing.bingIdx

