__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from config.ClassLogger import ClassLogger, LogLevel
from typing import Any

# TODO Ideally, I wouldn't have such a "weakly typed" data structure that is fed into the game callback methods,
#      as this could convolute future extendability. The correct approach is hierarchical inheritance, but I
#      can't be bothered to write that at the moment.
class ActionData:
    """
    POD object for adding context data to game calls within IGameInterface objects
    """

    # Assigning a function to this attribute causes it to be called when the various
    # GameInterfaceDiscord action is complete.
    # The finalize function must accept no args (for now)
    FINALIZE_FUNCT = "finalize"

    def __init__(self, **kwargs):
        self.add(**kwargs)

    def add(self, **kwargs):
        for key, val in kwargs.items():
            self.__setattr__(key, val)

    def get(self, attr: str) -> Any:
        if not hasattr(self, attr):
            ClassLogger(__name__).log(LogLevel.LEVEL_CRIT, f"Attribute \"{attr}\" of ActionData does not exist. Exiting.")
            raise ValueError(f"Expection {attr}")

        return self.__getattribute__(attr)

    def has(self, attr: str) -> bool:
        return hasattr(self, attr)

