__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .TaskUserDMs import TaskUserDMs

from config.ClassLogger import ClassLogger, LogLevel
from game.Player import Player

class TaskStartUserDMs(TaskUserDMs):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, player: Player):
        super().__init__(player)

    def __str__(self) -> str:
        playerName = self.player.card.getCardOwner()
        return f"Setup start view for \"{playerName}\"'s DM"

    def getType(self) -> TaskUserDMs.TaskType:
        return TaskUserDMs.TaskType.CHANGE_STATE

    async def execTask(self):
        if not self.player.ctx or not self.player.valid:
            TaskStartUserDMs.__LOGGER.log(LogLevel.LEVEL_WARN, f"Skipping start task for invalid user {self.player.card.getCardOwner()}!")
        else:
            await self.player.ctx.setViewStarted()

