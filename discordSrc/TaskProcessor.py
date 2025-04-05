__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import asyncio
import threading

from .UserDMChannel import UserDMChannel

from config.ClassLogger import ClassLogger
from config.Log import LogLevel

from game.Player import Player
from queue import Queue
from typing import Union

# For now we just have one task that this processor can handle,
# But is we end up with more, break this out into their own classes
class TaskUpdateUserDMs:
    __LOGGER = ClassLogger(__name__)

    def __init__(self, notifStr: str, player: Union[Player, None]):
        self.notifStr = notifStr
        self.player = player

    def __str__(self) -> str:
        playerName = self.player.card.getCardOwner() if self.player else ""
        return f" Update \"{playerName}\" DM"

    async def execTask(self):
        if not self.player or not self.player.valid:
            name = self.player.card.getCardOwner() if self.player else ""
            TaskUpdateUserDMs.__LOGGER.log(LogLevel.LEVEL_WARN, f"Skipping task for invalid user {name}")
            return

        ctx = self.player.ctx
        if isinstance(ctx, UserDMChannel):
            TaskUpdateUserDMs.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Updating user DM channel for: {self}")
            await ctx.setBoardView()
            await ctx.refreshRequestView()
            await ctx.sendNotice(self.notifStr)

class TaskProcessor:
    """
    Processor that runs tasks on a separate thread. Mainly used when needing to break off large
    workloads from the main game flow of control. i.e To increase the responsiveness of game
    discord ui controls
    """
    __LOGGER = ClassLogger(__name__)

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.processorThread = threading.Thread(target=self._threadEntry)
        self.running = False
        self.taskQueue: Queue[TaskUpdateUserDMs] = Queue()
        self.taskIDs: set[str] = set()

    def init(self):
        if self.running:
            return

        self.running = True
        self.processorThread.start()

    def stop(self):
        TaskProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Task processor signaled to shut down.")
        if not self.running:
            return

        self.running = False
        self.taskQueue.put(TaskUpdateUserDMs("", None)) # Unblock the processor thread
        self.processorThread.join()
        TaskProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Task processor signaled to shut down.") # TODO SCH rm

    # Adds a task to the process queue only if a task of the same type isnt already queued
    def addTask(self, task: TaskUpdateUserDMs):
        taskID = self._getTaskID(task)
        if self.running and taskID not in self.taskIDs:
            TaskProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Adding new task to processor queue: {task}")
            self.taskIDs.add(taskID)
            self.taskQueue.put(task)

    def _threadEntry(self):
        TaskProcessor.__LOGGER.log(LogLevel.LEVEL_INFO, "Task processor thread running.")

        # Note: Since there is only one async event loop handler (that is owned by the discord bot),
        #       this flow of control will reconverge onto the bot thread. However, this thread allows
        #       us to control when tasks get added to the loop so the discord bot can still be reactive
        #       to other tasks during this class's processing
        asyncio.set_event_loop(self.loop)
        while self.running:
            task  = self.taskQueue.get() # Wait for a task to become available
            self.taskIDs.discard(self._getTaskID(task))
            if self.running:
                TaskProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Executing task: {task}")
                future = asyncio.run_coroutine_threadsafe(task.execTask(), self.loop)
                future.result(timeout=5.0)
                self.taskQueue.task_done()

        TaskProcessor.__LOGGER.log(LogLevel.LEVEL_INFO, "Task processor thread ended.")

    def _getTaskID(self, task: TaskUpdateUserDMs) -> str:
        pID = str(task.player.userID) if task.player else ""
        return task.__class__.__name__ + pID

