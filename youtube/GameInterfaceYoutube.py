__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .ChatInterface import ChatInterface
from .ChatProcessor import ChatProcessor

from config.ClassLogger import ClassLogger
from config.Config import Config
from config.Globals import GLOBALVARS
from config.Log import LogLevel

from game.ActionData import ActionData
from game.Bing import Bing
from game.Binglets import Binglets
from game.CallRequest import CallRequest
from game.Game import Game
from game.IGameInterface import IGameInterface
from game.Result import Result

# TODO SCH Have an independent loop listen for the '/bingo' command that prints out how to join the game
class GameInterfaceYoutube(IGameInterface):
    __LOGGER = ClassLogger(__name__)

    def __init__(self):
        super().__init__(Game())
        self.chatIface = ChatInterface()
        self.chatProcessor = ChatProcessor(self.chatIface)

    def init(self) -> Result:
        self.chatIface.init()
        self.chatProcessor.init()
        return Result(True)

    def destroy(self) -> Result:
        return Result(True)

    def start(self) -> Result:
        GameInterfaceYoutube.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Sending start message to yt livestream.")
        message = Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_STARTED)
        message += f" {GLOBALVARS.GAME_MSG_JOIN}"
        ret = self.chatIface.sendMessage(message) and\
                self.chatIface.sendMessage(GLOBALVARS.GAME_NIGHTBOT_CMD_DISCORD)

        return Result(ret)

    def stop(self) -> Result:
        GameInterfaceYoutube.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Sending stop message to yt livestream.")
        ret = self.chatIface.sendMessage(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_ENDED))
        return Result(ret)

    def pause(self) -> Result:
        GameInterfaceYoutube.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Sending pause message to yt livestream.")
        ret = self.chatIface.sendMessage(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_PAUSED))
        return Result(ret)

    def resume(self) -> Result:
        GameInterfaceYoutube.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Sending resume message to yt livestream.")
        ret = self.chatIface.sendMessage(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_RESUMED))
        return Result(ret)

    def addPlayer(self, data: ActionData) -> Result:
        GameInterfaceYoutube.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Sending add player message to yt livestream.")
        displayName: str = data.get("displayName")
        ret = self.chatIface.sendMessage(f"Player \"{displayName}\" has joined the livestream bingo!")
        return Result(ret)

    def makeCall(self, data: ActionData) -> Result:
        GameInterfaceYoutube.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Sending make call message to yt livestream.")
        ret = Result(False)
        index: int = data.get("index")
        newPlayerCalls: str = data.get("newPlayerCalls")
        newPlayerBingos: str = data.get("newPlayerBingos")
        bing: Bing = Binglets().getBingFromIndex(index)

        if not bing:
            ret.responseMsg = f"Could not locate bing for index {index}"
            return ret

        ret.result = self.chatIface.sendMessage(f"Slot called: {bing.bingStr}")
        if newPlayerBingos:
            ret.result = ret.result and self.chatIface.sendMessage(newPlayerCalls)
        if newPlayerBingos:
            ret.result = ret.result and self.chatIface.sendMessage(newPlayerBingos)

        return ret

    def requestCall(self, data: ActionData) -> Result:
        callRequest: CallRequest = data.get("callRequest")
        self.chatProcessor.addCallRequest(callRequest)
        return Result(True)

    def deleteRequest(self, _: ActionData) -> Result:
        """No stream message for delete requests"""
        return Result(False)

