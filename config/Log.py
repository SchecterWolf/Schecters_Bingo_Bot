__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import logging
import threading

from .Config import Config
from .Globals import GLOBALVARS
from enum import Enum

class LogLevel(Enum):
    LEVEL_CRIT = 0
    LEVEL_ERROR = 1
    LEVEL_WARN = 2
    LEVEL_INFO = 3
    LEVEL_DEBUG = 4
    LEVEL_NONE = 5

class Logger:
    _instance = None
    _levelStrings = {
        LogLevel.LEVEL_CRIT: "CRITICAL",
        LogLevel.LEVEL_ERROR: "ERROR",
        LogLevel.LEVEL_WARN: "WARN",
        LogLevel.LEVEL_INFO: "INFO",
        LogLevel.LEVEL_DEBUG: "DEBUG",
        LogLevel.LEVEL_NONE: "NONE"
    }
    _levelAssociate = {
        LogLevel.LEVEL_CRIT: logging.CRITICAL,
        LogLevel.LEVEL_ERROR: logging.ERROR,
        LogLevel.LEVEL_WARN: logging.WARNING,
        LogLevel.LEVEL_INFO: logging.INFO,
        LogLevel.LEVEL_DEBUG: logging.DEBUG,
        LogLevel.LEVEL_NONE: logging.NOTSET
    }

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'init'):
            self.log_level: LogLevel = self._getLoglevelFromStr(Config().getConfig('LogLevel', "NONE"))
            self.log_file = None
            self.lock = threading.Lock()
            self.init = True

    def __del__(self):
        if self.log_file:
            self.log_file.close()
        self.init = False

    def log(self, level: LogLevel, msg: str):
        if int(level.value) <= int(self.log_level.value):
            if not self.log_file:
                self.log_file = open(f"{GLOBALVARS.PROJ_ROOT}/log.txt", 'w')
                print(f"New logfile created {GLOBALVARS.PROJ_ROOT}/log.txt")

            try:
                with self.lock:
                    self.log_file.write(f"=={Logger._levelStrings[level]}== {msg}\n")
                self.log_file.flush()
            except Exception as e:
                print(f"Failed to log to logfile: {e}")

    def getCononicalLevel(self) -> int:
        return self._levelAssociate.get(self.log_level, logging.NOTSET)

    def _getLoglevelFromStr(self, levelstr) -> LogLevel:
        level = LogLevel.LEVEL_NONE
        for key, value in self._levelStrings.items():
            if value == levelstr.upper():
                level = key
                break
        return level

