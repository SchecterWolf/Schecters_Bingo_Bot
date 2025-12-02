__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import copy
import json
import os

from .Bing import Bing
from config.ClassLogger import ClassLogger, LogLevel
from config.Globals import GLOBALVARS
from pathlib import Path
from typing import Dict, List

class Binglets:
    __instances: Dict[str, "Binglets"] = {}
    __LOGGER = ClassLogger(__name__)

    def __new__(cls, *args, **kwargs):
        bType = kwargs['type'] if 'type' in kwargs else GLOBALVARS.GAME_TYPE_DEFAULT
        _inst = None

        if bType in cls.__instances:
            _inst = cls.__instances[bType]
        else:
            _inst = super().__new__(cls)
            cls.__instances[bType] = _inst

        return _inst

    def __init__(self, bType: str = GLOBALVARS.GAME_TYPE_DEFAULT):
        # Init guard
        if bType in Binglets.__instances:
            return

        self._binglets: Dict[str, List[Bing]] = {}
        self._bings_ary: List[Bing] = []

        if bType == GLOBALVARS.GAME_TYPE_DEFAULT:
            self.bingletsFile = Path(GLOBALVARS.FILE_CONFIG_BINGLETS)
        else:
            self.bingletsFile = Path(f"{GLOBALVARS.DIR_CONFIG}/{bType}.json")

    def getBingletsCopy(self) -> List[Bing]:
        if not self._bings_ary:
            for key, array in self.getBingDict().items():
                for bng in array:
                    self._bings_ary.append(bng)

        return copy.deepcopy(self._bings_ary)

    def getBingDict(self) -> Dict[str, List[Bing]]:
        # Get the configured binglets, if we haven't already
        if not self._binglets:
            self._loadBings()

        return self._binglets

    def getNumBings(self) -> int:
        if not self._binglets:
            self._loadBings()
        return len(self._binglets)

    def getBingFromIndex(self, index: int) -> Bing:
        ret = Bing("", -1)
        for bing in self.getBingletsCopy():
            if index == bing.bingIdx:
                ret = copy.copy(bing)
                break
        return ret

    def findBings(self, substr: str) -> List[Bing]:
        substrLower = substr.lower()
        ret = []
        for key, array in self.getBingDict().items():
            for bing in array:
                if substrLower in bing.bingStr.lower():
                    ret.append(bing)
        return ret

    def _loadBings(self):
        Binglets.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Reading in binglets config.")
        if not self.bingletsFile.exists() or not os.path.getsize(self.bingletsFile):
            Binglets.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Binglets data file is empty or non existent, skipping load.")
            return

        with self.bingletsFile.open("r") as file:
            try:
                config = json.load(file)
            except Exception as e:
                Binglets.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Could not load binglets data file: {e}")
                return

        i = 1 # Note: 0 is reserved for FREE SPACE
        for key, array in config['bings'].items():
            _bings: List[Bing] = []
            for bstr in array:
                _bings.append(Bing(bstr, i))
                i+=1
            self._binglets[key] = _bings
        Binglets.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Binglets successfully parsed.")

