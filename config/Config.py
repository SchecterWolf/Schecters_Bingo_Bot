__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import json
import os

from .Globals import GLOBALVARS

from pathlib import Path
from typing import Any

class Config:
    __instance = None
    __config = {}
    __file = Path(GLOBALVARS.FILE_CONFIG_GENERAL)

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def resetConfig(self):
        self.__config = {}

    def getConfig(self, configStr: str, default: Any = "") -> Any:
        if not self.__config:
            self._loadConfig()
        return self.__config.get(configStr, default)

    def getFormatConfig(self, configStr: str, template: str) -> str:
        ret = ""
        val = self.getConfig(configStr)
        if val:
            data = {configStr: val}
            ret = template.format(**data)

        return ret

    def _loadConfig(self):
        if not Config.__file.exists() or not os.path.getsize(Config.__file):
            return

        with Config.__file.open("r") as file:
            try:
                self.__config = json.load(file)
            except Exception as e:
                print(f"Could not load config data: {e}")

