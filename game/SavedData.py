__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import json

from config.ClassLogger import ClassLogger, LogLevel # TODO SCH Update all files to include LogLevel from the ClassLogger from
from config.Globals import GLOBALVARS
from pathlib import Path
from typing import Union

class SavedData:
    __instance = None
    __LOGGER = ClassLogger(__name__)

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        self.dataFile = Path(GLOBALVARS.FILE_GAME_DATA)
        self.data: dict[str, str] = {}

        self._loadData()

    def __del__(self):
        self.flush()

    def flush(self):
        with self.dataFile.open("w") as file:
            json.dump(self.data, file, indent=4)
            SavedData.__LOGGER.log(LogLevel.LEVEL_INFO, "Game data has been saved.")

    def getData(self, key: str) -> Union[str, None]:
        return self.data.get(key)

    def saveData(self, key: str, val: str):
        self.data[key] = val

    def _loadData(self):
        SavedData.__LOGGER.log(LogLevel.LEVEL_INFO, "Reading in saved game data.")
        if not self.dataFile.exists():
            return
        else:
            with self.dataFile.open("r") as file:
                self.data = json.load(file)

