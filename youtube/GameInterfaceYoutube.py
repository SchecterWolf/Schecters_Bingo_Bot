__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .ChatInterface import ChatInterface
from .ChatProcessor import ChatProcessor

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS

from game.ActionData import ActionData
from game.Bing import Bing
from game.Binglets import Binglets
from game.CallRequest import CallRequest
from game.IGameInterface import IGameInterface
from game.Result import Result

class GameInterfaceYoutube(IGameInterface):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, game: IGameInterface):
        super().__init__(game.game)
        self.gameIface = game
        self.chatIface = ChatInterface()
        self.chatProcessor = ChatProcessor(game, self.chatIface)

    def init(self) -> Result:
        ret: Result = self.chatIface.init()
        if ret.result:
            self.chatProcessor.init()
        return ret

    def destroy(self) -> Result:
        # TODO SCH teardown the yt session in chatIface?
        return Result(True)

    def start(self) -> Result:
        GameInterfaceYoutube.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Sending start message to yt livestream.")
        message = Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_STARTED)
        self.chatIface.sendMessage(message)
        self.chatIface.sendMessage(f"{GLOBALVARS.GAME_MSG_JOIN}")

        return Result(True)

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
        GameInterfaceYoutube.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Queuing add player message to yt livestream.")
        self.chatProcessor.addNewPlayerJoined(data.get("displayName"))
        return Result(True)

    def kickPlayer(self, data: ActionData) -> Result:
        GameInterfaceYoutube.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Sending kick player message to yt livestream.")
        _fData = {"player": data.get("displayName")}
        ret = self.chatIface.sendMessage(GLOBALVARS.GAME_MSG_KICKED.format(**_fData))
        return Result(ret)

    def banPlayer(self, data: ActionData) -> Result:
        GameInterfaceYoutube.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Sending kick player message to yt livestream.")
        _fData = {"player": data.get("displayName")}
        ret = self.chatIface.sendMessage(GLOBALVARS.GAME_MSG_BANNED.format(**_fData))
        return Result(ret)

    def makeCall(self, data: ActionData) -> Result:
        GameInterfaceYoutube.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Sending make call message to yt livestream.")
        ret = Result(False)
        index: int = data.get("index")
        newPlayerCalls: str = data.get("newPlayerCalls")
        newPlayerBingos: str = data.get("newPlayerBingos")
        bing: Bing = Binglets(self.game.gameType).getBingFromIndex(index)

        # Make sure the index is associated with a valid bing
        if not bing:
            ret.responseMsg = f"Could not locate bing for index {index}"
            return ret

        # Update the chat processor of the newly called bing slot
        self.chatProcessor.addCalledSlot(index)

        # Print message to stream chat
        ret.result = self.chatIface.sendMessage(f"Slot called: {bing.bingStr}")
        # TODO Not doing this quite yet
        #if newPlayerCalls:
        #    ret.result = ret.result and self.chatIface.sendMessage(newPlayerCalls)
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

