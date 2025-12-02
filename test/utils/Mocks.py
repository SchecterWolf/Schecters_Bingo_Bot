__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = ""

import asyncio
import discord

from . import Const as Const
from discordSrc.GameGuild import GameGuild

from unittest.mock import AsyncMock, MagicMock

def makeMockBot():
    mockBot = MagicMock()

    def ignoreExceptions(loop, context):
        pass

    # Assign our own async loop to the mocked discord bot client
    try:
        loop = asyncio.get_running_loop()
    except:
        loop = asyncio.new_event_loop()

    loop.set_exception_handler(ignoreExceptions)
    mockBot.loop = loop

    return mockBot

def makeMockGuild():
    mockGuildID = Const.TEST_GUILD_ID

    mockChannelBingo = MagicMock()
    mockChannelBingo.send = AsyncMock()
    mockChannelBingo.fetch_message = AsyncMock()

    mockChannelAdmin = MagicMock()
    mockChannelAdmin.send = AsyncMock()
    mockChannelAdmin.fetch_message = AsyncMock()

    return GameGuild(mockGuildID, MagicMock(), mockChannelBingo, mockChannelAdmin)

def makeMockInteraction():
    mockInteraction = MagicMock(spec=discord.Interaction)
    mockInteraction.followup = MagicMock()
    mockInteraction.followup.send = AsyncMock()
    mockInteraction.guild = MagicMock()
    mockInteraction.guild.id = Const.TEST_GUILD_ID
    mockInteraction.guild_id = Const.TEST_GUILD_ID
    mockInteraction.response.send_message = AsyncMock()
    mockInteraction.response.defer = AsyncMock()
    mockInteraction.message.edit = AsyncMock()

    return mockInteraction

def makeMockUserWNOChannel(name: str, userID: int = -1):
    mockUser = MagicMock(spec=discord.User)
    mockUser.id = userID
    mockUser.name = name
    mockUser.bot = False
    mockUser.mention = f"<@{mockUser.id}>"
    mockUser.display_name = name
    mockUser.dm_channel = None

    return mockUser

def makeMockUser(name: str, userID: int = -1):
    mockUser = makeMockUserWNOChannel(name, userID)
    mockUser.dm_channel = makeMockDMChannel(mockUser)

    return mockUser

def makeMockDMChannel(mockUser):
    mockUserChannel = AsyncMock(spec=discord.DMChannel)
    mockUserChannel.id = -1
    mockUserChannel.recipient = mockUser
    mockUserChannel.type = discord.ChannelType.private
    mockUserChannel.send = AsyncMock()
    mockUserChannel.fetch_message = AsyncMock()

    return mockUserChannel

