__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

# cspell:ignore notifStr

from .TaskUserDMs import TaskUserDMs

from config.ClassLogger import ClassLogger, LogLevel
from game.Player import Player

class TaskUpdateUserDMs(TaskUserDMs):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, notifStr: str, player: Player):
        super().__init__(player)
        self.notifStr = notifStr

    def __str__(self) -> str:
        playerName = self.player.card.getCardOwner() if self.player else ""
        return f" Update \"{playerName}\" DM"

    def getType(self) -> TaskUserDMs.TaskType:
        return TaskUserDMs.TaskType.UPDATE

    async def execTask(self):
        if not self.player.ctx or not self.player.valid:
            name = self.player.card.getCardOwner() if self.player else ""
            TaskUpdateUserDMs.__LOGGER.log(LogLevel.LEVEL_WARN, f"Skipping task for invalid user {name}")
            return

        if self.player.ctx:
            await self.player.ctx.setBoardView()
            await self.player.ctx.refreshRequestView()
            await self.player.ctx.sendNotice(self.notifStr)

