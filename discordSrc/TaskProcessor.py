__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import asyncio
import threading

from .TaskUpdateUserDMs import TaskUpdateUserDMs
from .TaskUserDMs import TaskUserDMs
from config.ClassLogger import ClassLogger, LogLevel
from game.Player import Player

from queue import Queue
from typing import Dict, List

class TaskProcessor:
    """
    Processor that runs tasks on a separate thread. Mainly used when needing to break off large
    workloads from the main game flow of control. i.e To increase the responsiveness of game
    discord ui controls
    """
    __LOGGER = ClassLogger(__name__)

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.event = threading.Event()
        self.loop = loop
        self.processorThread = threading.Thread(target=self._threadEntry)
        self.running = False
        self.taskIDs: Dict[str, List[TaskUserDMs]] = dict()
        self.taskQueue: Queue[TaskUserDMs] = Queue()

    def init(self):
        if self.running:
            return

        self.running = True
        self.resume()
        self.processorThread.start()

    def stop(self):
        TaskProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Task processor signaled to shut down.")
        if not self.running:
            return

        self.running = False
        self.resume()
        self.taskQueue.put(TaskUpdateUserDMs("", Player("", 0))) # Unblock the processor thread
        self.processorThread.join()

    # Adds a task to the process queue only if a task of the same type isn't already queued
    def addTask(self, task: TaskUserDMs):
        if not self.running:
            return

        # Note: These aren't technically needed because the python GIL will only execute one
        #       critical section at a time. But i'll still add these for best practice.
        self.pause()

        addTask = False
        taskID = self._getTaskID(task)
        # Always add the task if the taskID has not already been added
        if taskID not in self.taskIDs:
            addTask = True
            self.taskIDs[taskID] = [task]
        # If there is already CHANGE_STATE tasks associated with the user, invalidate all the
        # queued tasks, since the most recent STATE is what should be honored.
        elif task.getType() == TaskUserDMs.TaskType.CHANGE_STATE:
            addTask = True
            for subtask in self.taskIDs[taskID]:
                subtask.setNoOp()
            self.taskIDs[taskID].append(task)
        # There only needs to be one UPDATE task per user, so skip
        else:
            TaskProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Skipping redundant update task: {taskID}")

        if addTask:
            TaskProcessor.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Adding new task to processor queue: {task}")
            self.taskQueue.put(task)

        self.resume()

    def pause(self):
        if not self.running:
            return

        self.event.clear()

    def resume(self):
        if not self.running:
            return

        self.event.set()

    def _threadEntry(self):
        TaskProcessor.__LOGGER.log(LogLevel.LEVEL_INFO, "Task processor thread running.")

        # Note: Since there is only one async event loop handler (that is owned by the discord bot),
        #       this flow of control will reconverge onto the bot thread. However, this thread allows
        #       us to control when tasks get added to the loop so the discord bot can still be reactive
        #       to other tasks during this class's processing.
        #       We HAVE to use the same event loop, because calling into the discord api in a different
        #       loop will cause it to throw an error
        asyncio.set_event_loop(self.loop)

        while self.running:
            self.event.wait()

            task  = self.taskQueue.get() # Wait for a task to become available
            self.taskIDs.pop(self._getTaskID(task), None)

            # Run the task, unless it's marked as noOp
            if self.running and not task.getNoOp():
                self._runTask(task)

            self.taskQueue.task_done()

        TaskProcessor.__LOGGER.log(LogLevel.LEVEL_INFO, "Task processor thread ended.")

    def _runTask(self, task: TaskUserDMs):
        future = asyncio.run_coroutine_threadsafe(task.execTask(), self.loop)
        future.result(timeout=10)

    def _getTaskID(self, task: TaskUserDMs) -> str:
        pID = str(task.getPlayer().userID)
        return str(task.getType()) + pID

