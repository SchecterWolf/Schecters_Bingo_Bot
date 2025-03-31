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
        TaskUpdateUserDMs.__LOGGER.log(LogLevel.LEVEL_DEBUG, "execTask called----") # TODO SCH rm
        if not self.player:
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

    def addTask(self, task: TaskUpdateUserDMs):
        if self.running:
            TaskProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Adding new task to processor queue: {task}")
            # TODO SCH Check if the player already has a task in queue. If they do, skip adding
            #           A new task, since the update will handle any new changes after the initial
            #           task was added
            self.taskQueue.put(task)

    def _threadEntry(self):
        TaskProcessor.__LOGGER.log(LogLevel.LEVEL_INFO, "Task processor thread running.")

        # TODO SCH even though the eventual async calls into the discord bot SDK from the task
        #           will reconverge with the other thread (because the bot can use one and only one
        #           async event loop), lets still utilize this threads task queue to "process" one bot
        #           task at a time, in sequence. This will allow other bot async tasks to be "injected"
        #           into the event queue as interactions happen. This will allow the bot to still be
        #           responsive to the UI
        asyncio.set_event_loop(self.loop)
        while self.running:
            task  = self.taskQueue.get() # Wait for a task to become available
            if self.running:
                TaskProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Executing task: {task}")
                future = asyncio.run_coroutine_threadsafe(task.execTask(), self.loop)
                future.result(timeout=5.0)

        TaskProcessor.__LOGGER.log(LogLevel.LEVEL_INFO, "Task processor thread ended.")

