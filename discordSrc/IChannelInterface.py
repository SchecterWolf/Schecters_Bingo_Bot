__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from abc import ABC, abstractmethod
from discord.channel import DMChannel, TextChannel
from enum import Enum
from functools import wraps
from typing import Union

# TODO SCH rm
from config.ClassLogger import ClassLogger
from config.Log import LogLevel
import sys

class ChannelView(Enum):
    INIT = 0
    NEW = 1
    STARTED = 2
    PAUSED = 3
    STOPPED = 4

# Duplicate guard decorator
def verifyView(view: ChannelView):
    def decorator(fn):
        @wraps(fn)
        def wrapper(self: IChannelInterface, *args, **kwargs):
            if not self._currentView == view:
                self._currentView = view
                return fn(self, *args, **kwargs)
        return wrapper
    return decorator

class IChannelInterface(ABC):
    __INVALID_ID = -1
    __MSG_NOTICE = "noticeid"

    def __init__(self, channel: Union[DMChannel, TextChannel]):
        super().__init__()

        self._channel = channel
        self._messageIDs: dict[str, int] = {}
        self._currentView: ChannelView = ChannelView.INIT

    async def sendNotice(self, notice: str):
        await self._deleteChannelItem(IChannelInterface.__MSG_NOTICE)
        await self._updateChannelItem(IChannelInterface.__MSG_NOTICE, content=f"NOTICE: {notice}")

    async def sendNoticeItem(self, **kwargs):
        await self._deleteChannelItem(IChannelInterface.__MSG_NOTICE)
        await self._updateChannelItem(IChannelInterface.__MSG_NOTICE, **kwargs)

    async def removeNotice(self):
        await self._deleteChannelItem(IChannelInterface.__MSG_NOTICE)

    def _hasChannelItem(self, idString: str) -> bool:
        return self._messageIDs.get(idString, IChannelInterface.__INVALID_ID) != IChannelInterface.__INVALID_ID

    async def _purgeChannel(self):
        if isinstance(self._channel, TextChannel):
            await self._channel.purge()
        else:
            async for message in self._channel.history(limit=None):
                await message.delete()

        self._messageIDs.clear()

    async def _updateChannelItem(self, idString: str, **kwargs):
        ClassLogger(__name__).log(LogLevel.LEVEL_DEBUG, f"_updateChannelItem called: {kwargs}") # TODO SCH rm
        messageID = self._messageIDs.get(idString, IChannelInterface.__INVALID_ID)
        if messageID == IChannelInterface.__INVALID_ID:
            message = await self._channel.send(**kwargs)
            self._messageIDs[idString] = message.id
        else:
            try:
                message = await self._channel.fetch_message(messageID)
            except Exception as e:
                print(f">>>>>>> caught exception: {e}")
                sys.exit(1)
            ClassLogger(__name__).log(LogLevel.LEVEL_DEBUG, f"editing channel message: {message.id}") # TODO SCH rm
            await message.edit(**kwargs)

    async def _deleteChannelItem(self, idString: str):
        messageID = self._messageIDs.get(idString, IChannelInterface.__INVALID_ID)
        if messageID != IChannelInterface.__INVALID_ID:
            del self._messageIDs[idString]
            message = await self._channel.fetch_message(messageID)
            await message.delete()

    @abstractmethod
    async def setViewNew(self):
        pass

    @abstractmethod
    async def setViewStarted(self):
        pass

    @abstractmethod
    async def setViewPaused(self):
        pass

    @abstractmethod
    async def setViewStopped(self):
        pass

