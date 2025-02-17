__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import json

from .Globals import GLOBALVARS

from typing import Any

class Config:
    __instance = None
    __config = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def getConfig(self, configStr: str, default: Any = ""):
        if not self.__config:
            with open(GLOBALVARS.FILE_CONFIG_GENERAL, 'r') as file:
                self.__config = json.load(file)
        return self.__config.get(configStr, default)

    def getFormatConfig(self, configStr: str, template: str) -> str:
        ret = ""
        val = self.getConfig(configStr)
        if val:
            data = {configStr: val}
            ret = template.format(**data)

        return ret

