__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

# Classes defined in this file are for functional tracking purposes for the unit tests.
# They SHALL inherit from the target class who ought to be tracked in some manner during
# the unit testing.

import asyncio
import discord
import time
import threading

from concurrent.futures import Future
from config.ClassLogger import ClassLogger, LogLevel
from discord.channel import DMChannel
from discordSrc.AdminChannel import AdminChannel
from discordSrc.BingoChannel import BingoChannel
from discordSrc.GameGuild import GameGuild
from discordSrc.TaskProcessor import TaskProcessor
from discordSrc.TaskUserDMs import TaskUserDMs
from discordSrc.UserDMChannel import UserDMChannel
from game.CallRequest import CallRequest
from game.Player import Player

from typing import List, Optional

class TestingAdminChannel(AdminChannel):
    def __init__(self, gameGuild: GameGuild, gameType: str):
        super().__init__(gameGuild, gameType)
        self.resetTracking()

    def resetTracking(self):
        self.setViewNewCalled = False
        self.setViewStartedCalled = False
        self.setViewPausedCalled = False
        self.setViewStoppedCalled = False
        self.addCallRequestCalled = False
        self.delCallRequestCalled = False
        self.sendNoticeCalled = False
        self.noticeItems: List[str] = []
        self.deletedRequestIdx = -1

    async def setViewNew(self):
        self.setViewNewCalled = True
        await super().setViewNew()

    async def setViewStarted(self):
        self.setViewStartedCalled = True
        await super().setViewStarted()

    async def setViewPaused(self):
        self.setViewPausedCalled = True
        await super().setViewPaused()

    async def setViewStopped(self):
        self.setViewStoppedCalled = True
        await super().setViewStopped()

    async def addCallRequest(self, request: CallRequest):
        self.addCallRequestCalled = True
        await super().addCallRequest(request)

    async def delCallRequest(self, index: int):
        self.deletedRequestIdx = index
        self.delCallRequestCalled = True
        await super().delCallRequest(index)

    async def sendNotice(self, notice: str):
        self.sendNoticeCalled = True
        self.noticeItems.append(notice)
        await super().sendNotice(notice)

class TestingBingoChannel(BingoChannel):
    def __init__(self, bot: discord.Client, guild: GameGuild):
        super().__init__(bot, guild)
        self.resetTracking()

    def resetTracking(self):
        self.setViewNewCalled = False
        self.setViewStartedCalled = False
        self.setViewPausedCalled = False
        self.setViewStoppedCalled = False
        self.refreshGameStatusCalled = False
        self.sendNoticeItemCalled = False
        self.noticeItem = dict()

    async def setViewNew(self):
        self.setViewNewCalled = True
        await super().setViewNew()

    async def setViewStarted(self):
        self.setViewStartedCalled = True
        await super().setViewStarted()

    async def setViewPaused(self):
        self.setViewPausedCalled = True
        await super().setViewPaused()

    async def setViewStopped(self):
        self.setViewStoppedCalled = True
        await super().setViewStopped()

    async def refreshGameStatus(self):
        self.refreshGameStatusCalled = True
        await super().refreshGameStatus()

    async def sendNoticeItem(self, **kwargs):
        self.sendNoticeItemCalled = True
        self.noticeItem = dict(kwargs)
        await super().sendNoticeItem(**kwargs)

class TestingUserDMChannel(UserDMChannel):
    def __init__(self, gameID: int, channel: DMChannel, player: Player):
        super().__init__(gameID, channel, player)
        self.resetTracking()

    def resetTracking(self):
        self.setViewNewCalled = False
        self.setViewStartedCalled = False
        self.setViewPausedCalled = False
        self.setViewStoppedCalled = False
        self.setViewKickedCalled = False
        self.refreshRequestViewCalled = False
        self.setBoardViewCalled = False
        self.sendNoticeCalled = False
        self.noticeItems: List[str] = []

    async def setViewNew(self):
        self.setViewNewCalled = True
        await super().setViewNew()

    async def setViewStarted(self):
        self.setViewStartedCalled = True
        await super().setViewStarted()

    async def setViewPaused(self):
        self.setViewPausedCalled = True
        await super().setViewPaused()

    async def setViewStopped(self):
        self.setViewStoppedCalled = True
        await super().setViewStopped()

    async def setViewKicked(self, action: str):
        self.setViewKickedCalled = True
        await super().setViewKicked(action)

    async def refreshRequestView(self):
        self.refreshRequestViewCalled = True
        await super().refreshRequestView()

    async def setBoardView(self):
        self.setBoardViewCalled = True
        await super().setBoardView()

    async def sendNotice(self, notice: str):
        self.sendNoticeCalled = True
        self.noticeItems.append(notice)
        await super().sendNotice(notice)

