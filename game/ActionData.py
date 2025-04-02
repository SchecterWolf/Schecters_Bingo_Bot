__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import sys

from config.ClassLogger import ClassLogger
from config.Log import LogLevel
from typing import Any

class ActionData:
    """
    POD object for adding context data to game calls within IGameInterface objects
    """
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            self.__setattr__(key, val)

    def get(self, attr: str) -> Any:
        if not hasattr(self, attr):
            ClassLogger(__name__).log(LogLevel.LEVEL_CRIT, f"Attribute \"{attr}\" of ActionData does not exist. Exiting.")
            sys.exit(1)

        return self.__getattribute__(attr)

    def has(self, attr: str) -> bool:
        return hasattr(self, attr)

