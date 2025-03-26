__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import copy
import json

from .Bing import Bing
from config.ClassLogger import ClassLogger, LogLevel
from config.Globals import GLOBALVARS
from pathlib import Path
from typing import Dict, List

class Binglets:
    __instance = None
    __binglets: Dict[str, List[Bing]] = {}
    __bings_ary: List[Bing] = []
    __LOGGER = ClassLogger(__name__)

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        self.bingletsFile = Path(GLOBALVARS.FILE_CONFIG_BINGLETS)

    def getBingletsCopy(self) -> List[Bing]:
        if not Binglets.__bings_ary:
            for key, array in self.getBingDict().items():
                for bng in array:
                    Binglets.__bings_ary.append(bng)

        return copy.copy(Binglets.__bings_ary)

    def getBingDict(self) -> Dict[str, List[Bing]]:
        # Get the configured binglets, if we haven't already
        if not Binglets.__binglets:
            self._loadBings()

        return Binglets.__binglets

    def getNumBings(self) -> int:
        if not Binglets.__binglets:
            self._loadBings()
        return len(Binglets.__binglets)

    def getBingFromIndex(self, index: int) -> Bing:
        ret = Bing("", 0)
        for bing in self.getBingletsCopy():
            if index == bing.bingIdx:
                ret = copy.copy(bing)
                break
        return ret

    def _loadBings(self):
        Binglets.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Reading in binglets config.")
        if not self.bingletsFile.exists():
            return
        else:
            with self.bingletsFile.open("r") as file:
                config = json.load(file)

        i = 1 # Note: 0 is reserved for FREE SPACE
        for key, array in config['bings'].items():
            _bings: List[Bing] = []
            for bstr in array:
                _bings.append(Bing(bstr, i))
                i+=1
            Binglets.__binglets[key] = _bings
        Binglets.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Binglets successfully parsed.")

