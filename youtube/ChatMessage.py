__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

class ChatMessage:
    def __init__(self, message: str, mod: bool, author: str):
        self.message = message
        self.mod = mod
        self.author = author
        self.command = self._getCommand(message)

    def getCommand(self) -> str:
        return self.command

    def getBody(self) -> str:
        idx = self.message.find(" ")
        return self.message[idx:]

    def isMod(self) -> bool:
        return self.mod

    def getAuthor(self) -> str:
        return self.author

    def _getCommand(self, message: str) -> str:
        idx = message.find(" ")
        return message[:idx] if idx != -1 else message
