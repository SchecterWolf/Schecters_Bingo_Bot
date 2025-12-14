__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import threading
import time

from .ChatInterface import ChatInterface
from .ChatMessage import ChatMessage

from config.ClassLogger import ClassLogger, LogLevel
from config.Globals import GLOBALVARS
from game.ActionData import ActionData
from game.Bing import Bing
from game.Binglets import Binglets
from game.CallRequest import CallRequest
from game.IGameInterface import IGameInterface
from game.NotificationMessageMaker import MakeCallRequestNotif

from typing import Dict, List, Set, Optional

TypeRequestEntry = Dict[int, CallRequest]

class ChatProcessor:
    __LOGGER = ClassLogger(__name__)

    __MAX_NAMED_PLAYERS = 2

    __POLLING_INTERVAL_SEC = 15
    __COMMAND_INTERVAL_SEC = 60
    __REQ_INTERVAL_SEC = 60
    __NEW_PLAYER_INTERVAL_SEC = 30

    __COMMAND_CMD = "cmd"
    __COMMAND_STAMP = "timestamp"
    __COMMAND_MOD = "mod"

    def __init__(self, gameIface: IGameInterface, streamIface: ChatInterface):
        self.gameIface = gameIface
        self.streamIface = streamIface
        self.processorThread = threading.Thread(target=self._threadEntry)
        self.condition = threading.Condition()
        self.lockRequest = threading.Lock()
        self.lockNewPlayerJoined = threading.Lock()
        self.running = False

        self.commands = {
            "/bingo": {
                ChatProcessor.__COMMAND_CMD: self._cmdMessageJoin,
                ChatProcessor.__COMMAND_STAMP: time.time(),
                ChatProcessor.__COMMAND_MOD: False
            },
            "/rank": {
                ChatProcessor.__COMMAND_CMD: self._cmdMessageRank,
                ChatProcessor.__COMMAND_STAMP: time.time(),
                ChatProcessor.__COMMAND_MOD: False
            },
            "/call": {
                ChatProcessor.__COMMAND_CMD: self._cmdMakeCall,
                ChatProcessor.__COMMAND_CMD: time.time(),
                ChatProcessor.__COMMAND_MOD: True
            },
            "/del": {
                ChatProcessor.__COMMAND_CMD: self._cmdDelRequest,
                ChatProcessor.__COMMAND_CMD: time.time(),
                ChatProcessor.__COMMAND_MOD: True
            }
        }

        self.callsMade: Set[int] = set()
        self.requestTimestamp: float = time.time()
        self.broadcastNewPlayersTimestamp: float = time.time()
        self.requestsActive: TypeRequestEntry = dict()
        self.requestsPendingPrint: TypeRequestEntry = dict()
        self.playersAdded: List[str] = []

    def __del__(self):
        self.stop()

    def init(self):
        if self.running:
            return

        self.running = True
        self.processorThread.start()
        ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, "The YT chat processor has been started.")

    def stop(self):
        if not self.running:
            return

        ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Attempting to shut down the YT chat processor...")
        self.running = False
        self.condition.notify()
        self.processorThread.join()
        ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, "The YT chat processor has been shut down.")

    def addCalledSlot(self, bingIdx: int):
        with self.lockRequest:
            self.callsMade.add(bingIdx)

    def addCallRequest(self, callRequest: CallRequest):
        with self.lockRequest:
            requestIdx = callRequest.requestBing.bingIdx

            # Make sure that the request hasn't already been a called slot in the game
            if requestIdx in self.callsMade:
                ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Skipping adding call request index \"{requestIdx}\" from the YT chat processor (It's already been called).")
            else:
                pendingRequest = self.requestsPendingPrint.get(requestIdx)

                # If the request type is still pending printing, combine the requests,
                # else inert the request into the pending queue
                if pendingRequest:
                    ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Adding request index \"{requestIdx}\", to an existing pending index.")
                    pendingRequest.mergeRequests(callRequest)
                else:
                    ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Adding new pending request index \"{requestIdx}\".")
                    self.requestsPendingPrint[requestIdx] = callRequest

    def addNewPlayerJoined(self, newPlayerName: str):
        with self.lockNewPlayerJoined:
            self.playersAdded.append(newPlayerName)

    def _threadEntry(self):
        # Don't have to worry about atomic locking since the GIL only execs one thread at a time
        while self.running:
            self._processCallRequests()
            self._processNewPlayers()
            for message in self.streamIface.getMessages():
                self._processMessage(message)
            with self.condition:
                self.condition.wait(timeout=ChatProcessor.__POLLING_INTERVAL_SEC)

    def _processCallRequests(self):
        # Only print a call request after a certain amount of time
        if time.time() - self.requestTimestamp < ChatProcessor.__REQ_INTERVAL_SEC:
            return

        val: Optional[CallRequest] = None
        with self.lockRequest:
            if self.requestsPendingPrint:
                val = next(iter(self.requestsPendingPrint.values()))
                del self.requestsPendingPrint[val.requestBing.bingIdx]

        if val:
            ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Broadcasting call request index \"{val.requestBing.bingIdx}\" to YT stream.")
            self.streamIface.sendMessage(MakeCallRequestNotif(val, True))
            self.requestTimestamp = time.time()

    def _processNewPlayers(self):
        if time.time() - self.broadcastNewPlayersTimestamp < ChatProcessor.__NEW_PLAYER_INTERVAL_SEC:
            return

        val: str = ""
        with self.lockNewPlayerJoined:
            if self.playersAdded and len(self.playersAdded) < ChatProcessor.__MAX_NAMED_PLAYERS:
                val = "Players " + ", ".join(self.playersAdded) + " has joined the livestream bingo!"
            elif self.playersAdded:
                val = "Players " + ", ".join(self.playersAdded[:ChatProcessor.__MAX_NAMED_PLAYERS]) + \
                        f" and {len(self.playersAdded) - ChatProcessor.__MAX_NAMED_PLAYERS} others " + \
                        "have joined the livestream bingo!"
            self.playersAdded.clear()

        if val:
            ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Broadcasting add player message to chat: {val}")
            self.streamIface.sendMessage(val)
            self.broadcastNewPlayersTimestamp = time.time()

    def _processMessage(self, message: ChatMessage):
        # TODO There seems to be a segfault here after running for awhile
        return
        command = self.commands.get(message.getCommand())
        if command and time.time() - command[ChatProcessor.__COMMAND_STAMP] >= ChatProcessor.__COMMAND_INTERVAL_SEC:
            if command[ChatProcessor.__COMMAND_MOD] and not message.isMod():
                ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Someone tried to use the mod-only command \"{message.getCommand()}\", ignoring.")
            else:
                command[ChatProcessor.__COMMAND_CMD](message)

            command[ChatProcessor.__COMMAND_STAMP] = time.time()

    def _cmdMessageJoin(self, _):
        ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Command \"join message\" received from user.")
        self.streamIface.sendMessage(GLOBALVARS.GAME_MSG_JOIN)
        self.streamIface.sendMessage(GLOBALVARS.GAME_NIGHTBOT_CMD_DISCORD)

    def _cmdMessageRank(self, _):
        ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Command \"rank\" received.")
        # TODO SCH print top 3 places to livestream
        pass

    def _cmdMakeCall(self, message: ChatMessage):
        ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Command \"call\" received from user {message.getAuthor()}.")
        callStr = message.getBody()
        bings: List[Bing] = Binglets(self.gameIface.game.gameType).findBings(callStr)

        if not bings:
            self.streamIface.sendMessage(f"Could not find a slot containing: \"{callStr}\" .")
        elif len(bings) > 1:
            self.streamIface.sendMessage(f"Could not make call, \"{callStr}\" is ambiguous.")
        else:
            self.streamIface.sendMessage(f"Calling slot \"{bings[0].bingStr}\"! Please wait.")
            _ = self.gameIface.makeCall(ActionData(index=bings[0].bingIdx))

    def _cmdDelRequest(self, message: ChatMessage):
        ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Command \"del\" received {message.getAuthor()}.")
        delStr = message.getBody()

        if not delStr.isdigit():
            ChatProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Ignoring invalid del command: {delStr}.")
        else:
            _ = self.gameIface.deleteRequest(ActionData(index=int(delStr)))

