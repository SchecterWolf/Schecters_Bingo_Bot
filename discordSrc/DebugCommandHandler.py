__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "__"

import aiohttp
import discord

from .IAsyncDiscordGame import IAsyncDiscordGame

from config.ClassLogger import ClassLogger, LogLevel
from config.Globals import GLOBALVARS

from discord.app_commands import AppCommandContext, CommandTree
from discord.app_commands.commands import Command

from game.ActionData import ActionData
from game.GameStore import GameStore

from PIL import Image
from io import BytesIO
from typing import cast
from unittest.mock import AsyncMock, MagicMock

class DebugCommandHandler:
    __LOGGER = ClassLogger(__name__)
    __DEBUG_ID_COUNTER = -1

    def __init__(self):
        appContext = AppCommandContext(guild=True, dm_channel=False, private_channel=False)
        self.listCommands: list[Command] = [
            Command(
                name="add_player",
                description="Add an ephemeral user",
                callback=self.addPlayer,
                allowed_contexts=appContext,
            ),
            Command(
                name="bulk_add_players",
                description="Adds many ephemeral users (30)",
                callback=self.bulkAddPlayers,
                allowed_contexts=appContext
            ),
            Command(
                name="save_avatar",
                description="Saves the users avatar internally",
                callback=self.saveAvatar,
                allowed_contexts=appContext
            )
        ]

    def setupCommands(self, tree: CommandTree):
        for cmd in self.listCommands:
            tree.add_command(cmd)

    async def saveAvatar(self, interaction: discord.Interaction):
        DebugCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Saving avatar for user \"{interaction.user.display_name}\"({interaction.user.id})")

        # Make sure user is included
        if not interaction.user:
            await interaction.response.send_message("Command didn't include user", ephemeral=True)
            return
        await interaction.response.send_message("Request processing", ephemeral=True)

        # Save the user's avatar
        user = interaction.user
        async with aiohttp.ClientSession() as session:
            async with session.get(user.display_avatar.url) as response:
                imageData = await response.read()
                image = Image.open(BytesIO(imageData))
                image.save(f"{GLOBALVARS.PROJ_ROOT}/SavedUserAvatar.png")

    async def bulkAddPlayers(self, interaction: discord.Interaction):
        DebugCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Slash command bulkAddPlayers called")
        mockPlayers = ["Elephant", "Tiger", "Whale", "Eagle", "Panda", "Shark", "Leopard", "Kangaroo", "Anaconda", "Penguin",
                       "Giraffe", "Frog", "Fox", "Dragon", "Cobra", "Bison", "Kingfisher", "Squid", "Mandrill", "Okapi", "Axolotl",
                       "Tasmanian Devil", "Badger", "Dart Frog", "Crab", "Narwal", "Aye-Aye", "Quokka"]

        # Make sure game instance exists
        game = GameStore().getGame(interaction.guild_id or -1)
        if not game:
            guildName = interaction.guild.name if interaction.guild else "the guild"
            await interaction.response.send_message(f"There is no active game for {guildName}, cannot add player!")
            return
        await interaction.response.send_message("Added bulk players to the game!")

        # Add mock players to game
        game = cast(IAsyncDiscordGame, game)
        for player in mockPlayers:
            mockInter = self._makeMockInteraction(interaction)
            self._addPlayerIntrnl(game, mockInter, player, False)
        self._addPlayerIntrnl(game, self._makeMockInteraction(interaction), "Pikachu", True)

    async def addPlayer(self, interaction: discord.Interaction, message: str):
        DebugCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Slash command addPlayer called with guild id: {interaction.guild_id}.")

        # Make sure the game instance exists
        game = GameStore().getGame(interaction.guild_id or -1)
        if not game:
            guildName = interaction.guild.name if interaction.guild else "the guild"
            await interaction.response.send_message(f"There is no active game for {guildName}, cannot add player!")
            return

        # Add mock player to the game
        await interaction.response.send_message(f"Mock user \"{message}\" as been added to the game.")
        self._addPlayerIntrnl(cast(IAsyncDiscordGame, game), interaction, message, True)

    def _makeMockInteraction(self, interaction: discord.Interaction):
        mockInter = AsyncMock(spec=discord.Interaction)

        mockUser = MagicMock()
        mockUser.id = interaction.user.id
        mockUser.mention = f"<@{interaction.user.id}>"
        mockUser.name = "MockUser"

        mockChannel = MagicMock()
        mockChannel.id = interaction.channel_id
        mockChannel.name = "MockChannel"

        mockGuild = MagicMock()
        mockGuild.id = interaction.guild_id
        mockGuild.name = "MockGuild"

        mockInter.user = mockUser
        mockInter.channel = mockChannel
        mockInter.guild = mockGuild
        mockInter.channel_id = interaction.channel_id
        mockInter.guild_id = interaction.guild_id

        mockInter.response = AsyncMock()

        return mockInter

    def _addPlayerIntrnl(self, game: IAsyncDiscordGame, interaction: discord.Interaction, player: str, refresh: bool):
        # Create the mock user
        mockUser = MagicMock(spec=discord.User)
        mockUser.id = DebugCommandHandler.__DEBUG_ID_COUNTER
        mockUser.name = player
        mockUser.bot = False
        mockUser.mention = f"<@{mockUser.id}>"
        mockUser.display_name = player
        mockUser.dm_channel = None

        # Create a mock DM channel
        mockChannel = AsyncMock(spec=discord.DMChannel)
        mockChannel.id = -1
        mockChannel.recipient = mockUser
        mockChannel.type = discord.ChannelType.private

        # Add mock player to the running game
        interaction.user = mockUser
        _ = game.addPlayer(ActionData(interaction=interaction, mockDMChannel=mockChannel, refresh=refresh))
        DebugCommandHandler.__DEBUG_ID_COUNTER -= 1

