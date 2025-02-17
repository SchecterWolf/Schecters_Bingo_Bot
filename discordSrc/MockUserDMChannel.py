__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import asyncio

from .UserDMChannel import UserDMChannel

from discord.channel import DMChannel
from game.Player import Player

class MockUserDMChannel(UserDMChannel):
    """
    Mock user DM channel for fake players within the bingo game.
    This class mimics overhead for regular players for the purposes of load testing.
    Note, the DMChannel should NOT be used, since it is a mock channel that could potentially
    throw an exception, since there is no backing for it.
    """
    def __init__(self, channel: DMChannel, player: Player):
        super().__init__(-1, channel, player)

    async def removeNotice(self):
        pass

    async def setViewNew(self):
        await asyncio.sleep(0.25)

    async def setViewStarted(self):
        await asyncio.sleep(0.25)

    async def setViewPaused(self):
        await asyncio.sleep(0.25)

    async def setViewStopped(self):
        await asyncio.sleep(0.30)

    async def refreshRequestView(self):
        pass

    async def setBoardView(self):
        # TODO SCH Might want to switch this to regular sleep to emulate async-blocking working
        await asyncio.sleep(1.9)