class TestingTaskProcessor(TaskProcessor):
    __LOGGER = ClassLogger(__name__)
    """
    This class intercepts typical TaskProcessor functions for test
    tracking purposes.
    """
    class AbstractTrackingTask(TaskUserDMs):
        def __init__(self, internalTask: TaskUserDMs):
            self.internalTask = internalTask
            self.taskExecuted = False

            # Hookup the internal tasks function calls
            self.setNoOp = self.internalTask.setNoOp
            self.getNoOp = self.internalTask.getNoOp
            self.getPlayer = self.internalTask.getPlayer

        def __str__(self) -> str:
            return self.internalTask.__str__()

        def getType(self) -> TaskUserDMs.TaskType:
            return self.internalTask.getType()

        async def execTask(self):
            """
            Captures the execTask function to track if the exec call
            has been performed on the task.
            """
            await self.internalTask.execTask()
            self.taskExecuted = True

    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__(loop)
        self.addedTasks: List[TestingTaskProcessor.AbstractTrackingTask] = []
        self.ephemeralBotThread: Optional[threading.Thread] = None
        self.futures: List[Future] = []

    def initThread(self):
        if not self.ephemeralBotThread:
            self.ephemeralBotThread = threading.Thread(target=self.loop.run_forever, daemon=True)

    def startProcessing(self):
        """
        Starts the task loop thread
        """
        self.initThread()
        if not self.ephemeralBotThread:
            return False

        if not self.ephemeralBotThread.is_alive():
            self.ephemeralBotThread.start()

    def stopProcessing(self):
        """
        Stops the task event loop by cancelling all remaining tasks and stoping
        the loop thread
        """
        if not self.ephemeralBotThread or not self.ephemeralBotThread.is_alive():
            return

        def cancelTaskLoop():
            for task in asyncio.all_tasks(self.loop):
                task.cancel()
            for future in self.futures:
                future.cancel()
            self.loop.stop()

        self.stop()
        self.loop.call_soon_threadsafe(cancelTaskLoop)

        # Stop the processing thread
        if self.ephemeralBotThread:
            self.ephemeralBotThread.join()
        self.ephemeralBotThread = None

    def processPendingTasks(self, timeoutSec = 2) -> bool:
        """
        Start a processing thread (If one hasn't been started already), and
        run until all tasks are processes or until the timeout has been reached.
        Then the processing thread is terminated.

        Note:
        For unit tests, we have to manually start the asyncio event loop.
        Normally, this is done by the discord py library when the bot is running regularly.
        """
        self.startProcessing()

        startTime = time.time()
        while self.futures and time.time() - startTime < timeoutSec:
            future = self.futures.pop()
            try:
                future.result()
            except Exception as e:
                TestingTaskProcessor.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Task '{future}'' failed to execute in an acceptable amount of time.")

        if not self.hasNoPendingTasks():
            print("Task processor timed out after {timeoutSec} seconds while processing tasks...")

        self.loop.call_soon_threadsafe(self.loop.stop)

        # Stop the processing thread
        if self.ephemeralBotThread:
            self.ephemeralBotThread.join()
        self.ephemeralBotThread = None

        return self.hasNoPendingTasks()

    def addTask(self, task: TaskUserDMs):
        """
        Captures the tasks that are added to the TaskProcessor so that the unit test
        can have access to them during the assertion phase.
        """
        mockTask = TestingTaskProcessor.AbstractTrackingTask(task)
        self.addedTasks.append(mockTask)
        super().addTask(mockTask)

    def hasNoPendingTasks(self) -> bool:
        return len(self.futures) == 0

    def _runTask(self, task: TaskUserDMs):
        self.futures.append(asyncio.run_coroutine_threadsafe(task.execTask(), self.loop))

