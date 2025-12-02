__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from game.Player import Player

from abc import ABC, abstractmethod
from enum import Enum

class TaskUserDMs(ABC):
    class TaskType(Enum):
        CHANGE_STATE = 1
        UPDATE = 2

    def __init__(self, player: Player):
        self.player = player
        self.noOp = False

    def setNoOp(self):
        self.noOp = True

    def getNoOp(self):
        return self.noOp

    def getPlayer(self):
        return self.player

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def getType(self) -> TaskType:
        pass

    @abstractmethod
    async def execTask(self):
        pass

