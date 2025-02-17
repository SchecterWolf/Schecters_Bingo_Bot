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

from config.Globals import GLOBALVARS
from game.CallRequest import CallRequest
from game.NotificationMessageMaker import MakeCallRequestNotif

from typing import Dict, Set

TypeRequestEntry = Dict[int, CallRequest]

class ChatProcessor:
    __POLLING_INTERVAL_SEC = 15
    __COMMAND_INTERVAL_SEC = 60
    __REQ_INTERVAL_SEC = 30

    __COMMAND_CMD = "cmd"
    __COMMAND_STAMP = "timestamp"

    def __init__(self, streamIface: ChatInterface):
        self.streamIface = streamIface
        self.processorThread = threading.Thread(target=self._threadEntry)
        self.condition = threading.Condition()
        self.lock = threading.Lock()
        self.running = False

        self.commands = {
            "/bingo": {
                ChatProcessor.__COMMAND_CMD: self._printMessageJoin,
                ChatProcessor.__COMMAND_STAMP: time.time()
            },
            "/rank": {
                ChatProcessor.__COMMAND_CMD: self._printMessageRank,
                ChatProcessor.__COMMAND_STAMP: time.time()
            }
        }

        self.requestTimestamp: float = time.time()
        self.requests: TypeRequestEntry = dict()
        self.broadcastedRequests: Set[int] = set()

    def __del__(self):
        self.stop()

    def init(self):
        if self.running:
            return

        self.running = True
        self.processorThread.start()

    def stop(self):
        if not self.running:
            return

        self.running = False
        self.condition.notify()
        self.processorThread.join()

    def addCallRequest(self, callRequest: CallRequest):
        with self.lock:
            if callRequest.requestBing.bingIdx in self.broadcastedRequests:
                return
            self.requests[callRequest.requestBing.bingIdx] = callRequest

    def _threadEntry(self):
        # Don't have to worry about atomic locking since the GIL only execs one thread at a time
        while self.running:
            self._processCallRequests()
            for message in self.streamIface.getMessages():
                self._processMessage(message)
            with self.condition:
                self.condition.wait(timeout=ChatProcessor.__POLLING_INTERVAL_SEC)

    def _processCallRequests(self):
        with self.lock:
            if not self.requests and time.time() - self.requestTimestamp >= ChatProcessor.__REQ_INTERVAL_SEC:
                return
            val = next(iter(self.requests.values()))
            self.broadcastedRequests.add(val.requestBing.bingIdx)
            del self.requests[val.requestBing.bingIdx]

        self.streamIface.sendMessage(MakeCallRequestNotif(val))
        self.requestTimestamp = time.time()

    def _processMessage(self, message: str):
        if not message:
            return

        tokens = message.split()
        command = self.commands.get(tokens[0].lower())
        if command and time.time() - command[ChatProcessor.__COMMAND_STAMP] >= ChatProcessor.__COMMAND_INTERVAL_SEC:
            command[ChatProcessor.__COMMAND_CMD]()
            command[ChatProcessor.__COMMAND_STAMP] = time.time()

    def _printMessageJoin(self):
        self.streamIface.sendMessage(GLOBALVARS.GAME_MSG_JOIN)
        self.streamIface.sendMessage(GLOBALVARS.GAME_NIGHTBOT_CMD_DISCORD)

    def _printMessageRank(self):
        # TODO SCH
        pass

