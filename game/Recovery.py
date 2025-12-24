__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import sqlite3

from .Game import Game

from config.ClassLogger import ClassLogger, Logger

class Recovery:
    __instance = None
    __LOGGER = ClassLogger(__name__)

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        if hasattr(self, "initialized"):
            return

        self.initialized = True

    def hasRecovery(self, gameID: int):
        return False;

    def removeRecovery(self, gameID: int):
        pass

    def updateRecovery(self, gameID: int, game: Game):
        pass

