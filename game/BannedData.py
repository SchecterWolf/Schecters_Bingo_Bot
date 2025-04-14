__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import json
import os
import time

from config.ClassLogger import ClassLogger, LogLevel
from config.Globals import GLOBALVARS
from pathlib import Path
from typing import Dict, List

TypeBannedData = Dict[str, str]
TypeBannedPlayer = Dict[str, TypeBannedData]

class BannedData:
    __instance = None
    __LOGGER = ClassLogger(__name__)
    __FIELD_BANNED_DATA_NAME = "name"
    __FIELD_BANNED_DATA_TIMESTAMP = "timestamp"

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        # Init guard
        if hasattr(self, "initialized"):
            return

        self.bannedFile = Path(GLOBALVARS.FILE_BANNED_DATA)
        self.data: TypeBannedPlayer = {}

        self._loadData()
        self.initialized = True

    def __del__(self):
        self.flush()

    def flush(self):
        if not self.data:
            return

        with self.bannedFile.open("w") as file:
            json.dump(self.data, file, indent=4)
            BannedData.__LOGGER.log(LogLevel.LEVEL_INFO, "Banned data has been saved.")

    def isBanned(self, playerID: int) -> bool:
        return str(playerID) in self.data

    def addBanned(self, playerID: int, playerName: str):
        BannedData.__LOGGER.log(LogLevel.LEVEL_INFO, f"Player ID {playerID} has been added to the banned list.")
        self.data[str(playerID)] = {
            BannedData.__FIELD_BANNED_DATA_NAME: playerName,
            BannedData.__FIELD_BANNED_DATA_TIMESTAMP: str(time.time())
        }
        self.flush()

    def removeBanned(self, playerID: int):
        if str(playerID) in self.data:
            BannedData.__LOGGER.log(LogLevel.LEVEL_INFO, f"Player ID {playerID} has been removed from the banned list.")
            del self.data[str(playerID)]
            self.flush()

    def getAllBanned(self) -> List[int]:
        return [int(playerID) for playerID in self.data.keys()]

    def _loadData(self):
        if not self.bannedFile.exists() or not os.path.getsize(self.bannedFile):
            BannedData.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Banned file is empty or non existent, skipping load.")
            return

        BannedData.__LOGGER.log(LogLevel.LEVEL_INFO, "Reading in banned player data.")
        with self.bannedFile.open("r") as file:
            try:
                self.data = json.load(file)
            except Exception as e:
                BannedData.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Could not load banned player data file: {e}")

